# helper classes to create


class State:
    def __init__(self, name='', msg=''):
        self.name = name
        self.msg = msg

    def run(self):
        pass


class Transition:
    def __init__(self, src, target):
        self.src = src
        self.target = target


class Machine:
    def __init__(self):
        self.active_state = None
        self.states = {}
        self.transitions = {}

    def add_state(self, state):
        self.states[state.name] = state
        self.transitions[state.name] = []

    def add_transition(self, trn):
        self.transitions[trn.src.name].append(trn)




