#!/usr/bin/env python3

import socket
import struct
import pycx4.pycda as cda
import numpy as np
from cservice import CXService
import binascii

#import signal
#signal.signal(signal.SIGINT, signal.SIG_DFL)


HOST = '192.168.130.231'    # The remote host
PORT = 12333             # The same port as used by the server
MESSAGE = b"hello"
cx_srv = 'cxhw:5'

# initial notation
# (13763000488061961256, 3458764540642773544, 10448351162332799272) wg1 --> wg2
# (16501189061519273000, 12033618231171627816, 1657324689677045544) wg2 --> wg1
# (11762278205136004136, 14932812342802399784, 11618442293006055720) wg3
# (9528492789967575080, 15221042718949404200, 12194623769361547048) wg4
# (13491660462039867176,) room

# wg-top - temp1, wg-mid - temp2, wg-bottom - temp3
sensors_map = {
    16501189061519273000: 'wg1.temp2',
    12033618231171627816: 'wg1.temp3',
    1657324689677045544:  'wg1.temp1',

    13763000488061961256: 'wg2.temp2',
    3458764540642773544:  'wg2.temp1',
    10448351162332799272: 'wg2.temp3',

    11762278205136004136: 'wg3.temp2',
    14932812342802399784: 'wg3.temp3',
    11618442293006055720: 'wg3.temp1',

    9528492789967575080:  'wg4.temp2',
    15221042718949404200: 'wg4.temp1',
    12194623769361547048: 'wg4.temp3',

    13491660462039867176: 'kls_hall.t',
}


def verefy_checksum(data_in):
    a = np.frombuffer(data_in, dtype=np.uint8)
    b = np.zeros(1, dtype=np.uint16)
    for i in range(len(a)-1):
        b[0] += a[i]
    c = np.bitwise_and(b[0], 0xFF)
    # return c == a[-1]
    return True

def sensor_ids(rom_code):
    # ROM code: 8bit crc + 48 bit serial + 8 bit family
    #ids = struct.unpack("Q" * ndevs, data[3:3 + 8 * ndevs])
    pass

class ArdThermo:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.file_ev = cda.FdEvent(self.sock)
        self.file_ev.ready.connect(self.receive_pack)
        self.pack_count = 0

        self.chans = {cname: cda.DChan(f"{cx_srv}.{cname}") for cname in sensors_map.values()}

        self.ids = {}
        self.timer = cda.Timer()
        self.timer.timeout.connect(self.request_data)
        self.request_data()

    def receive_pack(self, ev):
        data, addr = self.sock.recvfrom(1024)
        if not verefy_checksum(data):
            print("bad checksum, dropping packet")
            return
        pack_type, nline, ndevs = struct.unpack('bbb', data[:3])

        if pack_type == 1:
            ids = struct.unpack("Q" * ndevs, data[3:3+8*ndevs])
            ms = struct.unpack("I", data[3+8*ndevs:3+8*ndevs+4])
            self.ids[nline] = ids
            print(ids)

        elif pack_type == 2:
            ts = struct.unpack("h" * ndevs, data[3:3+2*ndevs])
            ms = struct.unpack("I", data[3+2*ndevs:3+2*ndevs+4])

            for i in range(len(ts)):
                if ts[i] == -7040 or ts[i] == 10880:
                    continue
                try:
                    cname = sensors_map[self.ids[nline-1][i]]
                    self.chans[cname].setValue(ts[i] / 128)
                except IndexError:
                    print(nline)
                    print(ts)


        self.pack_count += 1

        if self.pack_count > 5:
            self.pack_count = 0
            # sending keep-alive
            self.request_data()

    def request_data(self):
        self.sock.sendto(MESSAGE, (HOST, PORT))
        self.timer.singleShot(15000)


class ArdTermService(CXService):
    def main(self):
        self.temps_d = ArdThermo()


s = ArdTermService("linac_kls_thermo")

