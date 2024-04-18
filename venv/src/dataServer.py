import os
import socket
import threading
from auctioncomm import AuctionComm
from auctionmessage import AuctionMessage
from auctionprotocol import AuctionProtocol
from user import User
from auction import Auction
import sqlite3
import signal


def databaseSetup(cursor):
    # the users table should only have the ID of the auctions they own in the auctions field, separated by a comma
    # same for the auctions table and their bids field
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS users (userID INTEGER PRIMARY KEY, username TEXT, password TEXT, auctions TEXT, bids TEXT)"""
    )

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS auctions (auctionID INTEGER PRIMARY KEY, ownerID INTEGER, ttl INTEGER, startingPrice REAL, item TEXT, itemDescription TEXT, bids TEXT, highestBid REAL)"""
    )

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS bids (bidID INTEGER PRIMARY KEY, ownerID INTEGER, auctionID INTEGER, price REAL)"""
    )

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS finishedAuctions (auctionID INTEGER, itemName TEXT, winner TEXT, valuePaid REAL)"""
    )

    # commit the changes
    conn.commit()


def signal_handler(signum, frame):
    if signum == signal.SIGUSR1:
        print("inside signal handler")
        print("auction ttl ended")


def baseTCPProtocolS(csoc, dbCursor, conn):
    print("Started baseTCPProtocol")
    loggedInUser = None

    # connect to middleware server
    comm = AuctionComm(csoc)
    protocol = AuctionProtocol(comm)
    received_request = AuctionMessage()

    while True:  # Keep listening for messages
        received_request = protocol.getRequest()
        message_type = received_request.getType()

        if message_type == "LGIN":
            print("login request")
            lgin_response_message = AuctionMessage()

            loginRequestData = received_request.getData().decode()
            splitLoginRequest = loginRequestData.split(";")

            username = splitLoginRequest[0]
            password = splitLoginRequest[1]
            loggedInUser = User(username, password)

            # check if user exists in database
            userExists = loggedInUser.checkUserExists(loggedInUser, dbCursor)

            if userExists:
                userID = loggedInUser.getUserID(loggedInUser, dbCursor)
                loggedInUser.set_user_id(userID)
                lgin_response_message.setType("GOOD")
                lgin_response_message.setData(f"{userID}".encode())
            else:
                # create user
                lastId = loggedInUser.checkLastId(dbCursor)
                newUserID = int(lastId) + 1
                loggedInUser.set_user_id(newUserID)
                loggedInUser.createUser(loggedInUser, dbCursor)
                lgin_response_message.setType("GOOD")
                lgin_response_message.setData(f"{newUserID}".encode())

            conn.commit()
            protocol.putResponse(lgin_response_message)

        elif message_type == "LOUT":
            print("logout request")
            lout_response_message = AuctionMessage()

            lout_response_message.setType("GOOD")
            lout_response_message.setData(b"User logged out")

            protocol.putResponse(lout_response_message)
            break

        elif message_type == "LSAL":
            print("list sales request")
            lsal_response_message = AuctionMessage()

            # get sales from storage
            sales = Auction.getSales(dbCursor)

            if sales == "":
                lsal_response_message.setType("ERRO")
                lsal_response_message.setData(b"No sales found")
            else:
                lsal_response_message.setType("GOOD")
                lsal_response_message.setData(sales.encode())

            conn.commit()
            protocol.putResponse(lsal_response_message)

        elif message_type == "LBID":
            print("list bids request")
            lbid_response_message = AuctionMessage()
            userID = received_request.getData().decode()

            # get bids from storage
            bids = Auction.getBids(userID, dbCursor)

            if bids == "":
                lbid_response_message.setType("ERRO")
                lbid_response_message.setData(b"No bids found")
            else:
                lbid_response_message.setType("GOOD")
                lbid_response_message.setData(bids.encode())

            conn.commit()
            protocol.putResponse(lbid_response_message)

        elif message_type == "MBID":
            print("place bid request")
            mbid_response_message = AuctionMessage()

            mbidRequestData = received_request.getData().decode()
            splitMbidRequest = mbidRequestData.split(";")

            userID = splitMbidRequest[0]
            auctionItemName = splitMbidRequest[1]
            price = splitMbidRequest[2]

            if int(price) > 0:
                # update data storage with new bid
                bidPlaced = Auction.placeBid(userID, auctionItemName, price, dbCursor)
            else:
                bidPlaced = False

            if bidPlaced:
                mbid_response_message.setType("GOOD")
                # Auction.decreaseBidCount(auctionItemName)
                # isAuctionOver = Auction.checkBidCount(auctionItemName)

                # if isAuctionOver:
                #     highestBid = Auction.getHighestBid(auctionItemName)
                #     winnerID = Auction.getAuctionWinner(auctionItemName, highestBid)
                #     winnerName = loggedInUser.getUserByID(winnerID)
                #     Auction.deleteAuction(auctionItemName)
                #     Auction.deleteBids(auctionItemName, winnerName)

                #     mbid_response_message.setData(
                #         f"Auction is Over.\nWinner is: {winnerName}".encode()
                #     )
                # else:
                #     mbid_response_message.setData(b"Bid placed successfully")
            else:
                mbid_response_message.setType("ERRO")
                mbid_response_message.setData(b"Bid placement failed")

            conn.commit()
            protocol.putResponse(mbid_response_message)

        elif message_type == "MAUC":
            print("make auction request")
            mauc_response_message = AuctionMessage()

            maucRequestData = received_request.getData().decode()
            splitMaucRequest = maucRequestData.split(";")

            newAuction = Auction(
                splitMaucRequest[0],  # ownerID
                splitMaucRequest[1],  # ttl
                splitMaucRequest[2],  # startingPrice
                splitMaucRequest[3],  # item
                splitMaucRequest[4],  # itemDescription
            )

            # update data storage with new auction
            isAuctionCreated = newAuction.createAuction(newAuction, dbCursor)

            if isAuctionCreated:
                mauc_response_message.setType("GOOD")
            else:
                mauc_response_message.setType("ERRO")

            conn.commit()

            # get the auctionID of the newly created auction
            auctionID = Auction.getAuctionID(newAuction.item, dbCursor)
            pid = os.getpid()

            # create new thread to count down the auction ttl
            auction_thread = threading.Thread(
                target=Auction.count_ttl,
                args=(auctionID, pid),
            )
            auction_thread.start()

            protocol.putResponse(mauc_response_message)

        elif message_type == "SAUC":
            print("search auction request")
            sauc_response_message = AuctionMessage()

            searchItem = received_request.getData().decode()
            auctions = Auction.searchAuction(searchItem, dbCursor)

            if auctions == "":
                sauc_response_message.setType("ERRO")
                sauc_response_message.setData(b"No auctions found")
            else:
                sauc_response_message.setType("GOOD")
                sauc_response_message.setData(auctions.encode())

            conn.commit()
            protocol.putResponse(sauc_response_message)

        else:
            error_response_message = AuctionMessage()
            error_response_message.setType("ERRO")
            error_response_message.setData(b"Unknown message type")
            print("Unknown message type")

            protocol.putResponse(error_response_message)

    print("Ended baseTCPProtocol")


def handle_client(commsoc):
    try:
        conn = sqlite3.connect("user_data.db")
        userDataCursor = conn.cursor()
        baseTCPProtocolS(commsoc, userDataCursor, conn)
    finally:
        commsoc.close()


if __name__ == "__main__":
    # database connection and setup
    signal.signal(signal.SIGUSR1, signal_handler)
    conn = sqlite3.connect("user_data.db")
    userDataCursor = conn.cursor()
    databaseSetup(userDataCursor)
    conn.close()

    # create the server socket
    # defaults family=AF_INET, type=SOCK_STREAM, proto=0, filno=None
    serversoc = socket.socket()

    # bind to local host:55000
    serversoc.bind(("localhost", 55000))

    # make passive with backlog=5
    serversoc.listen(5)
    print("Server is listening on port 55000")

    # wait for incoming connections
    try:
        while True:
            print("Waiting for a connection")
            # accept the connection
            commsoc, raddr = serversoc.accept()
            print(f"Connection established with {raddr}")

            client_thread = threading.Thread(target=handle_client, args=(commsoc,))
            client_thread.start()
    finally:
        # close the server socket
        serversoc.close()
