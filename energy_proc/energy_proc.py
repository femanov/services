#!/usr/bin/env python3
import pycx4.pycda as cda
import numpy as np
from cservice import CXService
from ic_modules.calcs.energy import I2H_dr, H2E


class EnergyCalc(object):
    def __init__(self):
        # registering chans
        self.c_drm_set = cda.DChan("canhw:12.dRM.Iset")
        self.c_crm_set = [cda.DChan(f"canhw:12.rst2.cRM{x+1}.Iset") for x in range(8)]
        self.c_eset = cda.DChan("cxhw:0.info.Emag")
        self.c_drm_set.valueChanged.connect(self.update_energy)
        for x in self.c_crm_set:
            x.valueChanged.connect(self.update_energy)
        self.H = np.zeros(8)
        self.Hmean = 0
        self.Eset = 0

    def update_energy(self, chan):
        H = [I2H_dr(self.c_drm_set.val, self.c_crm_set[x].val, x+1) for x in range(8)]
        self.Hmean = np.mean(H)
        self.Eset = self.Hmean * 300 * 112.0 / 1.0e6
        self.c_eset.setValue(self.Eset)


class EnergyCalcService(CXService):
    def main(self):
        self.Ecalculateor = EnergyCalc()



# this runs service
ser = EnergyCalcService('energy_calc')


