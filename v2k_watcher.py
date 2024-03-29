#!/usr/bin/env python3

import pycx4.pycda as cda
from cservice import CXService
from settings.cx import v2k_cas

class V2KWatcher:
    def __init__(self):
        self.c_v2k_regime = cda.StrChan(v2k_cas + '.Regime', on_update=True)
        self.c_bep_state = cda.StrChan(v2k_cas + '.BEP.State', on_update=True)

        self.c_v2k_inflector = cda.StrChan(v2k_cas + '.B-3M.BEP_Inflektor', on_update=True)
        self.c_v2k_probros = cda.StrChan(v2k_cas + '.BEP.RF.Probros', on_update=True)
        self.c_v2k_auto_state = cda.StrChan(v2k_cas + '.BEP.Injection.State', on_opdate=True)

        self.c_bep_is_busy = cda.IChan('bep.is_busy', on_update=True)
        self.c_bep_offline = cda.IChan('bep.offline', on_update=True)
        self.c_v2k_particles = cda.StrChan('bep.particles', max_nelems=50, on_update=True)

        self.c_v2k_regime.valueMeasured.connect(self.requested_particles_check)
        self.c_bep_state.valueMeasured.connect(self.bep_busy_check)
        self.c_v2k_inflector.valueMeasured.connect(self.offline_check)
        self.c_v2k_probros.valueMeasured.connect(self.offline_check)
        self.c_v2k_auto_state.valueMeasured.connect(self.offline_check)

    def requested_particles_check(self, chan):
        particles = 'positrons'
        if self.c_v2k_regime.val in {'1', '2'}:
            particles = 'electrons'
        if self.c_v2k_particles.val != particles:
            self.c_v2k_particles.setValue(particles)

    def bep_busy_check(self, chan):
        is_busy = 0
        if self.c_bep_state.val in {'1->2', '2->1', '3->4', '4->3', '2', '4', 'Remagn-1', 'Remagn-3'}:
            is_busy = 1
        if self.c_bep_is_busy.val != is_busy:
            self.c_bep_is_busy.setValue(is_busy)

    def offline_check(self, chan):
        offline = 0
        if self.c_v2k_inflector.val == '0' or self.c_v2k_probros.val == '1' or \
                self.c_v2k_auto_state.val in {'SUSPENDED', 'UNKNOWN'}:
            offline = 1
        if self.c_bep_offline.val != offline:
            self.c_bep_offline.setValue(offline)


class V2KWatcherService(CXService):
    def main(self):
        self.v2k_w = V2KWatcher()

ws = V2KWatcherService('v2k_watcher')
