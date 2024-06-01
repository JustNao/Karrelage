from src.sniffer import protocol, network


class DofusModule:
    def handle_packet(self, msg):
        packet = protocol.readMsg(msg)
        if packet is None:
            # Something broke which will fuck up all subsequent packet reading
            # need to flush the buffers
            print("Broken buffers, flushing")
            network.flush_buffers()
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
