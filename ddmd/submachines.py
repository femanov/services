
from PyQt4.QtCore import *
import cothread.catools as catools
import pycx4.qcda as cda
import acc_ctl.modes as modes


class linStarter(QObject):

    runmodeChanged = pyqtSignal(int)
    shotsLeftChanged = pyqtSignal(int)
    counterRunChanged = pyqtSignal(int)
    neventsChanged = pyqtSignal(int)
    runDone = pyqtSignal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)

        # state variables.
        self.runmode = 0  # 0 - continous, 1 - counter
        self.runRequested = 0  # 0 - run not requested, 1 - requested
        self.counterRun = 0  # 0 - not running, 1 - running
        self.shotsLeft = 0  # 4095 - stop point
        self.nevents = 0  # inctementing when counter cycle ends
        self.nshots = 0 # number of requested shots

        # pre-connect PV's
        self.pvs_connect = [
            "V5:SYN:Status00C.B4",
            "V5:SYN:CountC",
            "V5:SYN:StartC.PROC",
            "V5:SYN:StopC.PROC"
        ]

        catools.connect(self.pvs_connect)

        catools.camonitor("V5:SYN:CountM", self.shotsLeftUpdate, datatype=int)
        catools.camonitor("V5:SYN:EventM", self.neventsUpdate, datatype=int)
        catools.camonitor("V5:SYN:Status00Rbv", self.statusUpdate, datatype=int)

    def shotsLeftUpdate(self, value):
        self.shootsLeft = value
        self.shotsLeftChanged.emit(value)
        if value > 3500 and value < 4094:
            self.stopCounter()
            print("stop error")

    def neventsUpdate(self, value):
        self.nevents = value
        self.neventsChanged.emit(value)
        if self.runRequested == 1:
            self.runRequested = 0
            self.runDone.emit()

    def statusUpdate(self, value):
        runmode = (value & 0b10000) >> 4
        if self.runmode != runmode:
            self.runmode = runmode
            self.runmodeChanged.emit(runmode)
        counterRun = int(not ((value & 0b1000000) >> 6))
        if counterRun != self.counterRun:
            self.counterRun = counterRun
            self.counterRunChanged.emit(counterRun)

    # Low Level requests

    def setRunmode(self, mode):
        if self.runmode != mode:
            catools.caput("V5:SYN:Status00C.B4", mode)

    def setCounter(self, nshots):
        if self.nshots == nshots:
            return
        self.shotsLeftChanged.emit(nshots)
        catools.caput("V5:SYN:CountC", nshots)

    def startCounter(self):
        if self.runmode == 1 and self.counterRun == 0:
            self.runRequested = 1
            catools.caput("V5:SYN:StartC.PROC", 1)  # run
        else:
            print("running")
            catools.caput("V5:SYN:StartC.PROC", 1)

    def stopCounter(self):
        catools.caput("V5:SYN:StopC.PROC", 1)

    # High Level Requests

    def newCounterCycle(self, nshots):
        if self.nshots != nshots:
            self.setCounter(nshots)
        self.startCounter()

# ---------------------------------------------------------------------------


class extractor(QObject):

    eventCountChanged = pyqtSignal(int)
    extractMaskChanged = pyqtSignal(int)
    startSrcChanged = pyqtSignal(int)
    extracting = pyqtSignal()
    extractionDone = pyqtSignal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)

        self.extractMask = 0  # 0 - no mask, 1 - mask
        self.extractStatus = 0
        self.extractRequest = 0  # 0 - idle, 1 - requested
        self.eventCount = 0    # incrementing when cycle end.
        self.startSrc = 0 # source of starting signals

        self.pvs_connect = [
            "V5:SYN:XFER:SwitchC",
            "V5:SYN:XFER:MaskC.B0",
            "V5:SYN:XFER:StartC.PROC",
            "V5:SYN:XFER:StopC.PROC"
        ]
        catools.connect(self.pvs_connect)

        catools.camonitor("V5:SYN:XFER:EventM", self.eventUpdate, datatype=int)
        catools.camonitor("V5:SYN:XFER:StatusRbv", self.statusUpdate, datatype=int)
        catools.camonitor("V5:SYN:XFER:MaskC.RBV", self.maskUpdate, datatype=int)
        catools.camonitor("V5:SYN:XFER:SwitchC", self.startSrcUpdate, datatype=int)

    def eventUpdate(self, value):
        self.eventCount = value
        self.eventCountChanged.emit(value)
        if self.extractRequest == 1:
            self.extractRequest = 0
            self.extractionDone.emit()

    def statusUpdate(self, value):
        extractStatus = (value & 0b01000000) >> 6
        if self.extractStatus != extractStatus:
            self.extractStatus = extractStatus

    def maskUpdate(self, value):
        maskB0 = value & 0b1
        if self.extractMask == maskB0:
            self.extractMask = maskB0
            self.extractMaskChanged.emit(maskB0)

    def startSrcUpdate(self, value):
        self.startSrc = value
        self.startSrcChanged.emit(value)

    def setStartSrc(self, value):
        if self.startSrc != value:
            catools.caput("V5:SYN:XFER:SwitchC", value)

    def setExtractMask(self, mask):
        if self.extractMask != mask:
            catools.caput("V5:SYN:XFER:MaskC.B0", mask)

    def stopExtraction(self):
        if self.extractRequest == 1:
            self.extractRequest = 0
            catools.caput("V5:SYN:XFER:StopC.PROC", 1)

    def extract(self):
        if self.extractRequest == 0:
            catools.caput("V5:SYN:XFER:StartC.PROC", 1)
            self.extractRequest = 1
            self.extracting.emit()

# --------------------------------------------------------------------------



class InjExtLoop(QObject):
    stateChanged = pyqtSignal(int)
    icmodeChanged = pyqtSignal(int)

    def __init__(self):
        QObject.__init__(self)

        self.particles = 0  # 0 - electrons, 1 - positrons
        self.state = 0
        # 0 - idle, 1 - preinject, 2 - inject, 3 - injected,
        # 4 - preextract, 5 - extract, 6 - extracted
        self.ic_runmode = 0  # 0 - idle, 1 - single-stage, 2 - single cycle, 3 - repeat cycle

        self.shots = [10, 20]
        self.linStarter = linStarter()
        self.extractor = extractor()
        self.modeCtl = modes.ModesClient()
        self.mode_subsys = [22, 18, 19]
        self.modes = [[1, 2], [3, 4]]  # modes[particles][inj_ext]

        self.timer = QTimer()
        self.modeCtl.markedReady.connect(self.nextState)
        self.linStarter.runDone.connect(self.nextState)
        self.extractor.extractionDone.connect(self.nextState)

        self.states = [
            self.__idle,
            self.__preinject, self.__inject2, self.__injected,
            self.__preextract, self.__extract2, self.__extracted
        ]
        self.stateMsg = [
            "Stopped!",
            "Preparing for injection",
            "Injecting",
            "Injection finished",
            "Preparing for extraction",
            "Extracting",
            "Beam Extracted"
        ]

    def nextState(self):
        if self.ic_runmode < 0:
            self.stateChanged.emit(self.state)
            return

        self.state += 1
        self.stateChanged.emit(self.state)

        self.states[self.state]()

        #condition to extract after injection
        if self.state == 3 and self.ic_runmode > 1:
            self.timer.singleShot(1, self.nextState)

        # condition to return for next inject-extract
        if self.state == 6 and self.ic_runmode > 2:
            self.timer.singleShot(1, self.nextState)
            self.state = 0

    def __idle(self):
        pass

    def __preinject(self):
        self.linStarter.setRunmode(1)
        mode = self.modes[self.particles][0]  # 0 - injection
        self.modeCtl.load_marked(mode, self.mode_subsys, ['rw'])

    def __inject2(self):
        self.linStarter.newCounterCycle(self.shots[self.particles])

    def __injected(self):
        pass

    def __preextract(self):
        self.linStarter.setRunmode(1)
        mode = self.modes[self.particles][1]  # 1 - extraction modes
        self.modeCtl.load_marked(mode, self.mode_subsys, ['rw'])

    def __extract2(self):
        self.extractor.extract()

    def __extracted(self):
        pass

    def setParticles(self, particles):
        self.particles = particles

    def setEshots(self, num):
        self.shots[0] = num

    def setPshots(self, num):
        self.shots[1] = num

    # stop any operation
    def stop(self):
        self.ic_runmode = 0
        self.icmodeChanged.emit(self.ic_runmode)
        self.state = 0
        self.linStarter.stopCounter()
        self.extractor.stopExtraction()

    def inject(self):
        self.ic_runmode = 1
        self.icmodeChanged.emit(self.ic_runmode)
        self.state = 0
        self.nextState()

    def extract(self):
        self.ic_runmode = 1
        self.icmodeChanged.emit(self.ic_runmode)
        self.state = 3
        self.nextState()

    def execRound(self):
        self.ic_runmode = 2
        self.icmodeChanged.emit(self.ic_runmode)
        self.state = 0
        self.nextState()

    def execBurst(self):
        self.ic_runmode = 3
        self.icmodeChanged.emit(self.ic_runmode)
        self.state = 0
        self.nextState()
