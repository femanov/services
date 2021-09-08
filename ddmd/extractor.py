import pycx4.pycda as cda

# exrtaction control channels
# canhw:19.xfr_d16_20.do_shot
# canhw:19.xfr_d16_20.was_start
# canhw:19.xfr_d16_20.ones_stop
# canhw:19.ic.extractor.clockSrc
clock_names = {
    "off":    0,
    "vepp2k": 1,
    "vepp3":  2,
    "test":   3,
}


class Extractor:
    extractionDone = cda.Signal()
    unexpectedShot = cda.Signal()
    trainingShot = cda.Signal()
    trainingStopped = cda.Signal()

    def __init__(self):
        super().__init__()
        self.extract_request = False
        self.training_shots = False
        self.training_interval = 3

        self.clock_src = 0

        self.c_clock_src = cda.IChan("canhw:19.ic.extractor.clockSrc", on_update=True)
        self.c_do_shot = cda.IChan("canhw:19.xfr_d16_20.do_shot",  on_update=True)
        self.c_was_shot = cda.IChan("canhw:19.xfr_d16_20.was_start",  on_update=True)
        self.c_stop = cda.IChan("canhw:19.xfr_d16_20.ones_stop",  on_update=True)

        self.c_was_shot.valueMeasured.connect(self.was_shot_proc)
        self.c_clock_src.valueChanged.connect(self.clock_src_update)

        self.timer = cda.Timer()

    def was_shot_proc(self, chan):
        if chan.val == 0:
            return
        if self.extract_request:
            self.extract_request = False
            self.extractionDone.emit()
            return
        if self.training_shots:
            self.timer.singleShot(self.training_interval * 1000, self.do_shot)
            self.trainingShot.emit()
            return
        self.unexpectedShot.emit()

    def set_clock_src(self, clk_name):
        value = clock_names.get(clk_name, 0)
        self.c_clock_src.setValue(value)

    def clock_src_update(self, chan):
        self.clock_src = chan.val

    def do_shot(self):
        self.c_do_shot.setValue(1)

    def extract(self):
        if self.extract_request:
            return
        self.stop_training()
        self.extract_request = True
        self.do_shot()

    def start_training(self):
        if self.training_shots:
            return
        self.stop_extraction()
        self.training_shots = True
        self.do_shot()

    def set_training_interval(self, delay_s):
        self.training_interval = delay_s

    def stop(self):
        self.stop_extraction()
        self.stop_training()

    def stop_extraction(self):
        if self.extract_request:
            self.extract_request = False
            self.c_stop.setValue(1)

    def stop_training(self):
        if self.training_shots:
            self.training_shots = False
            self.timer.stop()
            self.c_stop.setValue(1)
            self.trainingStopped.emit()
