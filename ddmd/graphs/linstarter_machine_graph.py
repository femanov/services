#!/usr/bin/env python3
from ic_modules.sm.linstarter import LinStarter, states, transitions
from transitions.extensions import GraphMachine


m = LinStarter()

machine = GraphMachine(model=m, states=states, transitions=transitions, initial='unknown')

m.get_graph().draw('linstarter_diagram.png', prog='dot')
