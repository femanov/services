#!/usr/bin/env python3

import sys
from math import fabs
import numpy as np

from aux import str2u
from aux.service_daemon import CothreadQtService

import pycx4.qcda as cda

from acc_ctl.mode_ser import ModesServer
from acc_ctl.k500modes import remag_devs, remag_srv
from acc_ctl.magwalker import MagWalker

from acc_db.db import AccConfig, ModesDB
from acc_db.mode_cache import SysCache, ModeCache


class ModeDeamon:
    def __init__(self):
        self.db = ModesDB()

        ans = self.db.mode_chans()
        self.db_chans = [list(c) for c in ans]

        self.cind = {}
        self.avaliable_cind = {}

        # db cols: protocol, name, fullchan_id
        for x in self.db_chans:
            chan = None
            if x[0] == 'cx':
                chan = cda.DChan(str(x[1]))#, on_update=True)
                chan.valueMeasured.connect(self.cx_new_data)
                chan.resolve.connect(self.cx_resolve)
            if x[0] == 'EPICS':
                chan = catools.camonitor(str(x[1]), self.epicsNewData, format=catools.FORMAT_TIME)
            x += [0, 0.0, 0]  # cols: protocol, name, fullchan_id, utime, value, available
            if x[1] in self.cind:
                print("error: chan doubled %s" % x[1], x, self.cind[x[1]])
                sys.exit(-1)
            self.cind[x[1]] = [chan, x]  # copy link to hash-table for faster look-up

        self.mode_ser = ModesServer()  # message server for accelerator mode control
        self.mode_ser.load.connect(self.loadMode)
        self.mode_ser.save.connect(self.saveMode)
        self.mode_ser.loadMarked.connect(self.loadMarked)
        self.mode_ser.markMode.connect(self.markMode)
        self.mode_ser.walkerLoad.connect(self.walkerLoad)
        self.mode_ser.setZeros.connect(self.apply_zeros)

        # create cache for "logical system" to "chan_name"
        self.sys_cache = SysCache(db=self.db)
        # load all current marks
        self.db.execute("SELECT name from modemark")
        marks = self.db.cur.fetchall()
        self.marks = [x[0] for x in marks]
        self.mode_caches = {x: ModeCache(x, db=self.db, sys_cache=self.sys_cache) for x in self.marks}

        # walkers for chain-load infrastructure
        self.walkers = {name: MagWalker(remag_srv + '.' + name) for name in remag_devs}
        for k in self.walkers:
            self.walkers[k].done.connect(self.mode_ser.walkerDone)

        self.dump_count = 0

    def cx_resolve(self, chan):
        row = self.cind[chan.name][1]
        if chan.rslv_stat == cda.RSLVSTAT_NOTFOUND or chan.rslv_stat == cda.RSLVSTAT_SEARCHING:
            if chan.name in self.avaliable_cind:
                del self.avaliable_cind[chan.name]
                row[-1] = 0
        elif chan.rslv_stat == cda.RSLVSTAT_FOUND:
            self.avaliable_cind[chan.name] = self.cind[chan.name]
            row[-1] = 1

    def cx_new_data(self, chan):
        row = self.cind[chan.name][1]
        row[-3], row[-2] = chan.time, chan.val

    def epicsNewData(self, value):
        row = self.cind[value.name][1]
        time = int(value.raw_stamp[0] * 1000000 + value.raw_stamp[1] / 1000)
        row[-3], row[-2], row[-1] = time, float(value), 2

    def saveMode(self, author, comment):
        mode_id = self.db.save_mode(str2u(author), str2u(comment), self.db_chans)
        self.mode_ser.saved(mode_id)

    def check_syslist(self, syslist):
        if isinstance(syslist, list):
            if len(syslist) < 1:
                self.mode_ser.loaded('nothing requested to load')
                return False
        return True

    def apply_zeros(self, syslist, a_kinds):
        namelist = self.sys_cache.cnames(syslist, a_kinds)
        print(namelist)


    def applyMode(self, mode_data):
        # mode_data cols: protocol, chan_name, value
        loaded_count, nochange_count, na_count, unknown_count = 0, 0, 0, 0
        epics_chans, epics_values = [], []

        # dump_file = open("/var/tmp/dump" + str(self.dump_count) + ".txt", "w")
        # for x in mode_data:
        #     dump_file.write(str(x) + "\n")
        # dump_file.close()
        # self.dump_count += 1

        for row in mode_data:
            c_row = self.avaliable_cind.get(row[1], None)
            if c_row is None:
                na_count += 1
                print('unavaliable: ', row[1])
                continue
            cdata = c_row[1]
            if row[-1] == cdata[-2]:
                nochange_count += 1
                continue
            if row[0] == 'EPICS':
                epics_chans.append(str(row[1]))
                epics_values.append(row[2])
                loaded_count += 1
                continue
            if row[0] == 'cx':
                chan = self.cind[cdata[1]][0]
                if fabs(chan.val - row[2]) < 2.0 * chan.quant:
                    nochange_count += 1
                    continue
                else:
                    chan.setValue(row[2])
                    loaded_count += 1
                    continue
            unknown_count += 1
        try:
            e_ok = catools.caput(epics_chans, epics_values)
        except:
            print('some epics pv problems', e_ok)
            pass
        msg = 'loaded %d, nochange %d, unavail %d, unknown %d' % \
              (loaded_count, nochange_count, na_count, unknown_count)
        return msg

    def loadMode(self, mode_id, syslist, types):
        if not self.check_syslist(syslist) or not types:
            return
        mode_data = self.db.load_mode(mode_id, syslist, types)
        msg = self.applyMode(mode_data)
        self.mode_ser.loaded(msg)

    def loadMarked(self, mark, syslist, types):
        if not self.check_syslist(syslist) or not types:
            return
        mode_data = self.mode_caches[mark].extract(syslist, types)
        msg = self.applyMode(mode_data)
        self.mode_ser.markedLoaded(mark, msg)

    def markMode(self, mode_id, mark, comment, author):
        self.db.mark_mode(mode_id, mark, comment, author)
        self.mode_caches[mark] = ModeCache(mark, db=self.db, sys_cache=self.sys_cache)
        self.mode_ser.update()

    # currently it's a special load to cycle k500 magnets with drivers automatics
    def walkerLoad(self, walkers_path, coefs=None):
        # walkers_path - is a dict with {'walker': [marks] }
        # coefs - the same dictionary with coefs for values
        for key in walkers_path:
            marks = walkers_path[key]
            if marks[0] is None:
                del marks[0]
            cname = remag_srv + '.' + key + '.Iset'  # case ?
            vs = []
            for m in marks:
                row = self.mode_caches[m].data[cname]
                vs.append(row[2])
            if coefs is not None:
                if coefs[key] is not None:
                    for ind in range(len(vs)):
                        vs[ind] *= coefs[key][ind]
            self.walkers[key].run_list(np.array(vs))

    def dump_state(self):
        dump_file = open("/var/tmp/moded_dump", "w")
        for x in self.db_chans:
            dump_file.write(str(x) + "\n")
        dump_file.close()


class ModeService(CothreadQtService):
    def main(self):
        global QtCore, catools, cothread, signal
        from aQt import QtCore
        import cothread
        from cothread import catools

        signal = QtCore.pyqtSignal
        self.m = ModeDeamon()

    def clean_proc(self):
        self.m.dump_state()


cfg_db = AccConfig()
cfg_db.execute("SELECT protocol FROM protocols_in_use()")
ans = cfg_db.cur.fetchall()
protocols = [p[0] for p in ans]
print(protocols)
if len(protocols) == 1:
    print("Single protocol is in use. Will use native main loop")
    single_protocol = protocols[0]
else:
    print("There are few protocols. Let's use some common main loop")


moded = ModeService("moded")

# from aQt import QtCore
# import cothread
# from cothread import catools
#
# app = QtCore.QCoreApplication(sys.argv)
# cothread.iqt()
#
# m = ModeDeamon()
#
# cothread.WaitForQuit()
