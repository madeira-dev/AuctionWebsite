import sqlite3

# Create a connection to the database
conn = sqlite3.connect("example.db")

# Create a cursor object
c = conn.cursor()

# make a query
c.execute("""SELECT * FROM stocks""")

# Fetch the results
results = c.fetchall()
print(results)

# Close the connection
conn.close()
