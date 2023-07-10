import logging
import zlib

from .binrw import Data, Buffer
from ..sniffer import protocol
from colorama import Fore

logger = logging.getLogger("labot")


class Msg:
    def __init__(self, m_id, data, count=None):
        self.id = m_id
        if isinstance(data, bytearray):
            data = Data(data)
        self.data = data
        self.count = count
        # logger.debug("Initialized Msg with id {}".format(self.id))

    def __str__(self):
        ans = str.format(
            "{}(m_id={}, data={}, count={})",
            self.__class__.__name__,
            self.id,
            self.data.data,
            self.count,
        )
        return ans

    def __repr__(self):
        ans = str.format(
            "{}(m_id={}, data={!r}, count={})",
            self.__class__.__name__,
            self.id,
            self.data.data,
            self.count,
        )
        return ans

    @staticmethod
    def fromRaw(buf: Buffer, from_client):
        """Read a message from the buffer and
        empty the beginning of the buffer.
        """
        id = 0
        lenData = 0
        if not buf:
            return
        try:
            header = buf.readUnsignedShort()
            if from_client:
                count = buf.readUnsignedInt()
            else:
                count = None
            lenData = int.from_bytes(buf.read(header & 3), "big")
            id = header >> 2
            try:
                if id != 2:
                    protocol.msg_from_id[id]
            except KeyError:
                # print(Fore.RED + "Flushing buffer" + Fore.RESET)
                buf.pos = len(buf)
                buf.end()
                return None
            data = Data(buf.read(lenData))
        except IndexError as e:
            if e.args[1] == 0 or e.args[1] > 20000:
                buf.pos = len(buf)
            else:
                buf.pos = 0
            logger.debug("Multi packet message with id", id)
            return None
        else:
            if id == 2:
                logger.debug("Message is NetworkDataContainerMessage! Uncompressing...")
                try:
                    newbuffer = Buffer(data.readByteArray())
                except IndexError:
                    return None
                try:
                    newbuffer.uncompress()
                except zlib.error:
                    return None
                msg = Msg.fromRaw(newbuffer, from_client)
                assert msg is not None and not newbuffer.remaining()
                return msg
            buf.end()

            return Msg(id, data, count)

    def lenlenData(self):
        if len(self.data) > 65535:
            return 3
        if len(self.data) > 255:
            return 2
        if len(self.data) > 0:
            return 1
        return 0

    def bytes(self):
        header = 4 * self.id + self.lenlenData()
        ans = Data()
        ans.writeUnsignedShort(header)
        if self.count is not None:
            ans.writeUnsignedInt(self.count)
        ans += len(self.data).to_bytes(self.lenlenData(), "big")
        ans += self.data
        return ans.data

    @property
    def msgType(self):
        return protocol.msg_from_id[self.id]

    def json(self):
        logger.debug("Getting json representation of message %s", self)
        if not hasattr(self, "parsed"):
            self.parsed = protocol.read(self.msgType, self.data)
        return self.parsed

    @staticmethod
    def from_json(json, count=None, random_hash=True):
        type_name: str = json["__type__"]
        type_id: int = protocol.types[type_name]["protocolId"]
        data = protocol.write(type_name, json, random_hash=random_hash)
        return Msg(type_id, data, count)
