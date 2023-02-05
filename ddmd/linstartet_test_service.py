#!/usr/bin/env python3
from cservice import CXService
from linstarter import LinStarter


class LinStarterService(CXService):
    def main(self):
        self.sl = LinStarter()


s = LinStarterService('linstarter', not_daemonize=True)
