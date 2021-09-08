#!/usr/bin/env python3

from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys

import pycx4.q5cda as cda

# v2kCAS 172.16.1.110 20041
# v5CAS v2k-k500-1.inp.nsk.su 20041
#
#



class k500state():
    def __init__(self):
        super()

        self.schans = {
            'v5_cas':  cda.StrChan("vcas::v2k-k500-1:20041.VEPP5.K500.Mode"),
            'v2k_cas': cda.StrChan("vcas::172.16.1.110:20041.VEPP5.K500.Mode"),
        }

