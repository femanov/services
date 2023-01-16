#!/usr/bin/env python3
import pycx4.pycda as cda
import numpy as np
import scipy as sp
from cservice import CXService
from settings.cx import ctl_server


class Kls1Interlocker:
    def __init__(self):
        self.ipump_chan = cda.DChan("canhw:13.kls1.ionpump.current", on_update=True)
        self.ipump_chan.valueMeasured.connect(self.ipump_measured)

        self.kls_hv_chan = cda.DChan("cxhw:25.kls1.hvset", on_update=True)
        self.kls_hv_chan.valueMeasured.connect(self.kls_hv_update)

        self.interlock = False

    def ipump_measured(self, chan):
        if chan.val > 50.0:
            self.interlock = True
            self.kls_hv_chan.setValue(30000)
        else:
            self.interlock = False

    def kls_hv_update(self, chan):
        if self.interlock:
            if chan.val > 30000:
                self.kls_hv_chan.setValue(30000)


class KlsInterlockService(CXService):
    def main(self):
        self.dcct = Kls1Interlocker()


s = KlsInterlockService('kla1_interlock')
