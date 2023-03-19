from src.sniffer import protocol
from src.data.msg import Msg
import functools


def packet_handler(func):
    """Decorator to handle packets in modules"""

    @functools.wraps(func)
    def packet_wrapper(module, msg):
        packet = protocol.readMsg(msg)
        if packet is None:
            return

        func(module, packet)

    return packet_wrapper
