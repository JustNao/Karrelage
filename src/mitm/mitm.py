#!/usr/bin/env python3

import sys
from pathlib import Path
import psutil

# include path to labot
sys.path.append(Path(__file__).absolute().parents[1].as_posix())

from .bridge import *

from fritm import hook, start_proxy_server

FILTER = "port == 5555 || port == 443"


bridges = []


def launch_mitm(packet_read, pid=None):
    global bridges

    PORT = 8080
    PID = None

    def my_callback(coJeu, coSer):
        global bridges
        bridge = KarrelageBridgeHandler(coJeu, coSer, packet_read)
        bridges.append(bridge)
        bridge.loop()

    # to interrupt : httpd.shutdown()
    httpd = start_proxy_server(my_callback, PORT)

    target = PID
    if target is None:
        for proc in psutil.process_iter():
            if "Dofus.exe" in proc.name():
                target = proc.pid
                break

    hook(target, PORT, FILTER)

    return httpd, bridges


if __name__ == "__main__":
    launch_mitm()
    if not sys.flags.interactive:
        sys.stdin.read()  # infinite loop
