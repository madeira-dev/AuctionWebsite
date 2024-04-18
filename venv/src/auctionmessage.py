from enum import Enum


class AuctionMessage(object):
    # Constants
    CMDS = Enum(
        "MCMDS",
        {
            "LGIN": "LGIN",  # login
            "LOUT": "LOUT",  # logout
            "POST": "POST",
            "GETM": "GETM",
            "LSAL": "LSAL",  # list auction
            "LBID": "LBID",  # list auctions and bids
            "MBID": "MBID",  # make bid
            "MAUC": "MAUC",  # make auction
            "SAUC": "SAUC",  # search for an auction
            "GOOD": "GOOD",  # success return
            "ERRO": "ERRO",  # failure return
        },
    )

    def __init__(self):
        """
        Constructor
        """
        self._cmd = AuctionMessage.CMDS["GOOD"]
        self._data = bytes()  # bytearray mutable array, bytes() == b'' is immutable

    def reset(self):
        self._cmd = AuctionMessage.CMDS["GOOD"]
        self._data = bytes()

    def setType(self, mtype: str):
        self._cmd = AuctionMessage.CMDS[mtype]

    def getType(self) -> str:
        return self._cmd.value

    def setData(self, d: bytes):
        self._data = d

    def getData(self) -> bytes:
        return self._data

    def marshal(self) -> str:
        size = len(self._data) + 4
        header = "{:04}{}".format(size, self._cmd.value)
        return b"".join([header.encode("utf-8"), self._data])

    def unmarshal(self, value: bytes):
        self.reset()
        if value:
            index = value[0:4].decode("utf-8")
            self._cmd = AuctionMessage.CMDS[index]
            self._data = value[4:]
