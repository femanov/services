#!/usr/bin/env python3

import time
from aux.Qt import QtCore, QtGui, QtWidgets

from cxwidgets.pspinbox import FSpinBox
from cxwidgets.pcheckbox import FCheckBox

import extractor


class TrainingCtlW(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(TrainingCtlW, self).__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.grid = QtWidgets.QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.setLayout(self.grid)

        self.grid.addWidget(QtWidgets.QLabel("Training shots control"), 0, 0, 1, 4)

        self.grid.addWidget(QtWidgets.QLabel("Interval,s"), 1, 0)

        self.sb_interval = FSpinBox()
        self.grid.addWidget(self.sb_interval, 1, 1)

        self.grid.addWidget(QtWidgets.QLabel("run"), 1, 2)

        self.cb_run = FCheckBox()
        self.grid.addWidget(self.cb_run, 1, 3)

        self.cb_run.stateChanged.connect(self.run_proc)

        extr.trainingStopped.connect(self.training_stopped_proc)

    def run_proc(self, state):
        if state:
            print("starting")
            extr.start_training(self.sb_interval.value())
        else:
            extr.stop_training()

    def training_stopped_proc(self):
        self.cb_run.setValue(False)


class ExtractorWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ExtractorWidget, self).__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.grid = QtWidgets.QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.setLayout(self.grid)

        self.b_start = QtWidgets.QPushButton('start')
        self.grid.addWidget(self.b_start, 0, 0)

        self.b_stop = QtWidgets.QPushButton('stop')
        self.grid.addWidget(self.b_stop, 0, 1)

        self.b_start.clicked.connect(self.extract)
        self.b_stop.clicked.connect(extr.stop)

        extr.unexpectedShot.connect(self.unexpected_shot_proc)
        extr.extractionDone.connect(self.extr_proc)

        self.st_time = 0
        self.fi_time = 0

    def extr_proc(self):
        self.fi_time = time.time()
        print('run time:', self.fi_time - self.st_time)
        self.extract()

    def unexpected_shot_proc(self):
        print("unexpected shot")

    def extract(self):
        self.st_time = time.time()
        extr.extract()



app = QtWidgets.QApplication(['extractor_test'])

extr = extractor.Extractor()

w = ExtractorWidget()
w.show()

w2 = TrainingCtlW()
w2.show()

app.exec_()
