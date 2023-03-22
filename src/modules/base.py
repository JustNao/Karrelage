from src.sniffer import protocol


class DofusModule:
    def handle_packet(self, msg):
        packet = None
        try:
            name = protocol.msg_from_id[msg.id]["name"]
        except KeyError:
            print("Unknown packet id:", msg.id)
            return
        except AttributeError:
            # msg is not a Msg object
            packet = msg
            name = msg['__type__']
        handle = f"handle_{name}"
        if hasattr(self, handle) and callable(handler := getattr(self, handle)):
            if packet is None:
                packet = protocol.readMsg(msg)

            if packet is None:
                return

            handler(packet)
