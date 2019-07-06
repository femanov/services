#!/usr/bin/env python3
import pycx4.pycda as cda
from aux.service_daemon import CXService


class PassChanTest(CXService):
    def main(self):
        self.pc = cda.PassGW('cxhw:0.dcct.ExtractionCurrent',
                               'cxout:1.ringcur_users.ExtractedCurrent',
                               on_update=True)


s = PassChanTest('pc_test')
