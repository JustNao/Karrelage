#!/usr/bin/env python3

import sys
import os
import argparse
from pathlib import Path
from subprocess import Popen

# include path to labot
sys.path.append(Path(__file__).absolute().parents[1].as_posix())

from bridge import *

from fritm import hook, start_proxy_server

FILTER = "port == 5555 || port == 443"


def launch_mitm(pid=None):
    bridges = []
    PORT = 8080
    PID = None

    def my_callback(coJeu, coSer):
        global bridges
        bridge = PrintingMsgBridgeHandler(coJeu, coSer)
        bridges.append(bridge)
        bridge.loop()

    # to interrupt : httpd.shutdown()
    httpd = start_proxy_server(my_callback, PORT)

    target = PID
    target = "Dofus.exe"

    hook(target, PORT, FILTER)

    if not sys.flags.interactive:
        sys.stdin.read()  # infinite loop


if __name__ == "__main__":
    launch_mitm()
