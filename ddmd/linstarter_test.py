#!/usr/bin/env python3

import time
from aux.Qt import QtCore, QtGui, QtWidgets

import linstarter


class LinstarterWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(LinstarterWidget, self).__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.grid = QtWidgets.QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.setLayout(self.grid)

        self.b_start = QtWidgets.QPushButton('start')
        self.grid.addWidget(self.b_start, 0, 0)

        self.b_stop = QtWidgets.QPushButton('stop')
        self.grid.addWidget(self.b_stop, 0, 1)

        self.lin_st = linstarter.LinStarter()
        self.b_start.clicked.connect(self.run_counter)
        self.b_stop.clicked.connect(self.lin_st.stop)

        self.lin_st.runmodeChanged.connect(print)
        self.lin_st.nshotsChanged.connect(print)
        self.lin_st.runDone.connect(self.rundone_proc)

        self.st_time = 0
        self.fi_time = 0

    def rundone_proc(self):
        self.fi_time = time.time()
        print('run time:', self.fi_time - self.st_time)
        self.run_counter()

    def run_counter(self):
        self.st_time = time.time()
        self.lin_st.start()


app = QtWidgets.QApplication(['linstarter test'])


w = LinstarterWidget()
w.show()

app.exec_()
