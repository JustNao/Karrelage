from . import network, protocol
def packetRead(msg):
    try:
        print(protocol.read(protocol.msg_from_id[msg.id]['name'], msg.data))
    except KeyError:
        print("KeyError : ", msg.id)

network.launch_in_thread(packetRead)