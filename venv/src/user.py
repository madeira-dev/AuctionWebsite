class User:

    user_id = None

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def checkLastId(self, dbCursor):
        dbCursor.execute("SELECT MAX(userID) FROM users")
        lastId = dbCursor.fetchone()[0]
        if lastId:
            return lastId
        else:
            return 0

    def checkUserExists(self, user, dbCursor):
        dbCursor.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (user.username, user.password),
        )
        userExists = dbCursor.fetchone()

        if userExists:
            return True
        else:
            return False

    def createUser(self, user, dbCursor):
        dbCursor.execute(
            "INSERT INTO users (username, password, auctions, bids) VALUES (?, ?, ?, ?)",
            (user.username, user.password, "", ""),
        )

    def getUserID(self, user, dbCursor):
        dbCursor.execute(
            "SELECT userID FROM users WHERE username = ? AND password = ?",
            (user.username, user.password),
        )
        userID = dbCursor.fetchone()[0]
        return userID

    def getUserByID(self, userID, dbCursor):
        dbCursor.execute("SELECT username FROM users WHERE userID = ?", (userID,))

    def set_user_id(self, id):
        self.user_id = id

    def login(self, username, password):
        self.username = username
        self.password = password
