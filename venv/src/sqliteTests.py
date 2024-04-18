import sqlite3

# Create a connection to the database
conn = sqlite3.connect("example.db")

# Create a cursor object
c = conn.cursor()

# create a users table with id, name, password and a list of auctions
c.execute(
    """CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, password TEXT, auctions TEXT)"""
)

# create a auctions table with id, owner, list of bids, max bids, starting price, item and item description

c.execute(
    """CREATE TABLE IF NOT EXISTS auctions (id INTEGER PRIMARY KEY, owner INTEGER, bids TEXT, max_bids INTEGER, starting_price REAL, item TEXT, item_description TEXT)"""
)

# add a user to the users table
c.execute(
    """INSERT INTO users (name, password, auctions) VALUES ('user1', 'password1', '[]')"""
)

# add a new acution to the created user
c.execute(
    """INSERT INTO auctions (owner, bids, max_bids, starting_price, item, item_description) VALUES (1, '[]', 3, 10.0, 'item1', 'item1 description')"""
)

# add an auction to the user's list of auctions
c.execute("""UPDATE users SET auctions = '1' WHERE id = 1""")

# add another auction to the same user's list of auctions
c.execute("""UPDATE users SET auctions = auctions || '&new_auc' WHERE id = 1""")

conn.commit()
conn.close()
