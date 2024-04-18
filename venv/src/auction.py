import sqlite3
from time import sleep
import signal
import os


class Auction:

    def __init__(self, owner_id, ttl, starting_price, item, item_description):
        self.owner_id = owner_id
        self.ttl = ttl
        self.starting_price = starting_price
        self.item = item
        self.item_description = item_description

    def getAuctionID(itemName, dbCursor):
        print("itemName", itemName)
        # given an item name, return the auction ID
        dbCursor.execute("""SELECT * FROM auctions WHERE item = ?""", (itemName,))
        auctions = dbCursor.fetchall()
        auctionID = auctions[0][0]
        return auctionID

    def createAuction(self, auctionObj, dbCursor):
        # check if owner already has an auction with the same item name
        dbCursor.execute(
            """SELECT item FROM auctions WHERE ownerID = ? AND item = ?""",
            (auctionObj.owner_id, auctionObj.item),
        )
        # check if the item is already in the database
        # return False if the item is already in the database
        if dbCursor.fetchone() is not None:
            print("You already have an auction with the same item.")
            return False

        # add auction too auctions table
        dbCursor.execute(
            """INSERT INTO auctions (ownerID, ttl, startingPrice, item, itemDescription, bids, highestBid) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                auctionObj.owner_id,
                auctionObj.ttl,
                auctionObj.starting_price,
                auctionObj.item,
                auctionObj.item_description,
                "",
                0.0,
            ),
        )

        # get auction ID
        dbCursor.execute(
            """SELECT auctionID FROM auctions WHERE ownerID = ? AND item = ?""",
            (auctionObj.owner_id, auctionObj.item),
        )
        auctionID = dbCursor.fetchone()[0]

        formmated_auctionID = str(auctionID) + ","

        # add auction ID to user's list of auctions
        dbCursor.execute(
            """UPDATE users SET auctions = auctions || ? WHERE userID = ?""",
            (formmated_auctionID, auctionObj.owner_id),
        )

        return True

    def placeBid(bidOwnerID, auctionItemName, price, dbCursor):
        # check if the auction exists
        dbCursor.execute(
            """SELECT item FROM auctions WHERE item = ?""", (auctionItemName,)
        )
        if dbCursor.fetchone() is None or dbCursor.fetchone() == [("",)]:
            print("Auction does not exist.")
            return False

        # check if the owner is trying to bid on his own auction
        dbCursor.execute(
            """SELECT ownerID FROM auctions WHERE item = ?""", (auctionItemName,)
        )
        fetchOwnerID = dbCursor.fetchone()
        ownerID = fetchOwnerID[0]
        if ownerID == bidOwnerID:
            print("You cannot bid on your own auction.")
            return False

        auctionID = Auction.getAuctionID(auctionItemName, dbCursor)

        # add bid to bids table
        dbCursor.execute(
            """INSERT INTO bids (ownerID, auctionID, price) VALUES (?, ?, ?)""",
            (bidOwnerID, auctionID, price),
        )

        # get bid ID
        dbCursor.execute(
            """SELECT bidID FROM bids WHERE ownerID = ? AND auctionID = ?""",
            (bidOwnerID, auctionID),
        )
        bidID = dbCursor.fetchone()[0]
        print("bidID:", bidID)

        formatted_bidID = str(bidID) + ","

        # add bid ID to user's list of bids
        dbCursor.execute(
            """UPDATE users SET bids = bids || ? WHERE userID = ?""",
            (formatted_bidID, bidOwnerID),
        )

        # add bid ID to auction's list of bids
        dbCursor.execute(
            """UPDATE auctions SET bids = bids || ? WHERE item = ?""",
            (formatted_bidID, auctionItemName),
        )

        """compare bid value to decide if it is the highest one or not!!"""
        Auction.setHighestBid(auctionID, dbCursor)

        return True

    def getSales(dbCursor):
        dbCursor.execute("SELECT * FROM auctions")
        auctions = dbCursor.fetchall()
        sales = ""

        sales += "Active Auctions:\n"
        for auction in auctions:
            # get seller name from userID
            dbCursor.execute(
                """SELECT username FROM users WHERE userID = ?""", (auction[1],)
            )
            fetchSellerName = dbCursor.fetchone()
            sellerName = fetchSellerName[0]
            sales += f"Seller: {sellerName}\n"
            sales += f"Auctions:\n"
            sales += f"Item:{auction[4]} - Description:{auction[5]} - Starting Price:{auction[3]} - ttl:{auction[2]} - Highest Bid:{auction[7]}\n"

        sales += "\nFinished Auctions:\n"

        # get auctions from finishedAuctions table
        dbCursor.execute("SELECT * FROM finishedAuctions")
        finishedAuctions = dbCursor.fetchall()
        for finishedAuction in finishedAuctions:
            sales += f"Item:{finishedAuction[1]} - Winner:{finishedAuction[2]} - Value Paid:{finishedAuction[3]}\n"
        sales += "\n"

        return sales

    def setHighestBid(auctionID, dbCursor):
        dbCursor.execute("""SELECT price FROM bids WHERE auctionID = ?""", (auctionID,))
        bids = dbCursor.fetchall()
        highestBid = 0
        for bid in bids:
            if bid[0] > highestBid:
                highestBid = bid[0]

        dbCursor.execute(
            """UPDATE auctions SET highestBid = ? WHERE auctionID = ?""",
            (highestBid, auctionID),
        )

    def getHighestBidOwnerID(auctionID, dbCursor):
        dbCursor.execute(
            """SELECT highestBid FROM auctions WHERE auctionID = ?""", (auctionID,)
        )
        fetchHighestBid = dbCursor.fetchone()
        print("fetchHighestBid:", fetchHighestBid)
        highestBid = fetchHighestBid[0]

        # check if highest bid is 0.0 meaning no bids were placed
        if (
            highestBid == 0.0
            or highestBid == None
            or highestBid == ""
            or highestBid == "0.0"
        ):
            return None

        dbCursor.execute("""SELECT ownerID FROM bids WHERE price = ?""", (highestBid,))
        fetchHighestBidOwner = dbCursor.fetchone()
        print("fetchHighestBidOwner:", fetchHighestBidOwner)
        highestBidOwner = fetchHighestBidOwner[0]

        return highestBidOwner

    def getBids(userID, dbCursor):
        dbCursor.execute("""SELECT bids FROM users WHERE userID = ?""", (userID,))
        bids = dbCursor.fetchall()
        print("bids:", bids)
        # check if the user has no bids
        if bids == [("",)]:
            return "You have no bids.\n"

        bidsID = bids[0][0].split(",")
        print("bidsID:", bidsID)

        allBids = ""
        for bidID in bidsID:
            print("bidID:", bidID)
            if bidID == "" or bidID == None:
                continue
            dbCursor.execute("""SELECT auctionID FROM bids WHERE bidID = ?""", (bidID,))
            fetchAuctionID = dbCursor.fetchone()
            auctionID = fetchAuctionID[0]

            dbCursor.execute(
                """SELECT item FROM auctions WHERE auctionID = ?""", (auctionID,)
            )
            fetchItem = dbCursor.fetchone()
            item = fetchItem[0]

            dbCursor.execute("""SELECT price FROM bids WHERE bidID = ?""", (bidID,))
            fetchPrice = dbCursor.fetchone()
            price = fetchPrice[0]

            allBids += f"Item:{item} - Bid value:{price}\n"

        return allBids

    def deleteAuction(auctionItemName, dbCursor):
        # get auction ID from auction name
        dbCursor.execute(
            """SELECT auctionID FROM auctions WHERE item = ?""", (auctionItemName,)
        )
        fetchAuctionID = dbCursor.fetchone()
        auctionID = fetchAuctionID[0]

        # delete the auction from the auctions table
        dbCursor.execute("""DELETE FROM auctions WHERE auctionID = ?""", (auctionID,))

        # delete the auction from the user's list of auctions
        dbCursor.execute(
            """SELECT auctions FROM users WHERE auctions LIKE ?""", (f"%{auctionID}%",)
        )
        fetchUserAuctions = dbCursor.fetchone()

        userAuctions = fetchUserAuctions[0]
        userAuctions = userAuctions.split(",")
        userAuctions.remove(str(auctionID))
        userAuctions = ",".join(userAuctions)
        dbCursor.execute(
            """UPDATE users SET auctions = ? WHERE auctions LIKE ?""",
            (userAuctions, f"%{auctionID}%"),
        )

        return True

    def deleteBids(auctionItemName, dbCursor):
        # get auction ID from auction name
        dbCursor.execute(
            """SELECT auctionID FROM auctions WHERE item = ?""", (auctionItemName,)
        )
        fetchAuctionID = dbCursor.fetchone()
        auctionID = fetchAuctionID[0]

        # delete the bids from the bids field from the given auctionID
        dbCursor.execute(
            """UPDATE auctions SET bids = '' WHERE auctionID = ?""", (auctionID,)
        )

    def count_ttl(auctionID, mainProgramPID):
        # create new connection to the database
        dbConnection = sqlite3.connect("user_data.db")
        dbCursor = dbConnection.cursor()

        """Decrease the time to live of an auction by 1 every second until it reaches 0."""
        dbCursor.execute(
            """SELECT ttl FROM auctions WHERE auctionID = ?""", (auctionID,)
        )
        fetchTtl = dbCursor.fetchone()
        ttl = fetchTtl[0]
        while 1:
            ttl -= 1
            sleep(1)
            if ttl <= 0:
                # final update of the ttl value
                dbCursor.execute(
                    """UPDATE auctions SET ttl = ? WHERE auctionID = ?""",
                    (ttl, auctionID),
                )
                dbConnection.commit()
                # get highest bid owner
                highestBidOwnerID = Auction.getHighestBidOwnerID(auctionID, dbCursor)
                # add auction to finished auctions table
                Auction.endAuction(auctionID, highestBidOwnerID, dbCursor)
                dbConnection.commit()
                dbConnection.close()
                # send message to data server through pipe
                print("ttl reached 0.")
                os.kill(mainProgramPID, signal.SIGUSR1)
                break

    def endAuction(auctionID, highestBidOwnerID, dbCursor):
        # get auction details
        dbCursor.execute("""SELECT * FROM auctions WHERE auctionID = ?""", (auctionID,))
        auctionDetails = dbCursor.fetchone()

        if highestBidOwnerID is None:
            # add auction to finished auctions table
            dbCursor.execute(
                """INSERT INTO finishedAuctions (auctionID, itemName, winner, valuePaid) VALUES (?, ?, ?, ?)""",
                (auctionID, auctionDetails[4], "No bids placed", 0.0),
            )

            # delete auction from auctions table
            dbCursor.execute(
                """DELETE FROM auctions WHERE auctionID = ?""", (auctionID,)
            )

            # delete auction from user's list of auctions
            dbCursor.execute(
                """SELECT auctions FROM users WHERE auctions LIKE ?""",
                (f"%{auctionID}%",),
            )
            fetchUserAuctions = dbCursor.fetchone()
            userAuctions = fetchUserAuctions[0]
            userAuctions = userAuctions.split(",")
            userAuctions.remove(str(auctionID))
            userAuctions = ",".join(userAuctions)
            dbCursor.execute(
                """UPDATE users SET auctions = ? WHERE auctions LIKE ?""",
                (userAuctions, f"%{auctionID}%"),
            )

            return True

        # get name of the highest bid owner
        dbCursor.execute(
            """SELECT username FROM users WHERE userID = ?""", (highestBidOwnerID,)
        )
        fetchHighestBidOwnerName = dbCursor.fetchone()
        highestBidOwnerName = fetchHighestBidOwnerName[0]

        # add auction to finished auctions table
        dbCursor.execute(
            """INSERT INTO finishedAuctions (auctionID, itemName, winner, valuePaid) VALUES (?, ?, ?, ?)""",
            (auctionID, auctionDetails[4], highestBidOwnerName, auctionDetails[7]),
        )

        # delete auction from auctions table
        dbCursor.execute("""DELETE FROM auctions WHERE auctionID = ?""", (auctionID,))

        # delete auction from user's list of auctions
        dbCursor.execute(
            """SELECT auctions FROM users WHERE auctions LIKE ?""", (f"%{auctionID}%",)
        )
        fetchUserAuctions = dbCursor.fetchone()
        userAuctions = fetchUserAuctions[0]
        userAuctions = userAuctions.split(",")
        userAuctions.remove(str(auctionID))
        userAuctions = ",".join(userAuctions)
        dbCursor.execute(
            """UPDATE users SET auctions = ? WHERE auctions LIKE ?""",
            (userAuctions, f"%{auctionID}%"),
        )

        # delete bids from bids table
        dbCursor.execute("""DELETE FROM bids WHERE auctionID = ?""", (auctionID,))

        # delete bids from user's list of bids of every user that bid on the auction
        dbCursor.execute(
            """SELECT bids FROM users WHERE bids LIKE ?""", (f"%{auctionID}%",)
        )
        fetchUserBids = dbCursor.fetchall()
        for userBids in fetchUserBids:
            userBids = userBids[0]
            userBids = userBids.split(",")
            userBids.remove(str(auctionID))
            userBids = ",".join(userBids)
            dbCursor.execute(
                """UPDATE users SET bids = ? WHERE bids LIKE ?""",
                (userBids, f"%{auctionID}%"),
            )

        return True

    def searchAuction(userInput, dbCursor):
        dbCursor.execute(
            """SELECT * FROM auctions WHERE item LIKE ?""", (f"%{userInput}%",)
        )
        auctions = dbCursor.fetchall()

        searchResults = ""
        for auction in auctions:
            # get seller name from userID
            dbCursor.execute(
                """SELECT username FROM users WHERE userID = ?""", (auction[1],)
            )
            fetchSellerName = dbCursor.fetchone()
            sellerName = fetchSellerName[0]
            searchResults += f"Seller: {sellerName} - Item:{auction[4]} - Description:{auction[5]} - Starting Price:{auction[3]} - ttl:{auction[2]} - Highest Bid:{auction[7]}\n"

        return searchResults
