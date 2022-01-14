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
import time


class RpiThermo:
    """"
    DS18B20/DS18S20 sensors served by w1_therm linux kernel driver, see
    https://www.kernel.org/doc/html/latest/w1/slaves/w1_therm.html
    highlights:
    - slave devices data can be read using sysfs files which located
    in /sys/bus/w1/devices/ where will device dirs.
    - device dir name starting from device type, in our case: 28 or 10
    - in device dir: w1_slave - all data, temperature - only temperature in
    mC.

    According to my experience sensors connection can be lost due to some
    kind of out of sync. In that case helps only power cycle for sensors.

    """
    def __init__(self, pwr_pin=19):
        self.line_pwr = DigitalOutputDevice(pwr_pin)
        self.sensor_files = {}

        self.start_time = time.time()
        self.timer = cda.Timer()

        self.line_pwr.on()
        self.timer.singleShot(100, proc=self.look_for_sensors)
        self.search_retry = 0

    def look_for_sensors(self):
        base_dir = '/sys/bus/w1/devices/'
        device_folder = glob.glob(base_dir + '28*') + glob.glob(base_dir + '10*')
        #print(device_folder)
        if len(device_folder) == 1:
            print("1 found, time = ", time.time() - self.start_time)
            self.search_retry += 1
            if self.search_retry < 100:
                self.timer.singleShot(10)
        if len(device_folder) == 2:
            print("2 found, time = ", time.time() - self.start_time)
            cda.break_()

        if len(device_folder) == 0:
            self.search_retry += 1
            if self.search_retry < 100:
                self.timer.singleShot(10)


        #device_file = device_folder + '/temperature'

        # self.room_t_dev = open(device_file, 'r')
        # os.set_blocking(self.room_t_dev.fileno(), False)  # make it nonblocking
        # self.file_ev = cda.FdEvent(self.room_t_dev)
        # self.file_ev.ready.connect(self.fd_ready)


    def fd_ready(self, ev):
        ev.file.seek(0)
        lines = ev.file.readlines()
        # if equals_pos != -1:
        #     self.room_t_chan.setValue(float(lines[1][equals_pos+2:]) / 1000.0 )
        # self.cpu_t_chan.setValue(self.cpu_t.temperature)
        # self.la_chan.setValue(self.la.load_average)



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
        self.rpi_mon = RpiThermo()


s = RpiMonitorService('rpi_monitor')

