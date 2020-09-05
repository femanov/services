#!/usr/bin/env python3
import pycx4.pycda as cda
import glob
import time
import os
from fcntl import fcntl, F_GETFL, F_SETFL

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'


def fd_ready(ev):
    ev.file.seek(0)
    lines = ev.file.readlines()
    print(time.time())
    print(lines)

f = open(device_file, 'r')  # open file
os.set_blocking(f.fileno(), False)  # make it nonblocking
#fcntl(f, F_SETFL, fcntl(f, F_GETFL) | os.O_NONBLOCK)  # make it nonblocking

file_ev = cda.FdEvent(f)

file_ev.ready.connect(fd_ready)

cda.main_loop()