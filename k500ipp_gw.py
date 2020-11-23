#!/usr/bin/env python3
import pycx4.pycda as cda
from cservice import CXService

def get_chan_info():
    from settings.db import acc_cfg
    from acc_db.db import AccConfig

    db = AccConfig(**acc_cfg)
    db.execute('select * from nsys_chans_info(32)')

    return db.cur.fetchall()


class k500ipp_gw(CXService):
    def main(self):
        chans = get_chan_info()
        self.gw_chans = [cda.PassGW(x[1], x[1].replace('cxhw:3', 'cxout:3'), on_update=True) for x in chans]


gw = k500ipp_gw('k500_ipp_gw')
