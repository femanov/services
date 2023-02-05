from pycx4.pycda import InstSignal, IChan

from transitions import Machine

runmodes = {
    'continuous': 0,
    'counter':   1
}

states = ['fail',               # if some command not finished in expected time
          'unknown',            # just started, no operation data yet
          'switching_runmode',  # we ordered to switch runmode
          'continuous',         # operating in continuous mode
          'counter_idle',       # counter mode idle
          'counter_start',      # counter mode start command issues
          'counter_run']        # counter running

transitions = [
    # initial transitions
    {'trigger': 'init', 'source': 'unknown', 'dest': 'continuous', 'unless': ['is_counter']},
    {'trigger': 'init', 'source': 'unknown', 'dest': 'counter_idle', 'conditions': ['is_counter'],
     'unless': ['is_running']},
    {'trigger': 'init', 'source': 'unknown', 'dest': 'counter_run', 'conditions': ['is_counter', 'is_running']},

    # when runmode switching requested
    {'trigger': 'switch_runmode', 'source': ['continuous', 'counter_idle', 'counter_run'], 'dest': 'switching_runmode'},

    # when recieved data about runmode
    {'trigger': 'update_runmode', 'source': 'continuous', 'dest': 'counter_idle', 'conditions': ['is_counter'],
     'unless': ['is_running']},
    {'trigger': 'update_runmode', 'source': 'counter_idle', 'dest': 'continuous', 'unless': ['is_counter']},

    {'trigger': 'start_request', 'source': 'counter_idle', 'dest': 'counter_start'},
    {'trigger': 'run_confirmed', 'source': 'counter_start', 'dest': 'counter_run'},
    {'trigger': 'run_done', 'source': 'counter_run', 'dest': 'counter_idle'},
    {'trigger': 'run_timed_out', 'source': 'counter_run', 'dest': 'fail'},
    {'trigger': 'reset', 'source': 'fail', 'dest': 'unknown'},

    # {'trigger': 'update', 'source': 'counter_idle', 'dest': 'counter_run',
    #  'conditions': ['is_counter', 'is_running']},

    # {'trigger': 'update', 'source': '*', 'dest': 'on', 'conditions': ['is_on']},
    # {'trigger': 'update', 'source': '*', 'dest': 'off', 'conditions': ['is_off']},
    # {'trigger': 'update', 'source': '*', 'dest': 'turning_on', 'conditions': ['is_turning_on']},
    # {'trigger': 'update', 'source': '*', 'dest': 'turning_off', 'conditions': ['is_turning_off']},
    # {'trigger': '', 'source': '', 'dest': ''},
    # {'trigger': '', 'source': '', 'dest': ''},

    # 2DO: timeout on transition to failed state
]


class LinStarter:
    def __init__(self):
        super().__init__()
        self.runmodeChanged = InstSignal(str)
        self.nshotsChanged = InstSignal(int)
        self.runDone = InstSignal()

        self.m = Machine(model=self, states=states, transitions=transitions, initial='unknown',
                         after_state_change=self.state_notify)

        # state variables.
        self.runmode = None
        self.runmode_req = False
        self.running = False
        self.run_req = False
        self.nshots = 0  # number of requested shots
        self.nshots_req = False

        self.c_runmode = IChan('syn_ie4.mode', on_update=True)
        self.c_running = IChan('syn_ie4.bum_going', on_update=True)
        self.c_lamsig = IChan('syn_ie4.lam_sig', on_update=True)
        self.c_start = IChan('syn_ie4.bum_start', on_update=True)
        self.c_stop = IChan('syn_ie4.bum_stop', on_update=True)
        self.c_nshots = IChan('syn_ie4.re_bum', on_update=True)

        self.c_runmode.valueMeasured.connect(self.runmode_update)
        self.c_running.valueChanged.connect(self.running_update)
        self.c_nshots.valueChanged.connect(self.nshots_update)
        self.c_lamsig.valueMeasured.connect(self.done_proc)

    def state_notify(self):
        print('linstarter machine state: ', self.state)

    def runmode_update(self, chan):
        self.runmode = 'counter' if chan.val == 1 else 'continuous'  # not totally correct
        self.update()
        self.runmodeChanged.emit(self.runmode)

    def done_proc(self, chan):
        if self.running:
            self.running = False
            self.runDone.emit()

    def running_update(self, chan):
        self.running = bool(chan.val)
        print('running:', self.running)
        self.update()

    def is_counter(self):
        return True if self.runmode == 'counter' else False

    def is_running(self):
        return self.running


    def set_runmode(self, runmode):
        if self.runmode != runmode:
            self.c_runmode.setValue(runmodes[runmode])
            self.runmode_req = True


    # check correctness
    def set_nshots(self, nshots):
        if self.nshots != nshots:
            self.c_nshots.setValue(nshots)
            self.nshots_req = True

    def nshots_update(self, chan):
        self.nshots = chan.val
        self.nshots_req = False
        self.nshotsChanged.emit(self.nshots)

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

