#!/usr/bin/env python3

from cothread.catools import camonitor
import cothread
import signal
import math
import pycx4.q5cda as cda
from settings.cx import pwa1_server
import datetime
import time
from acc_ctl.service_daemon import Service



signal.signal(signal.SIGINT, signal.SIG_DFL)

uiPVs = ['V5:PA:PhaseVoltage1M', 'V5:PA:PhaseVoltage2M', 'V5:PA:PhaseVoltage3M',
         'V5:PA:Current1M', 'V5:PA:Current2M','V5:PA:Current3M']

uicnames = ['Uph1', 'Uph2', 'Uph3', 'Iph1', 'Iph2', 'Iph3']

powerPVs = ['V5:PA:ActivePower1M', 'V5:PA:ActivePower2M', 'V5:PA:ActivePower3M',
       'V5:PA:ReactivePower1M', 'V5:PA:ReactivePower2M', 'V5:PA:ReactivePower3M']

cnames = ['pa1', 'pa2', 'pa3',
          'pr1', 'pr2', 'pr3',
          'paFull', 'prFull', 'pfull', 'cos_fi']

upd = [0] * 6
powers = [0.0] * 6
full_power = 0.0
active_power = 0.0
reactive_power = 0.0
E_today = 0
workdate = datetime.date.today()
last_time = time.time()


def PowerNewData(value, index):
    global upd, powers, workdate, last_time, E_today, etoday_chan
    powers[index] = value
    upd[index] = 1
    if sum(upd) == 6:
        upd = [0] * 6
        full_power = math.sqrt(powers[0]**2 + powers[3]**2) + \
                     math.sqrt(powers[1] ** 2 + powers[4] ** 2) + \
                     math.sqrt(powers[2]**2 + powers[5]**2)
        active_power = sum(powers[0:3])
        reactive_power = sum(powers[3:6])
        pchans[6].setValue(active_power)
        pchans[7].setValue(reactive_power)
        pchans[8].setValue(full_power)
        pchans[9].setValue(active_power/full_power)
        for i in range(6):
            pchans[i].setValue(powers[i])
        if (datetime.date.today() - workdate).days > 0:
            workdate = datetime.date.today()
            elastday_chan.setValue(E_today)
            E_today = 0
        t = time.time()
        dt = t - last_time
        last_time = t
        E_today += dt * full_power/3600.0
        etoday_chan.setValue(E_today)


def UINewData(value, index):
    uichans[index].setValue(value)

app = cothread.iqt()

a = camonitor(powerPVs, PowerNewData)
pchans = [cda.DChan(pwa1_server + '.' + x) for x in cnames]

b = camonitor(uiPVs, UINewData)
uichans = [cda.DChan(pwa1_server + '.' + x) for x in uicnames]

etoday_chan = cda.DChan(pwa1_server + '.Etoday')
elastday_chan = cda.DChan(pwa1_server + '.Elastday')

cothread.WaitForQuit()
