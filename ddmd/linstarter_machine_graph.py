#!/usr/bin/env python3
from linstarter import LinStarter, states, transitions
from transitions.extensions import GraphMachine


m = LinStarter()

machine = GraphMachine(model=m, states=states, transitions=transitions, initial='unknown')

m.get_graph().draw('my_state_diagram.png', prog='dot')
