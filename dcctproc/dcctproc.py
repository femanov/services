#!/usr/bin/env python3
import pycx4.pycda as cda
import numpy as np
from cservice import CXService
from settings.cx import ctl_server
import scipy.constants as const

# IC damping
f0 = 10.94e06  # hz
t0 = 1./f0


def current2n_no(current):
    """
    converts DR current to particle number (e- or e+)
    :param current: beam current in mA
    :return: N - particles number
    """
    return (current * t0) / (1000 * const.e)


class DCCTproc:
    def __init__(self):
        dname = ctl_server + '.dcct.'
        # voltage measurement channel
        self.dcctv_chan = cda.DChan("canhw:21.ring_current", on_update=True)
        self.dcctv_chan.valueMeasured.connect(self.dcctv_measured)

        # input chans
        self.adczero_chan = cda.DChan(dname + 'ADCzero', on_update=True)
        # self.u2i_chan = cda.DChan(dname + 'u2i', on_update=True)
        # self.storage_fitl_chan = cda.IChan(dname + 'storage_fitlength', on_update=True)
        # self.life_fitl_chan = cda.IChan(dname + 'life_fitlength', on_update=True)

        self.adczero_chan.valueChanged.connect(self.adc_zero_update)
        # self.u2i_chan.valueChanged.connect(self.parUpdate)
        # self.storage_fitl_chan.valueChanged.connect(self.parUpdate)
        # self.life_fitl_chan.valueChanged.connect(self.parUpdate)

        # output channels
        self.beamcur_chan = cda.DChan(dname + 'beamcurrent')
        self.storage_rate_chan = cda.DChan(dname + 'storagerate')
        self.lifetime_chan = cda.DChan(dname + 'lifetime')
        self.curstep_chan = cda.DChan(f'{dname}.currentstep')

        self.n_beam_chan = cda.DChan(f'{dname}.Nbeam')
        self.n_step_chan = cda.DChan(f'{dname}.Nstep')

        self.u2i = 20.50  # calibration coefficient
        self.adc_zero = 0.0

        # data owner arrays
        self.I = np.zeros(20)
        self.t = np.zeros(20)
        # copy arrays for shifted views
        self.Is = self.I
        self.ts = self.t

        self.step_processing = False
        self.step_base = 0
        self.step_top = 0
        self.prev_beamcur = None

    def adc_zero_update(self, chan):
        self.adc_zero = chan.val

    def dcctv_measured(self, chan):
        beamcur = self.u2i * (chan.val - self.adc_zero)
        self.beamcur_chan.setValue(beamcur)
        self.n_beam_chan.setValue(current2n_no(beamcur))

        if self.I.size < 2:
            return
        self.Is = np.roll(self.Is, -1)
        self.Is[-1] = beamcur
        self.ts = np.roll(self.ts, -1)
        self.ts[-1] = 1e-6 * chan.time

        # self.line = sp.polyfit(self.ts, self.Is, 1)
        # self.storagerate = self.line[0]
        # self.storage_rate_chan.setValue(self.storagerate)
        # 2DO: put lifetime calc here

        # experimental step-up detection
        # first: threshold = 0.1 mA
        Ib = self.Is[-1]
        Ib_rpev = self.Is[-2]
        if ((Ib - Ib_rpev) > 0.02) and (not self.step_processing):
            self.step_processing = True
            self.step_base = Ib_rpev
        elif self.step_processing and (np.abs(Ib - Ib_rpev) < 0.02):
            self.step_top = np.max((Ib, Ib_rpev))
            self.step_processing = False
            cur_step = self.step_top - self.step_base
            self.curstep_chan.setValue(cur_step)
            self.n_step_chan.setValue(current2n_no(cur_step))


class DCCTService(CXService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dcct = None

    def main(self):
        self.dcct = DCCTproc()


s = DCCTService('dcct_proc', not_daemonize=True)
