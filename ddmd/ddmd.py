#!/usr/bin/env python3
from cservice import CXService
from injext_looper import InjExtLoop


class DDMService(CXService):
    def main(self):
        self.injext_loop = InjExtLoop()

    def clean(self):
        self.log_str('exiting doom\`s day machine daemon')


ddmd = DDMService("ddmd")

