#!/usr/bin/env python3
# Notes:
# onboard devices looks like always ready to read, so in order to avoid
# huge loads: will read them when ds* temperature ready.
# In modern kernel driver we don't need to parse w1_slave
# since only temperature available through dedicated sysfs file


from gpiozero import LoadAverage, CPUTemperature, DigitalOutputDevice
import pycx4.pycda as cda
import glob
import os
from platform import node
from cservice import CXService



class RpiMonitor:
    def __init__(self):
        srv = "cxhw:5."
        hostname = node()
        cx_devname = hostname.replace('-', '_')

        self.pwr_dev = DigitalOutputDevice(19)
        self.cpu_t = CPUTemperature()
        self.la = LoadAverage()

        self.cpu_t_chan = cda.DChan(srv + cx_devname + ".cputemp")
        self.room_t_chan = cda.DChan(srv + cx_devname + ".roomtemp")
        self.la_chan = cda.DChan(srv + cx_devname + ".loadaverage")


    def look_for_sensor(self):
        base_dir = '/sys/bus/w1/devices/'
        device_folder = glob.glob(base_dir + '28*')[0]
        device_file = device_folder + '/temperature'
        self.room_t_dev = open(device_file, 'r')
        os.set_blocking(self.room_t_dev.fileno(), False)  # make it nonblocking
        self.file_ev = cda.FdEvent(self.room_t_dev)
        self.file_ev.ready.connect(self.fd_ready)


    def fd_ready(self, ev):
        ev.file.seek(0)
        lines = ev.file.readlines()

        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            self.room_t_chan.setValue(float(lines[1][equals_pos+2:]) / 1000.0 )
        self.cpu_t_chan.setValue(self.cpu_t.temperature)
        self.la_chan.setValue(self.la.load_average)


class RpiMonitorService(CXService):
    def main(self):
        self.rpi_mon = RpiMonitor()


s = RpiMonitorService('rpi_monitor')

