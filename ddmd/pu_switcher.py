import sys
if "pycx4.qcda" in sys.modules:
    import pycx4.qcda as cda
elif "pycx4.pycda" in sys.modules:
    import pycx4.pycda as cda

from acc_ctl.mode_ser import ModesClient
from acc_ctl.k500modes import K500Director
from acc_db.db import AccConfig

db = AccConfig()

subsys_names = ['syn', 'linac', 'ring', 'syn.transfer', 'K500.e.ext', 'K500.p.ext', 'K500.com', 'K500.cVEPP3', 'K500.cBEP']
mode_subsys = {x: db.sys_descendants(x) for x in subsys_names}

bline_parts = {
    'e2v2': ['syn', 'linac', 'ring', 'syn.transfer', 'K500.e.ext', 'K500.com', 'K500.cBEP'],
    'p2v2': ['syn', 'linac', 'ring', 'syn.transfer', 'K500.p.ext', 'K500.com', 'K500.cBEP'],
    'e2v4': ['syn', 'linac', 'ring', 'syn.transfer', 'K500.e.ext', 'K500.com', 'K500.cVEPP3'],
    'p2v4': ['syn', 'linac', 'ring', 'syn.transfer', 'K500.p.ext', 'K500.com', 'K500.cVEPP3'],
    'None': [],
}


class PUSwitcher:
    switching_done = cda.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.mode_ctl = kwargs.get('mode_ctl', ModesClient())
        self.k500ctl = kwargs.get('k500ctl', K500Director())

        self.c_k500mode = cda.StrChan('cxhw:0.k500.modet', max_nelems=4)
        self.c_k500user_mode = cda.StrChan('cxout:1.ic_out.mode', max_nelems=4)
        self.c_mode_progress = cda.IChan('cxhw:0.k500.mode_progress')
        self.c_k500_mag_state = cda.StrChan('cxhw:0.k500.mag_state', max_nelems=4)

        self.k500ctl.progressing.connect(self.c_mode_progress.setValue)

        #self.k500ctl.modeCurUpdate.connect(self.update_cur_mode)
        self.k500ctl.done.connect(self.switched)

        self.req_mode = None
        self.all_mode = None

        self.modes = {
            'syn': None,
            'linac': None,
            'ring': None,
            'syn.transfer': None,
            'K500.e.ext': None,
            'K500.p.ext': None,
            'K500.com': None,
            'K500.cBEP': None,
            'K500.cVEPP3': None,
        }

        self.wait_remag = False
        self.timer = cda.Timer()

    def what2switch(self, mode):
        bline = bline_parts[mode]
        return [bline[ind] for ind in range(len(bline)) if mode != self.modes[bline[ind]]]

    def set_mode(self, mode):
        self.all_mode = mode
        self.c_k500mode.setValue(mode)
        self.c_k500user_mode.setValue(mode)
        sw = self.what2switch(mode)
        for x in sw:
            self.modes[x] = mode

    def switch_mode(self, mode, **kwargs):
        if self.all_mode == mode:
            pass
            #return
        if self.req_mode == mode:
            pass
            #return
        self.req_mode = mode

        switch_all = kwargs.get('switch_all', True)
        if switch_all:
            sw = mode_subsys.keys()
        else:
            sw = self.what2switch(mode)
        sys2sw = []
        for k in sw:
            sys2sw += mode_subsys[k]

        self.mode_ctl.load_marked(mode, sys2sw)

        if 'K500.com' in sw:
            self.timer.singleShot(100, self.remag)
        else:
            self.timer.singleShot(500, self.switched)

    def remag(self):
        self.k500ctl.set_mode(self.req_mode)

    def switched(self):
        self.set_mode(self.req_mode)
        self.req_mode = None
        self.switching_done.emit()
