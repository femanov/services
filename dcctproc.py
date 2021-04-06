#!/usr/bin/env python3
import pycx4.pycda as cda
import numpy as np
import scipy as sp
from cservice import CXService
from settings.cx import ctl_server


class DCCTproc:
    def __init__(self):
        dname = ctl_server + '.dcct.'

        # voltage measurement channel
        self.dcctv_chan = cda.DChan("canhw:21.ring_current", on_update=True)

        # input chans
        self.u2i_chan = cda.DChan(dname + 'u2i', on_update=True)
        self.adczero_chan = cda.DChan(dname + 'ADCzero', on_update=True)
        self.storage_fitl_chan = cda.IChan(dname + 'storage_fitlength', on_update=True)
        self.life_fitl_chan = cda.IChan(dname + 'life_fitlength', on_update=True)

        # output channels
        self.beamcur_chan = cda.DChan(dname + 'beamcurrent')
        self.storage_rate_chan = cda.DChan(dname + 'storagerate')
        self.lifetime_chan = cda.DChan(dname + 'lifetime')

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
        self.I = np.zeros(10)
        self.t = np.zeros(10)
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
        self.Is = None
        self.ts = None
        self.I.resize(size)
        self.t.resize(size)
        self.Is = self.I
        self.ts = self.t

    def dcctv_measured(self, chan):
        par = self.params
        beamcur = par['u2i'] * (chan.val - par['ADCzero'])
        self.beamcur_chan.setValue(beamcur)

        if self.I.size < 2:
            return
        self.Is = np.roll(self.Is, -1)
        self.Is[-1] = beamcur
        self.ts = np.roll(self.ts, -1)
        self.ts[-1] = 1e-6 * chan.time

        self.line = sp.polyfit(self.ts, self.Is, 1)
        self.storagerate = self.line[0]
        self.storage_rate_chan.setValue(self.storagerate)
        # 2DO: put lifetime calc here


class DCCTService(CXService):
    def main(self):
        self.dcct = DCCTproc()


s = DCCTService('dcct_proc')
