#!/usr/bin/env python3

from acc_db.db import AccConfig
import pycx4.pycda as cda
from cservice import CXService
from acc_ctl.daemon_ctrl import DaemonCtl

class Calibrator(DaemonCtl):
    def __init__(self):
        super().__init__('cxhw:0.calibrator')

        db = AccConfig()
        db.execute("select namesys.name,dev.name from chan, devtype_chans, dev_devtype, dev, namesys where "
                   "chan.name=\'do_calb_dac\' and chan.id=devtype_chans.chan_id and "
                   "devtype_chans.devtype_id=dev_devtype.devtype_id and dev_devtype.dev_id=dev.id and"
                   " dev.namesys_id=namesys.id")
        self.cnames = ['.'.join(x) + '.do_calb_dac' for x in db.cur.fetchall()]
        self.clb_chans = [cda.IChan(x) for x in self.cnames]

        self.clb_timer = cda.Timer()
        self.clb_timer.timeout.connect(self.calibrated)

    def reaction(self, cdict):
        if cdict['cmd'] == "calibrate":
            self.calibrate()

    def calibrate(self):
        for x in self.clb_chans:
            x.setValue(1)
        self.clb_timer.singleShot(1000)

    def calibrated(self):
        self.send_pack('calibrated')


class CalibratorService(CXService):
    def main(self):
        self.c = Calibrator()


CalibratorService()




