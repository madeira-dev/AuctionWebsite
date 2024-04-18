from auctionmessage import AuctionMessage
from auctioncomm import AuctionComm


class AuctionProtocol(object):

    def __init__(self, comm: AuctionComm = -1):
        self._auctioncomm = comm

    def close(self):
        self._auctioncomm.close()

    # server needs
    def getRequest(self) -> AuctionMessage:
        return self._auctioncomm.recvMessage()

    def putResponse(self, resp: AuctionMessage):
        self._auctioncomm.sendMessage(resp)

    # client needs
    def sendRequest(self, req: AuctionMessage) -> AuctionMessage:
        self._auctioncomm.sendMessage(req)
        resp = self._auctioncomm.recvMessage()
        return resp
