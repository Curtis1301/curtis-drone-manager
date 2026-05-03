import sqlite3

class DatabaseManager():
    '''Designated class that handles all database actions.'''
    def __init__(self, database):
        self.database = database
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

        self.createUsersTable()
        self.createDronesTable()
        self.createCommandsTable()

    def createUsersTable(self):
        createTableStatement = '''
        CREATE TABLE IF NOT EXISTS Users (
            userID INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        );
        '''
        self.executionQuery(createTableStatement)

    def createDronesTable(self):
        createTableStatement = '''
        CREATE TABLE IF NOT EXISTS Drones (
            droneID INTEGER PRIMARY KEY AUTOINCREMENT,
            userID INTEGER,
            droneName TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            droneIP TEXT NOT NULL,
            commandPort INTEGER NOT NULL,
            videoPort INTEGER NOT NULL,
            FOREIGN KEY (userID) REFERENCES Users(userID) ON DELETE CASCADE
        );
        '''
        self.executionQuery(createTableStatement)

    def createCommandsTable(self):
        pass # droneID, takeoff, land, left etc
        createTableStatement = '''
        CREATE TABLE IF NOT EXISTS Commands (
            droneID INTEGER PRIMARY KEY,
            takeoffCommand TEXT NOT NULL,
            landCommand TEXT NOT NULL,
            ascendCommand TEXT NOT NULL,
            descendCommand TEXT NOT NULL,
            hoverCommand TEXT NOT NULL,
            flipCommand TEXT,
            forwardCommand TEXT NOT NULL,
            backwardCommand TEXT NOT NULL,
            leftCommand TEXT NOT NULL,
            rightCommand TEXT NOT NULL,
            yawLeftCommand TEXT NOT NULL,
            yawRightCommand TEXT NOT NULL,
            cameraOnCommand TEXT,
            cameraOffCommand TEXT,
            pingCommand TEXT,
            emergencyCommand TEXT,
            timeReadCommand TEXT,
            batteryReadCommand TEXT,
            speedReadCommand TEXT,

            FOREIGN KEY (droneID) REFERENCES Drones(droneID) ON DELETE CASCADE
        );
        '''
        self.executionQuery(createTableStatement)

    def insertData(self, table, data): # data is of the form ("val1","val2",)
        placeholders = ", ".join("?" * len(data)) # formats as ? ? ? according to the number of values (i.e. the length of data)
        query = f"INSERT INTO {table} VALUES ({placeholders})"
        self.executionQuery(query, data)
        self.connection.commit()
        print(f"data inserted into table: {table}")

    def executionQuery(self, query, params=()): # for INSERT INTO / DELETE / UPDATE queries
        self.cursor.execute(query, params)
        self.connection.commit()
        print("Query executed")

    def fetchQuery(self, query, params=()): # for SELECT / read queries
        self.cursor.execute(query, params)
        result = self.cursor.fetchall()
        return result
    
    def closeConnection(self):
        self.connection.close()