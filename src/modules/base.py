from src.utils import packet_handler
from src.sniffer import protocol


class DofusModule:
    def handle_packet(self, msg):
        try:
            name = protocol.msg_from_id[msg.id]["name"]
        except KeyError:
            print("Unknown packet id:", msg.id)

        handle = f"handle_{name}"
        if hasattr(self, handle) and callable(handler := getattr(self, handle)):
            handler(msg)
