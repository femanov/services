#!/usr/bin/env python3
from cservice import CXService
from ic_modules.acc_ctl.beam_switch import LinBeamSwitch


class BeamSwitchService(CXService):
    def main(self):
        self.b_swc = LinBeamSwitch()


s = BeamSwitchService('beam_swc', not_daemonize=True)
