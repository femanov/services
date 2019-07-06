#!/usr/bin/env python3
import pycx4.pycda as cda
import numpy as np
import scipy as sp
from aux.service_daemon import CXService
from settings.cx import ctl_server

dname = ctl_server + '.dcct.'
outdev = "cxout.inp.nsk.su:1.ringcur_users."

class dcct_proc:
    def __init__(self):

        # voltage measurement channel
        self.dcctv_chan = cda.DChan("canhw:21.ring_current")

        # input chans
        self.u2i_chan = cda.DChan(dname + 'u2i')
        self.adczero_chan = cda.DChan(dname + 'ADCzero')
        self.storage_fitl_chan = cda.IChan(dname + 'storage_fitlength')
        self.life_fitl_chan = cda.IChan(dname + 'life_fitlength')

        self.beamcur_chan = cda.DChan(dname + 'beamcurrent')
        self.storage_rate_chan = cda.DChan(dname + 'storagerate')
        self.lifetime_chan = cda.DChan(dname + 'lifetime')

        self.beamcur_chan_out = cda.DChan(outdev + 'beamcurrent')
        self.storage_rate_chan_out = cda.DChan(outdev + 'storagerate')


        self.params = {
            'u2i':               20.51,
            'ADCzero':           0.0,
            'storage_fitlength': 10,
            'life_fitlength':    10,
        }

        self.u2i_chan.valueChanged.connect(self.parUpdate)
        self.adczero_chan.valueChanged.connect(self.parUpdate)
        self.storage_fitl_chan.valueChanged.connect(self.parUpdate)
        self.life_fitl_chan.valueChanged.connect(self.parUpdate)

        self.dcctv_chan.valueMeasured.connect(self.dcctv_measured)

        # data owner arrays
        self.I = np.zeros(self.params['life_fitlength'])
        self.t = np.zeros(self.params['life_fitlength'])
        # copy arrays for shifted views
        self.Is = self.I
        self.ts = self.t

    def parUpdate(self, chan):
        fname = chan.name
        name = fname.split('.')[-1]
        self.params[name] = chan.val
        if name == 'storage_fitlength' or name == 'life_fitlength':
            self.resize_data()

    def resize_data(self):
        pars = self.params
        size = max(pars['storage_fitlength'], pars['life_fitlength'])
        if size == self.I.size:
            return
        self.I.resize(size, refcheck=False)
        self.t.resize(size, refcheck=False)
        self.Is = self.I
        self.ts = self.t

    def dcctv_measured(self, chan):
        par = self.params
        beamcur = par['u2i'] * (chan.val - par['ADCzero'])
        self.beamcur_chan.setValue(beamcur)
        self.beamcur_chan_out.setValue(beamcur)


        if self.I.size < 2:
            return

        self.Is = np.roll(self.Is, -1)
        self.Is[-1] = beamcur
        self.ts = np.roll(self.ts, -1)
        self.ts[-1] = 1e-6 * chan.time

        self.line = sp.polyfit(self.ts, self.Is, 1)
        self.storagerate = self.line[0]
        self.storage_rate_chan.setValue(self.storagerate)
        self.storage_rate_chan_out.setValue(self.storagerate)
        # 2DO: put lifetime calc here


class DCCTService(CXService):
    def main(self):
        self.DCCTm = dcct_proc()


s = DCCTService('dcct_proc')
