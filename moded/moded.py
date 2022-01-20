#!/usr/bin/env python3
import numpy as np
import simplejson as json

import pycx4.pycda as cda
from cservice import CXService

from acc_ctl.mode_ser import ModesServer
from acc_ctl.k500modes import remag_devs, remag_srv
from acc_ctl.magwalker import MagWalker

from acc_db.db import ModesDB
from acc_db.mode_cache import SysCache, ModeCache


class ChanFactory:
    def create_chan(self, protocol, name, **kwargs):
        if protocol == 'cx':
            return cda.DChan(name, **kwargs)
        if protocol == 'EPICS':
            return cda.DChan()
        return None


class ModeController:
    def __init__(self):
        self.db = ModesDB()
        ans = self.db.mode_chans()
        self.db_chans = [list(c) for c in ans]
        cf = ChanFactory()

        # dict for faster id-based lookup
        self.cind = {x[2]: cf.create_chan(x[0], x[1]) for x in self.db_chans}
        self.name_ind = {x[1]: x[2] for x in self.db_chans}

        self.mode_ser = ModesServer()  # message server for accelerator mode control
        self.mode_ser.load.connect(self.loadMode)
        self.mode_ser.save.connect(self.save_mode)
        self.mode_ser.loadMarked.connect(self.loadMarked)
        self.mode_ser.markMode.connect(self.markMode)
        self.mode_ser.walkerLoad.connect(self.walkerLoad)
        self.mode_ser.setZeros.connect(self.load_zeros)

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

    def save_mode(self, author, comment):
        cind = self.cind
        data2json = {'columns': ['fullchan_id', 'value', 'time', 'available'],
                     'doc_type': '1.0',
                     'data': {str(k): [cind[k].val, cind[k].time, cind[k].is_available()] for k in cind}}
        data_json = json.dumps(data2json, ignore_nan=True)
        mode_id = self.db.save_mode(author, comment, data_json)
        self.mode_ser.saved(mode_id)

    def check_syslist(self, syslist):
        if isinstance(syslist, list):
            if len(syslist) < 1:
                self.mode_ser.loaded('nothing requested to load')
                return False
        return True

    def applyMode(self, mode_data):
        # mode_data: {id:[value, ...]}
        loaded_count, nochange_count, na_count = 0, 0, 0
        for c_id in mode_data:
            chan = self.cind.get(c_id, None)
            if chan is None:
                na_count += 1
                print('unavaliable: ', c_id)
                continue
            # warning !!! it's not always correct
            if mode_data[c_id][0] == chan.val:
                nochange_count += 1
                continue
            chan.setValue(mode_data[c_id][0])
            loaded_count += 1
        msg = f'loaded {loaded_count}, nochange {nochange_count}, unavailiable {na_count}'
        return msg

    def load_zeros(self, syslist, a_kinds):
        cids = self.sys_cache.cids(syslist, a_kinds)
        zero_mode = {x: [0.0] for x in cids}
        msg = self.applyMode(zero_mode)
        self.mode_ser.loaded(msg)

    def loadMode(self, mode_id, syslist, types):
        if not self.check_syslist(syslist) or not types:
            return
        data = self.db.load_mode(mode_id, syslist, types)
        msg = self.applyMode(data)
        self.mode_ser.loaded(msg)

    def loadMarked(self, mark, syslist, types):
        if not self.check_syslist(syslist) or not types:
            return
        data = self.mode_caches[mark].extract(syslist, types)
        msg = self.applyMode(data)
        self.mode_ser.markedLoaded(mark, msg)

    def markMode(self, mode_id, mark, comment, author):
        self.db.mark_mode(mode_id, mark, comment, author)
        self.mode_caches[mark] = ModeCache(mark, db=self.db, sys_cache=self.sys_cache)
        self.mode_ser.update()

    # currently it's a special load to cycle k500 magnets with drivers automatics
    def walkerLoad(self, walkers_path, coefs=None):
        # walkers_path - is a dict with {'walker': [marks] }
        # coefs - the same dictionary with coefs for values
        #print("walker load: ", walkers_path, coefs)
        for key in walkers_path:
            marks = walkers_path[key]
            if marks[0] is None:
                del marks[0]
            cname = remag_srv + '.' + key + '.Iset'  # case ?
            c_id = self.name_ind[cname]
            vs = []
            for m in marks:
                row = self.mode_caches[m].data[c_id]
                vs.append(row[0])
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


class ModeService(CXService):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.mc = None

    def main(self):
        print('running main')
        self.mc = ModeController()

    def clean_proc(self):
        self.mc.dump_state()



moded = ModeService("moded")

