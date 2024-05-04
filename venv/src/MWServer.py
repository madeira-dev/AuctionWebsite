"""
    this is the middleware server so it should work as a server for the user (client)
    and as a client for the data storage server
"""

import socket
import threading
from auctioncomm import AuctionComm
from auctionmessage import AuctionMessage
from auctionprotocol import AuctionProtocol
import sqlite3


def loopRecv(csoc, size):
    data = bytearray(b" " * size)
    mv = memoryview(data)
    while size:
        rsize = csoc.recv_into(mv, size)
        mv = mv[rsize:]
        size -= rsize
    return data


def baseTCPProtocolS(csoc):
    print("Started baseTCPProtocol")

    comm = AuctionComm(csoc)
    protocol = AuctionProtocol(comm)
    client_received_request = AuctionMessage()

    # connect to data storage server
    dataCommSoc = socket.socket()
    dataCommSoc.connect(("172.31.86.142", 55000))
    dataComm = AuctionComm(dataCommSoc)
    dataProtocol = AuctionProtocol(dataComm)

    while True:  # Keep listening for messages
        client_received_request = protocol.getRequest()
        client_message_type = client_received_request.getType()

        if client_message_type == "LGIN":
            print("Login Request")
            dataLoginMessage = AuctionMessage()
            dataLoginResponseMessage = AuctionMessage()
            lgin_response_message = AuctionMessage()

            # send request to data storage server
            dataLoginMessage.setType("LGIN")
            dataLoginMessage.setData(client_received_request.getData())
            dataLoginResponseMessage = dataProtocol.sendRequest(dataLoginMessage)

            # set response information according to data storage server response
            lgin_response_message.setType("GOOD")
            lgin_response_message.setData(dataLoginResponseMessage.getData())

            # send response to client
            protocol.putResponse(lgin_response_message)

        elif client_message_type == "LOUT":
            print("Logout Request")
            dataLoutMessage = AuctionMessage()
            dataLoutResponseMessage = AuctionMessage()
            lout_response_message = AuctionMessage()

            # send request to data storage server
            dataLoutMessage.setType("LOUT")
            dataLoutMessage.setData(client_received_request.getData())
            dataLoutResponseMessage = dataProtocol.sendRequest(dataLoutMessage)

            # set response information according to data storage server response
            lout_response_message.setType("GOOD")

            lout_response_message.setData(b"User logged out")
            print("User logged out")

            protocol.putResponse(lout_response_message)
            break

        elif client_message_type == "LSAL":
            print("List Auctions Request")
            """
            send request to data storage server to get sales
            """
            dataLsalMessage = AuctionMessage()
            dataLsalResponseMessage = AuctionMessage()
            lsalResponseMessage = AuctionMessage()

            # send request to data storage server
            dataLsalMessage.setType("LSAL")
            dataLsalMessage.setData(client_received_request.getData())
            dataLsalResponseMessage = dataProtocol.sendRequest(dataLsalMessage)

            # set response information according to data storage server response
            if dataLsalResponseMessage.getType() == "GOOD":
                lsalResponseMessage.setType("GOOD")
                lsalResponseMessage.setData(dataLsalResponseMessage.getData())
            else:
                lsalResponseMessage.setType("ERRO")

            protocol.putResponse(lsalResponseMessage)

        elif client_message_type == "LBID":
            print("List Bids Request")
            """
            send request to data storage server to get bids list
            """
            dataLbidMessage = AuctionMessage()
            dataLbidResponseMessage = AuctionMessage()
            lbidResponseMessage = AuctionMessage()

            # send request to data storage server
            dataLbidMessage.setType("LBID")
            dataLbidMessage.setData(client_received_request.getData())
            dataLbidResponseMessage = dataProtocol.sendRequest(dataLbidMessage)

            # set response information according to data storage server response
            if dataLbidResponseMessage.getType() == "GOOD":
                lbidResponseMessage.setType("GOOD")
                lbidResponseMessage.setData(dataLbidResponseMessage.getData())
            else:
                lbidResponseMessage.setType("ERRO")

            protocol.putResponse(lbidResponseMessage)

        elif client_message_type == "MBID":
            print("Place Bid Request")
            dataMbidMessage = AuctionMessage()
            dataMbidResponseMessage = AuctionMessage()
            mbidResponseMessage = AuctionMessage()

            # send request to data storage server
            dataMbidMessage.setType("MBID")
            dataMbidMessage.setData(client_received_request.getData())
            dataMbidResponseMessage = dataProtocol.sendRequest(dataMbidMessage)

            # set response information according to data storage server response
            if dataMbidResponseMessage.getType() == "GOOD":
                mbidResponseMessage.setType("GOOD")
                mbidResponseMessage.setData(dataMbidResponseMessage.getData())
            else:
                mbidResponseMessage.setType("ERRO")
                mbidResponseMessage.setData(dataMbidResponseMessage.getData())

            protocol.putResponse(mbidResponseMessage)

        elif client_message_type == "MAUC":
            print("Make Auction Request")
            dataMaucMessage = AuctionMessage()
            dataMaucResponseMessage = AuctionMessage()
            maucResponseMessage = AuctionMessage()

            # send request to data storage server
            dataMaucMessage.setType("MAUC")
            dataMaucMessage.setData(client_received_request.getData())
            dataMaucResponseMessage = dataProtocol.sendRequest(dataMaucMessage)

            if dataMaucResponseMessage.getType() == "GOOD":
                maucResponseMessage.setType("GOOD")
            else:
                maucResponseMessage.setType("ERRO")

            protocol.putResponse(maucResponseMessage)

        elif client_message_type == "SAUC":
            print("Search Auction Request")
            dataSaucMessage = AuctionMessage()
            dataSaucResponseMessage = AuctionMessage()
            saucResponseMessage = AuctionMessage()

            # send request to data storage server
            dataSaucMessage.setType("SAUC")
            dataSaucMessage.setData(client_received_request.getData())
            dataSaucResponseMessage = dataProtocol.sendRequest(dataSaucMessage)

            if dataSaucResponseMessage.getType() == "GOOD":
                saucResponseMessage.setType("GOOD")
                saucResponseMessage.setData(dataSaucResponseMessage.getData())
            else:
                saucResponseMessage.setType("ERRO")

            protocol.putResponse(saucResponseMessage)

        else:
            error_response_message = AuctionMessage()
            error_response_message.setType("ERRO")
            error_response_message.setData(b"Unknown message type")
            print("Unknown message type")

            protocol.putResponse(error_response_message)

    print("Ended baseTCPProtocol")


def handle_client(commsoc):
    try:
        baseTCPProtocolS(commsoc)
    finally:
        commsoc.close()


if __name__ == "__main__":
    # create the server socket
    # defaults family=AF_INET, type=SOCK_STREAM, proto=0, filno=None
    serversoc = socket.socket()

    # bind to local host:50000
    serversoc.bind(("172.31.86.142", 50000))

    # make passive with backlog=5
    serversoc.listen(5)

    print("Listening on", 50000)

    # wait for incoming connections
    try:
        while True:
            print("Waiting for a connection")
            # accept the connection
            commsoc, raddr = serversoc.accept()
            print(f"Connection established with {raddr}")

            # Create new thread for each client
            client_thread = threading.Thread(target=handle_client, args=(commsoc,))
            client_thread.start()

    finally:
        # close the server socket
        serversoc.close()
