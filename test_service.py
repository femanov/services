#!/usr/bin/env python3
import pycx4.pycda as cda
from cservice import CXService


class teste_srv(CXService):
    def main(self):
        print('I am started')


# this runs service
ser = teste_srv('test', redef_print=True)



