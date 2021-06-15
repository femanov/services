#!/usr/bin/env python3

import socket
import struct
import pycx4.pycda as cda
import numpy as np
from cservice import CXService

#import signal
#signal.signal(signal.SIGINT, signal.SIG_DFL)


HOST = '192.168.130.231'    # The remote host
PORT = 12333             # The same port as used by the server
MESSAGE = b"hello"
cx_srv = 'cxhw:5'

# id:num
sensors = {
    #line 0
    16501189061519273000: 1,
    12033618231171627816: 2,
    1657324689677045544:  3,
    #line 1
    13763000488061961256: 1,
    3458764540642773544:  2,
    10448351162332799272: 3,
    #line 2
    11762278205136004136: 1,
    14932812342802399784: 2,
    11618442293006055720: 3,
    #line 3 - yet unknown
    #line 4 - room temp sensor
    13491660462039867176: 1,
}


def verefy_checksum(data_in):
    a = np.frombuffer(data_in, dtype=np.uint8)
    b = np.zeros(1, dtype=np.uint16)
    for i in range(len(a)-1):
        b[0] += a[i]
    c = np.bitwise_and(b[0], 0xFF)
    # return c == a[-1]
    return True


class ArdThermo:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.file_ev = cda.FdEvent(self.sock)
        self.file_ev.ready.connect(self.recive_pack)
        self.pack_count = 0

        self.chans = {ln+1: {sn+1: cda.DChan("{srv}.wg{wgn}.temp{sensn}".format(srv=cx_srv, wgn=ln, sensn=sn+1))
                      for sn in range(3)} for ln in range(4)}
        self.chans[5] = {1: cda.DChan("{srv}.wg{wgn}.t".format(srv=cx_srv, wgn=4, sensn=1))}
        self.ids = {}

        self.timer = cda.Timer()
        self.timer.timeout.connect(self.request_data)

        self.request_data()

    def recive_pack(self, ev):
        data, addr = self.sock.recvfrom(1024)
        if not verefy_checksum(data):
            print("bad checksum, dropping packet")
            return
        pack_type, nline, ndevs = struct.unpack('bbb', data[:3])
        #print("pack_type=", pack_type, "line=", nline, " ndevs=", ndevs)

        if pack_type == 1:
            ids = struct.unpack("Q" * ndevs, data[3:3+8*ndevs])
            ms = struct.unpack("I", data[3+8*ndevs:3+8*ndevs+4])
            self.ids[nline] = ids
            #print(ids, ms[0])

        elif pack_type == 2:
            ts = struct.unpack("h" * ndevs, data[3:3+2*ndevs])
            ms = struct.unpack("I", data[3+2*ndevs:3+2*ndevs+4])
            for i in range(len(ts)):
                if ts[i] == -7040:
                    continue
                self.chans[nline][i+1].setValue(ts[i]/128)
            # for x in ts:
            #     print(x/128)
            #print("conv_millis=", ms[0])

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

