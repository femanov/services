#!/usr/bin/env python3
import pycx4.pycda as cda
from cservice import CXService
from ic_modules.acc_ctl.beam_switch import LinBeamSwitch
from settings.cx import ctl_server


class BeamSwitchService(CXService):
    def main(self):
        self.b_swc = LinBeamSwitch()


s = BeamSwitchService('beam_swc', not_daemonize=True)
