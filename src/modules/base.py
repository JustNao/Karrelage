from src.sniffer import protocol
import json
import time


class DofusModule:
    def handle_packet(self, msg):
        packet = protocol.readMsg(msg)
        if packet is None:
            return
        handle = f"handle_{packet["__type__"]}"
        if hasattr(self, handle) and callable(handler := getattr(self, handle)):
            if packet is None:
                packet = protocol.readMsg(msg)

            if packet is None:
                return
            handler(packet)

    def update(self, data):
        pass

    def get_data(self):
        return {}
