#!/usr/bin/env python3
import time
import io
import os
import pycx4.pycda as cda


sensor_file = '/sys/class/thermal/thermal_zone0/temp'
f = io.open(sensor_file, 'r')
os.set_blocking(f.fileno(), False)  # make it nonblocking


def fd_ready(ev):
    ev.file.seek(0)
    t_cpu = float(f.readline().strip()) / 1000
    print(t_cpu, time.time())
    time.sleep(1)


file_ev = cda.FdEvent(f)

file_ev.ready.connect(fd_ready)

cda.main_loop()

