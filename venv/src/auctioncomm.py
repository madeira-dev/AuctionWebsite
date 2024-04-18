import socket
from auctionmessage import AuctionMessage


class AuctionComm(object):
    BUFFSIZE = 8196

    def __init__(self, s: socket = -1):
        self._sock = s

    def _loopRecv(self, size: int):
        data = bytearray(b" " * size)
        mv = memoryview(data)
        while size:
            rsize = self._sock.recv_into(mv, size)
            mv = mv[rsize:]
            size -= rsize
        return data

    def sendMessage(self, m: AuctionMessage):
        data = m.marshal()
        self._sock.sendall(data)

    def recvMessage(self) -> AuctionMessage:
        try:
            m = AuctionMessage()

            # pass the size of message in dict? so if passing the size of greater message should cover all of them
            size = self._loopRecv(4)
            print(size)
            data = self._loopRecv(int(size.decode("utf-8")))
            m.unmarshal(data)
        except Exception:
            raise Exception("bad getMessage")
        else:
            return m

    def close(self):
        self._sock.close()
