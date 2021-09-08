# level 0 software automatics for injection complex
# IC machne loop
# by Fedor Emanov

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import acc_ctl.modes as modes
from acc_ctl.common import *
from acc_ctl.mode_defs import *
from linstarter import LinStarter, runmodes
from extractor import Extractor

_states = [
    'idle',
    'preinject',
    'injecting',
    'injected',
    'preextract',
    'extracting',
    'extracted'
]


class ICLoop(QObject):
    stateChanged = pyqtSignal(str)
    icmodeChanged = pyqtSignal(str)

    # stage events
    preparing2inject = pyqtSignal()
    injecting = pyqtSignal()
    injected = pyqtSignal()
    preparing2extract = pyqtSignal()
    extracting = pyqtSignal()
    extracted = pyqtSignal()

    def __init__(self):
        QObject.__init__(self)

        self.linStarter = LinStarter()
        self.extractor = Extractor()
        self.modeCtl = modes.ModesClient()

        self.particles = 'e'  #  'e', 'p'
        self.stored_particles = None  # None, 'e', 'p'
        self.requested_particles = None  # None (means do not switch), 'e', 'p'
        self.beam_user = None  # None, 'v2', 'v4'
        self.requested_beam_user = None
        self.requested_runmode = None

        self.ic_runmode = 'manual'  # 'manual', 'single', 'round', 'auto'
        self.state = "idle"
        self.state_ind = 0

        self.shots = {'e': 5, 'p': 50}

        self.kickers_subsys = [22, 18, 19]  # subsystems to switch injection-extraction
        self.ic_subsys = [32, 17, 38, 52, 53, 54, 55, 29, 59, 61, 62, 63, 64, 65, 67, 68, 60, 69, 70,
                          71, 72, 73, 66, 74, 75, 50, 3, 4, 51, 5, 6, 23, 30, 7, 8, 9, 10, 11, 33, 37]
        self.k500_subsys = [34, 24, 45, 12, 56, 13, 46, 14, 57, 15, 47, 43, 76, 58, 44, 48, 26, 25, 49, 28, 27]


        self.timer = QTimer()

        self.modeCtl.markedReady.connect(self.nextState)
        self.linStarter.runDone.connect(self.nextState)
        self.extractor.extractionDone.connect(self.nextState)

        self.states = [
            self.__idle,
            self.__preinject, self.__injecting, self.__injected,
            self.__preextract, self.__extracting, self.__extracted
        ]

    # stat machine switching conditions implementation
    def nextState(self):
        if self.ic_runmode != "manual":
            # for manual operation - just proc requested stage if possible and stop
            self.stateChanged.emit(self.state)
            return

        self.state_ind += 1
        self.state = _states[self.state_ind]
        self.stateChanged.emit(self.state)
        self.states[self.state_ind]()

        if self.state == "injected" and self.ic_runmode in ["round", "auto"]:
            self.nextState()

        if self.state == 'extracted' and self.ic_runmode in ["round", "auto"]:
            self.state_ind = 0
            self.state = _states[self.state_ind]
            self.nextState()


    # state functions: what to do when proceeding to state

    def __idle(self):
        pass

    def __preinject(self):
        # check for requests
        if self.requested_particles:
            pass
        if self.requested_beam_user:
            pass

        self.linStarter.setRunmode(1)
        self.modeCtl.load_marked(mode_map[self.particles + 'inj'], self.kickers_subsys)

    def __injecting(self):
        self.linStarter.newCounterCycle(self.shots[self.particles])
        # after injection initiation - possible some particles already stored
        self.stored_particles = self.particles

    def __injected(self):
        pass

    def __preextract(self):
        self.modeCtl.load_marked(mode_map[self.particles + 'ext'], self.kickers_subsys)

    def __extracting(self):
        self.extractor.extract()

    def __extracted(self):
        # the particles are gone
        self.stored_particles = None

    # commands inplementalions -------------------------

    # not really correct... we need to initiate end of round,
    # extract beam if needed and then make changes to magnetic systems

    def setUseCase(self, particles, beam_user):
        if self.beam_user == beam_user and self.particles == particles:
            # no changes
            return
        mode_subsys = []
        if self.particles == particles and self.beam_user != beam_user:
            # just beam user changed, possibly no changes to IC
            # need to initiate channels remag

            # stop beam if running, don't drop beam
            self.requested_runmode = self.runmode
            if self.state != 'idle':
                self.stop()
            mode_subsys = self.k500_subsys
        if self.particles != particles and self.beam_user == beam_user:
            # need to drop beam and change everything in magsys

            # ask to drop a beam
            if self.state != 'idle':
                self.extract()
            mode_subsys = self.ic_subsys + self.k500_subsys

        if self.particles != particles and self.beam_user != beam_user:
            # need to drop beam and change everything in magsys

            # ask to drop a beam
            if self.state != 'idle':
                self.extract()
            mode_subsys = self.ic_subsys + self.k500_subsys

        start_mode = mode_num(self.particles, self.beam_user)
        target_mode = mode_num(particles, beam_user)

        mag_path = {name: mode_path_num(name, start_mode, target_mode) for name in remag_devs}

        #self.modeCtl.load_marked(mode, mode_subsys)


    def setLinRunMode(self, runmode):
        if isinstance(runmode, str):
            mode_val = runmodes[runmode]
        else:
            mode_val = runmode
        if self.linStarter.runmode == mode_val:
            # no changes
            return
        if self.state != 'idle':
            # if in any automatic stages - go to idle state
            self.stop()
        self.linStarter.setRunmode(runmode)

    def setEshots(self, num):
        self.shots['e'] = int(num)

    def setPshots(self, num):
        self.shots['p'] = int(num)


    # stop any operation
    def stop(self):
        self.ic_runmode = 'manual'
        self.state = 'idle'
        self.state_ind = 0
        self.icmodeChanged.emit(self.ic_runmode)
        self.linStarter.stopCounter()
        self.extractor.stopExtraction()

    def inject(self):
        self.ic_runmode = 'single'
        self.state = 'idle'
        self.state_ind = 0
        self.icmodeChanged.emit(self.ic_runmode)
        self.nextState()

    def extract(self):
        self.ic_runmode = 'manual'
        self.state = 'injected'
        self.state_ind = 3
        self.icmodeChanged.emit(self.ic_runmode)
        self.nextState()

    def execRound(self):
        self.ic_runmode = 'round'
        self.state = 'idle'
        self.state_ind = 0
        self.icmodeChanged.emit(self.ic_runmode)
        self.nextState()

    def execBurst(self):
        self.ic_runmode = 'auto'
        self.state = 'idle'
        self.state_ind = 0
        self.icmodeChanged.emit(self.ic_runmode)
        self.nextState()

