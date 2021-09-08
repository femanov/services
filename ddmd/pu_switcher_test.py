#!/usr/bin/env python3


from pu_switcher import PUSwitcher

switch = PUSwitcher()

print('current modes')
print(switch.modes)

print('switch to e2v2')
print(switch.what2switch('e2v2'))

switch.set_mode('e2v2')
print('modes after change...')
print(switch.modes)
