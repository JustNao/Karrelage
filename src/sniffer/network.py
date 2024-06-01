#!/usr/bin/env python3


import os
import sys

# Necessary on macOS if the folder of libdnet is not in
# ctypes.macholib.dyld.DEFAULT_LIBRARY_FALLBACK
# because the newer macOS do not allow to export
# $DYLD_FALLBACK_LIBRARY_PATH with sudo
if os.name == "posix" and sys.platform == "darwin":
    import ctypes.macholib.dyld

    ctypes.macholib.dyld.DEFAULT_LIBRARY_FALLBACK.insert(0, "/opt/local/lib")

import socket
import threading
from select import select
import errno

from scapy import plist
from scapy.all import Raw, PcapReader, conf, sniff
from scapy.data import ETH_P_ALL, MTU
from scapy.consts import WINDOWS
from scapy.layers.inet import IP
import logging


from ..data import Buffer, Msg

logger = logging.getLogger("labot")
    
def raw(pa):
    """Raw data from a packet
    """
    return pa.getlayer(Raw).load


def get_local_ip():
    """from https://stackoverflow.com/a/28950776/5133167
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


LOCAL_IP = get_local_ip()


def from_client(pa):
    logger.debug("Determining packet origin...")
    dst = pa.getlayer(IP).dst
    src = pa.getlayer(IP).src
    if src == LOCAL_IP:
        logger.debug("Packet comes from local machine")
        return True
    elif dst == LOCAL_IP:
        logger.debug("Packet comes from server")
        return False
    logger.error(
        "Packet origin unknown\nsrc: %s\ndst: %s\nLOCAL_IP: %s", src, dst, LOCAL_IP
    )
    assert False, "Packet origin unknown"


buf1 = Buffer()
buf2 = Buffer()


def on_receive(pa, action):
    """Adds pa to the relevant buffer
    Parse the messages from that buffer
    Calls action on that buffer
    """
    logger.debug("Received packet. ")
    direction = from_client(pa)
    buf = buf1 if direction else buf2
    buf += raw(pa)
    msg = Msg.fromRaw(buf, direction)
    if msg is None:
        buf.end()
    while msg:
        action(msg)
        msg = Msg.fromRaw(buf, direction)

def launch_in_thread(action, capture_file=None):
    """Sniff in a new thread
    When a packet is received, calls action
    Returns a stop function
    """
    global stop
    logger.debug("Launching sniffer in thread...")

    def _sniff(stop_event):
        stop_filter = lambda _: stop_event.is_set()
        if capture_file:
            sniff(
                filter="tcp port 5555",
                lfilter=lambda p: p.haslayer(Raw),
                prn=lambda p: on_receive(p, action),
                stop_filter=stop_filter,
                # iface="Ethernet", # Ethernet, Ethernet 2, Wi-Fi, Wi-Fi 2, etc ...
                offline=capture_file,
            )
        else:
            sniff(
                filter="tcp port 5555",
                lfilter=lambda p: p.haslayer(Raw),
                stop_filter=stop_filter,
                prn=lambda p: on_receive(p, action),
                # iface="Ethernet", # Ethernet, Ethernet 2, Wi-Fi, Wi-Fi 2, etc ...
            )
        logger.info("sniffing stopped")

    e = threading.Event()
    t = threading.Thread(target=_sniff, args=(e,), name = "Sniffer")
    t.start()

    def stop():
        flush_buffers()
        e.set()
        print("Sniffer stopped")

    logger.debug("Started sniffer in new thread")

    return stop


def on_msg(msg):
    global m
    m = msg
    from pprint import pprint

    pprint(msg.json()["__type__"])
    print(msg.data)
    print(Msg.from_json(msg.json()).data)

def flush_buffers():
    buf1.end()
    buf2.end()

if __name__ == "__main__":
    stop = launch_in_thread(on_msg)
