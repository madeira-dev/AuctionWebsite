import socket
from auctionmessage import AuctionMessage
from auctioncomm import AuctionComm
from auctionprotocol import AuctionProtocol
from user import User
from auction import Auction
from item import Item


def main():
    commsoc = socket.socket()

    commsoc.connect(("174.129.99.121", 50000)) # this is the public IP address of the MWserver

    comm = AuctionComm(commsoc)
    protocol = AuctionProtocol(comm)
    message = AuctionMessage()
    response = AuctionMessage()

    user = User(None, None)

    print("""1. Login
99. Exit""")
    firstOption = input(">")

    if firstOption == "1":
        username = input("Enter username: ")
        password = input("Enter password: ")

        user.login(username, password)

        # Send LGIN message
        login_data = f'{user.username};{user.password}'.encode()
        message.setType('LGIN')
        message.setData(login_data)

        # Receive response from server
        response = protocol.sendRequest(message)
        user_id = response.getData().decode()
        user.set_user_id(user_id)
        print(f"User {user.username} logged in")
    else:
        commsoc.close()
        return

    # After login, accept other commands
    while True:
        print("""1. List Auctions
2. List Bids
3. Make an Auction
4. Place a Bid
5. Search for an Auction
98. Logout
99. Exit""")
        option = input(">")

        if option == "98" or option == "99":
            # probably don't need to set a data since it's just a logout?
            message.setType('LOUT')
            response = protocol.sendRequest(message)
            print(response.getData().decode())
            break

        elif option == "1":
            message.setType('LSAL')
            response = protocol.sendRequest(message)

            print("\n")
            if response.getType() == 'GOOD':
                print(response.getData().decode())
            else:
                print("Error fetching auctions.")

        elif option == "2":
            message.setType('LBID')
            message.setData(user.user_id.encode())
            response = protocol.sendRequest(message)

            print("\n")
            if response.getType() == 'GOOD':
                print("\nBids placed by you:")
                print(response.getData().decode())
            else:
                print("No bids found.\n")

        elif option == "4":
            message.setType('MBID')

            userInput = input("\nEnter auction product name:")
            price = input("Enter bid price:")

            newBidData = f'{user.user_id};{userInput};{price}'.encode()

            message.setData(newBidData)
            response = protocol.sendRequest(message)

            print("\n")
            print({response.getData().decode()})

        elif option == "3":
            # message type
            message.setType('MAUC')

            # create item to add to auction
            print("\nTo create an auction, first you need to add an item.")
            item_name = input("Enter item name:")
            item_description = input("Enter item description:")
            item_price = input("Enter item price:")
            item = Item(item_name, item_description,
                        user.user_id, item_price)

            # create auction
            print("\nNow enter the auction details.")
            ttl = input("Enter the auction ttl in seconds:")
            new_auction = Auction(user.user_id, ttl, item.price, item.name, item.description )

            # format auction data
            newAuctionData = f'{new_auction.owner_id};{new_auction.ttl};{new_auction.starting_price};{
                new_auction.item};{new_auction.item_description}'.encode()

            # set data message and send request to middleware server
            message.setData(newAuctionData)
            response = protocol.sendRequest(message)

            print("\n")
            if response.getType() == 'GOOD':
                print("Auction created successfully.")
            else:
                print("Auction creation failed.")

        elif option == "5":
            message.setType('SAUC')
            userInput = input("Enter product name:")
            message.setData(userInput.encode())
            response = protocol.sendRequest(message)

            print("\n")
            if response.getType() == 'GOOD':
                print("\nAuctions found:\n")
                print(response.getData().decode())

        else:
            message.setType('ERRO')
            response = protocol.sendRequest(message)
            print("Response received from server:", response.marshal())

    commsoc.close()


if __name__ == '__main__':
    main()
