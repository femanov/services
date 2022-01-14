#!/usr/bin/env python3
# Notes:
# DS18B20/DS18S20 sensors served by w1_therm linux kernel driver, see
# https://www.kernel.org/doc/html/latest/w1/slaves/w1_therm.html
# highlights:
# - slave devices data can be read using sysfs files which located
# in /sys/bus/w1/devices/ where will device dirs.
# - device dir name starting from device type, in our case: 28 or 10
# - in device dir: w1_slave - all data, temperature - only temperature in mC.
#
# According to my experience sensors connection can be lost due to some
# kind of out of sync. In that case helps only power cycle for sensors.
#
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
import time


class W1Sensor:
    def __init__(self, device_folder):
        self.dev_file = open(device_folder + '/temperature', 'r')
        os.set_blocking(self.dev_file.fileno(), False)  # make it nonblocking
        self.file_ev = cda.FdEvent(self.dev_file)
        self.file_ev.ready.connect(self.fd_ready)

    def fd_ready(self, ev):
        ev.file.seek(0)
        lines = ev.file.readlines()
        # if equals_pos != -1:
        #     self.room_t_chan.setValue(float(lines[1][equals_pos+2:]) / 1000.0 )
        # self.cpu_t_chan.setValue(self.cpu_t.temperature)
        # self.la_chan.setValue(self.la.load_average)


class RpiTherm:
    def __init__(self, pwr_pin=19, expected_devs=1):
        self.line_pwr = DigitalOutputDevice(pwr_pin)
        self.expected_devs = expected_devs
        self.sensors = {}

        self.search_timer = cda.Timer()
        self.pwr_timer = cda.Timer()
        self.pwr_timer.timeout.connect(self.cycle_pwr_finish)

        self.line_pwr.on()
        self.search_timer.singleShot(1000, proc=self.look_for_sensors)
        self.search_retry = 0

    def __del__(self):
        self.line_pwr.off()

    def look_for_sensors(self):
        base_dir = '/sys/bus/w1/devices/'
        device_folder = glob.glob(base_dir + '28*') + glob.glob(base_dir + '10*')
        if len(device_folder) < self.expected_devs:
            self.search_retry += 1
            if self.search_retry == 10:
                self.search_retry = 0
                self.cycle_pwr()
            else:
                self.search_timer.singleShot(1000)
        else:
            print(device_folder)

        # for x in device_folder:
        #    if x not in


    def cycle_pwr(self):
        self.line_pwr.off()
        self.pwr_timer.singleShot(1000)

    def cycle_pwr_finish(self):
        self.line_pwr.on()
        self.search_timer.singleShot(1000)



# class RpiMonitor:
#     def __init__(self):
#         srv = "cxhw:5."
#         hostname = node()
#         cx_devname = hostname.replace('-', '_')
#
#         self.pwr_dev = DigitalOutputDevice(19)
#         self.cpu_t = CPUTemperature()
#         self.la = LoadAverage()
#
#         self.cpu_t_chan = cda.DChan(srv + cx_devname + ".cputemp")
#         self.room_t_chan = cda.DChan(srv + cx_devname + ".roomtemp")
#         self.la_chan = cda.DChan(srv + cx_devname + ".loadaverage")




class RpiMonitorService(CXService):
    def main(self):
        self.rpi_mon = RpiTherm(expected_devs=2)


s = RpiMonitorService('rpi_monitor')

