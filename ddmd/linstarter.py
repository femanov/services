import pycx4.pycda as cda

cx_srv = 'canhw:19'
prefix = cx_srv + '.'

runmodes = {
    'continous': 0,
    'counter':   1
}
# syn_ie4.bum_going - not yet used, do i need it?


class LinStarter:
    runmodeChanged = cda.Signal(str)
    nshotsChanged = cda.Signal(int)
    runDone = cda.Signal()

    def __init__(self):
        super().__init__()

        # state variables.
        self.runmode = None
        self.runmode_req = False
        self.running = False
        self.run_req = False
        self.nshots = 0  # number of requested shots
        self.nshots_req = False
        self.eshots = 5
        self.pshots = 10
        self.particles = 'e'

        self.c_runmode = cda.DChan(prefix + 'syn_ie4.mode', on_update=True)
        self.c_start = cda.DChan(prefix + 'syn_ie4.bum_start', on_update=True)
        self.c_stop = cda.DChan(prefix + 'syn_ie4.bum_stop', on_update=True)
        self.c_lamsig = cda.DChan(prefix + 'syn_ie4.lam_sig', on_update=True)
        self.c_nshots = cda.DChan(prefix + 'syn_ie4.re_bum', on_update=True)

        self.c_runmode.valueMeasured.connect(self.runmode_update)
        self.c_nshots.valueChanged.connect(self.nshots_update)
        self.c_lamsig.valueMeasured.connect(self.done_proc)

        self.c_eshots = cda.DChan('cxhw:0.ddm.eshots')
        self.c_pshots = cda.DChan('cxhw:0.ddm.pshots')
        self.c_eshots.valueChanged.connect(self.shots_update)
        self.c_pshots.valueChanged.connect(self.shots_update)

    def shots_update(self, chan):
        if chan is self.c_eshots:
            if chan.val == 0:
                chan.setValue(self.eshots)
                return
            self.eshots = chan.val
            if self.particles == 'e':
                self.set_nshots(self.eshots)
        if chan is self.c_pshots:
            if chan.val == 0:
                chan.setValue(self.pshots)
                return
            self.pshots = chan.val
            if self.particles == 'p':
                self.set_nshots(self.pshots)

    def set_nshots(self, nshots):
        if self.nshots != nshots:
            self.c_nshots.setValue(nshots)
            self.nshots_req = True

    def nshots_update(self, chan):
        self.nshots = chan.val
        self.nshots_req = False
        self.nshotsChanged.emit(self.nshots)

    def set_particles(self, particles):
        self.particles = particles
        if self.particles == 'e':
            self.set_nshots(self.eshots)
        if self.particles == 'p':
            self.set_nshots(self.pshots)

    def set_runmode(self, runmode):
        if self.runmode != runmode:
            self.c_runmode.setValue(runmodes[runmode])
            self.runmode_req = True

    def runmode_update(self, chan):
        self.runmode = next(key for key, value in runmodes.items() if value == chan.val)
        self.runmode_req = False
        self.runmodeChanged.emit(self.runmode)

    def done_proc(self, chan):
        if self.running:
            self.running = False
            self.runDone.emit()

    def start(self):
        if self.runmode == 'continous':
            self.set_runmode('counter')
        #we just corrected runmode...not checking, if not working need to make correct checks
        #if self.runmode == 'counter' and not self.running:
        self.running = True
        self.c_start.setValue(1)

    def stop(self):
        self.c_stop.setValue(1)
        self.running = False

    def shots_left_update(self, chan):
        pass

