import time
from src.modules.base import DofusModule
from src.sniffer import protocol

class Debug(DofusModule):
    """Debug & dev module"""

    def __init__(self):
        self.packets = []

    def handle_packet(self, msg):
        """Supercharging the handle_packet method from parent class to save every packet"""

        packet = protocol.readMsg(msg)
        if packet:
            timestamp = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime()
            )
            self.packets.append({"timestamp": timestamp, "packet": packet, "size": len(msg.data)})

    def get_data(self):
        packets = self.packets
        self.clear_packets()
        return {
            "packets": packets
        }

    def clear_packets(self):
        self.packets = []