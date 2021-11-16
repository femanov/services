import sys
if "pycx4.qcda" in sys.modules:
    import pycx4.qcda as cda
elif "pycx4.pycda" in sys.modules:
    import pycx4.pycda as cda
else:
    import pycx4.pycda as cda
from transitions import Machine

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class LinBeamSwitch:
    def __init__(self):
        self.states = ['unknown', 'open', 'closed', 'opening', 'closing']
        self.transitions = [
            {'trigger': 'update', 'source': '*', 'dest': 'unknown', 'conditions': ['is_unknown']},
            {'trigger': 'update', 'source': '*', 'dest': 'open', 'conditions': ['is_open']},
            {'trigger': 'update', 'source': '*', 'dest': 'closed', 'conditions': ['is_closed']},
            {'trigger': 'update', 'source': '*', 'dest': 'opening', 'conditions': ['is_opening']},
            {'trigger': 'update', 'source': '*', 'dest': 'closing', 'conditions': ['is_closing']},
            # {'trigger': '', 'source': '', 'dest': ''},
            # {'trigger': '', 'source': '', 'dest': ''},
        ]

        self.m = Machine(model=self, states=self.states, transitions=self.transitions, initial='unknown')

        self.cav_h_iset_chan = cda.DChan('canhw:11.rst1.CAV_H.Iset', on_update=True)
        self.cav_h_imeas_chan = cda.DChan('canhw:11.rst1.CAV_H.Imes', on_update=True)

        self.cav_h_imeas_chan.setTolerance(10.0)  # 10 mA to react
        self.cav_h_iset_chan.valueChanged.connect(self.cavh_update)
        self.cav_h_imeas_chan.valueChanged.connect(self.cavh_update)

        # cxhw:0.beamswitch.state
        # cxhw:0.beamswitch.state_t
        # cxhw:0.BeamSwitch.SwitchOn
        # cxhw:0.BeamSwitch.SwitchOff

        #self.vepp3_infl_chan = cda.StrChan('cxout:11.vepp3.tInflectorStatus', max_nelems=100)
        #self.vepp3_chan = cda.StrChan('cxout:11.vepp3.tstatus', max_nelems=100)
        #self.vepp3_chan.valueMeasured.connect(self.vepp3_update)

        self.on_chan = cda.IChan('cxhw:0.BeamSwitch.SwitchOn')
        self.off_chan = cda.IChan('cxhw:0.BeamSwitch.SwitchOff')
        self.state_chan = cda.IChan('cxhw:0.BeamSwitch.state')
        self.state_t_chan = cda.StrChan('cxhw:0.beamswitch.state_t', max_nelems=100)


    def on_enter_unknown(self):
        print("unknown state")

    def on_enter_open(self):
        print("beam on")

    def on_enter_closed(self):
        print("beam off")

    def on_enter_opening(self):
        print('opening beam')

    def on_enter_closing(self):
        print('closing beam')

    def is_unknown(self):
        return True if (self.cav_h_imeas_chan.val < 4000 and self.cav_h_imeas_chan.val > -4000) or \
                       (self.cav_h_iset_chan.val < 4000 and self.cav_h_iset_chan.val > -4000) else False

    def is_open(self):
        return True if self.cav_h_imeas_chan.val > 4000 and self.cav_h_iset_chan.val > 4000 else False

    def is_closed(self):
        return True if self.cav_h_imeas_chan.val < -4000 and self.cav_h_iset_chan.val < -4000 else False

    def is_opening(self):
        return True if self.cav_h_imeas_chan.val < 4000 and self.cav_h_iset_chan.val > 4000 else False

    def is_closing(self):
        return True if self.cav_h_imeas_chan.val < -4000 and self.cav_h_iset_chan.val < -4000 else False

    def open_beam(self):
        self.cav_h_iset_chan.setValue(4700)

    def close_beam(self):
        self.cav_h_iset_chan.setValue(-4700)

    def cavh_update(self, chan):
        print(chan.name, chan.val)
        self.update()

    def vepp3_update(self, chan):
        print('update from vepp3: ', chan.name, chan.val)
        if chan.val == 'Injection':
            self.open_beam()
        else:
            self.close_beam()


sw = LinBeamSwitch()

cda.main_loop()


