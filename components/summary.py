import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,  QComboBox, QGroupBox, QLabel, QComboBox, 
    QPushButton, QDialog, QFormLayout, QLineEdit, QMessageBox
    )
from PySide6.QtCore import Slot, Signal

class SummaryView(QWidget): # creates the VIEW for the drone's summary information
    droneSet = Signal(str)
    commandUpdate = Signal(str)
    def __init__(self, database, userID):
        super().__init__()
        self.database = database
        self.userID = userID
        self.hasDrones = False

        self.initUI()

    def initUI(self):
        '''
        Creates the UI of the summary layout as a grid
        '''
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        summaryContainer = QGroupBox("Summary")
        layout.addWidget(summaryContainer)

        self.summaryLayout = QVBoxLayout()
        summaryContainer.setLayout(self.summaryLayout)

        self.createDroneSelector()

        self.latestReponseLabel = QLabel("Currently Connected to:")
        self.latestReponseLabel.setProperty("class","droneConnectLabel")
        self.summaryLayout.addWidget(self.latestReponseLabel)

        self.batteryLabel = QLabel("Current Battery Level: Not Connected")
        self.modeLabel = QLabel("Current Control Mode: Autonomous")
        self.cameraStatus = QLabel("Camera Feed: Disabled")
        self.faceDetectMode = QLabel("Face Detect Mode: Enabled")
        
        for w in [self.batteryLabel, self.modeLabel, self.cameraStatus, self.faceDetectMode]:
            w.setProperty("class","infoLabel")
            self.summaryLayout.addWidget(w)

    def updateConnectedDroneLabel(self, name):
        self.latestReponseLabel.setText(f"Currently Connected to: {name}")

    @Slot()
    def updateModeLabel(self, mode):
        self.modeLabel.setText(f"Current Control Mode: {mode.capitalize()}")

    @Slot()
    def updateBatteryLevel(self, level):
        self.batteryLabel.setText(f"Current Battery Level: {str(level)}%")

    def updateCameraLabel(self, cameraRunning):
        label = f"Camera Feed: Enabled" if cameraRunning else f"Camera Feed: Disabled"
        self.cameraStatus.setText(label)

    def updateFaceDetectLabel(self, detectMode):
        label = f"Face Detect Mode: Enabled" if detectMode else f"Face Detect Mode: Disabled"
        self.faceDetectMode.setText(label)

    def createDroneSelector(self):
        '''
        If the user has drones, the drone selector is a combo box that lists all the drones.
        Otherwise it is a button that creates a new drone when clicked.
        '''
        selectLayout = QHBoxLayout()

        query = "SELECT * FROM Drones WHERE userID = ?"
        results = self.database.fetchQuery(query, (self.userID,))

        self.droneConfigButton = QPushButton("Configure Drone")
        self.droneConfigButton.setDisabled(True)
        self.droneConfigButton.setProperty("class","configButton")
        self.droneConfigButton.clicked.connect(self.configDrone)  

        if results:
            self.hasDrones = True
            self.droneSelector = QComboBox()
            self.droneSelector.setProperty("class","selectorComboBox")
            self.formatDroneSelector(results)
        else:
            self.droneSelector = QPushButton("+ Click to add a new drone")
            self.droneSelector.setProperty("class","selectorButton")
            self.droneSelector.clicked.connect(self.createNewDrone)
            self.droneConfigButton.setDisabled(True)

        selectLayout.addWidget(self.droneSelector)
        selectLayout.addWidget(self.droneConfigButton)
        self.summaryLayout.insertLayout(0,selectLayout)

    def formatDroneSelector(self, results):
        '''
        takes sql results to build the drone select combo box
        '''
        self.droneSelector.addItem("No Drone Selected")
        for record in results:
            droneLabel = f"Name: {record[2]}, Manufacturer: {record[3]}"
            self.droneSelector.addItem(droneLabel)
            self.droneSelector.setItemData(self.droneSelector.count() - 1, record[2]) # attatches the name to the drone item
        self.droneSelector.addItem("+ New Drone")
        self.droneSelector.setItemData(self.droneSelector.count() - 1, "new drone")
        self.droneSelector.currentIndexChanged.connect(self.droneSelectChanged)

    def updateDroneSelector(self):
        '''
        If the user creates a new drone or deletes one, the list is updated
        '''
        query = "SELECT * FROM Drones WHERE userID = ?"
        results = self.database.fetchQuery(query, (self.userID,))
        if isinstance(self.droneSelector, QComboBox) and results:
            self.droneConfigButton.setDisabled(True)
            self.droneSelector.currentIndexChanged.disconnect() # Do nothing when current index changed for now
            self.droneSelector.clear()
            self.formatDroneSelector(results)
        else:
            self.summaryLayout.removeWidget(self.droneConfigButton)
            self.droneConfigButton.deleteLater() # get rid of the config button as it is no longer needed (as there are no drones)
            self.summaryLayout.removeWidget(self.droneSelector)
            self.droneSelector.deleteLater()

            self.createDroneSelector()  

    def droneSelectChanged(self):
        '''
        triggered when the user changes their drone selection
        '''
        if self.hasDrones:
            self.droneConfigButton.setEnabled(True)
            selection = self.droneSelector.itemData(self.droneSelector.currentIndex())
            if selection == "new drone":
                self.droneSelector.setCurrentIndex(0)
                self.createNewDrone()
                return
            elif not selection:
                self.droneConfigButton.setDisabled(True)
            self.updateConnectedDroneLabel(selection)
            self.droneSet.emit(selection)
            self.commandUpdate.emit(selection)
        else:
            self.createNewDrone()

    def createNewDrone(self):
        '''
        Inserts the data of the new drone into the database
        '''
        newDroneDialog = NewDroneDialog()
        if newDroneDialog.exec():
            droneData = newDroneDialog.getDroneData()
            if self.validateDroneUpdate(droneData):
                self.database.insertData("Drones", (None, self.userID, droneData[0], droneData[1], droneData[2], droneData[3], droneData[4],)) # write the drone data to the database
                self.updateDroneSelector()
                topValue = self.droneSelector.count() - 2
                self.droneSelector.setCurrentIndex(topValue)
                self.droneConfigButton.setEnabled(True)

    def validateDroneUpdate(self, data, checkNameTaken=True):
        '''
        Checks that the user hasn't put any illegal data into the form. If command data also needs to be checked, then it will be here.
        '''
        errorTitle = "Error creating new drone"

        if checkNameTaken:
            query = "SELECT droneName FROM Drones WHERE userID = ?"
            takenDroneNames = self.database.fetchQuery(query, (self.userID,)) # Get the drone ID of that drone
            for name in takenDroneNames:
                if name[0] == data[0]:
                    error = "A drone with this name already exists"
                    self.showWarningBox(error, errorTitle)
                    return False

        for dataItem in data: # Check for empty fields
            if len(dataItem) == 0:
                error = "All drone information must be present"
                self.showWarningBox(error, errorTitle)
                return False
            
        try: # check data types for the port numbers
            data[3] = int(data[3])
            data[4] = int(data[4])
        except ValueError:
            error = "Ports must be integer values"
            self.showWarningBox(error, errorTitle)
            return False
        
        if (0 > data[3] or data[3] > 65535 or 0 > data[4] or data[4] > 65535): # check ranges for the ports
            error = "Port is outside the valid range 0 to 65535"
            self.showWarningBox(error, errorTitle)
            return False
        
        regex = r'^(\d{1,3}\.){3}\d{1,3}$' # https://sparkbyexamples.com/python/python-regex-ip-address/
        match = re.match(regex, data[2]) # validation of IP address
        if not bool(match):
            error = "The drone IP address is invalid"
            self.showWarningBox(error, errorTitle)
            return False

        return True

    def showWarningBox(self, text, title):
        message = QMessageBox()
        message.setIcon(QMessageBox.Icon.Warning)
        message.setText(text)
        message.setWindowTitle(title)
        message.setStandardButtons(QMessageBox.StandardButton.Ok)
        message.exec()

    def getDroneSelection(self):
        '''
        Returns the name of the selected drone in the drone selector combo box
        or None if no drone is selected
        '''
        if self.hasDrones:
            return self.droneSelector.itemData(self.droneSelector.currentIndex())

    @Slot()
    def deleteDrone(self):
        name = self.getDroneSelection()

        query = "SELECT droneID FROM Drones WHERE userID = ? AND droneName = ?"
        droneID = self.database.fetchQuery(query, (self.userID, name,))[0][0] # Get the drone ID of that drone

        if droneID:
            query = "DELETE FROM Drones WHERE userID = ? AND droneName = ?"
            self.database.executionQuery(query, (self.userID, name,))

            query = "DELETE FROM Commands WHERE droneID = ?"
            self.database.executionQuery(query, (droneID,))

            self.updateDroneSelector()

    def configDrone(self):
        name = self.getDroneSelection()
        if name != "No Drone Selected":
            query = "SELECT * FROM Drones WHERE userID = ? AND droneName = ?"
            droneDataResult = self.database.fetchQuery(query, (self.userID, name,))

            if droneDataResult:
                droneID = droneDataResult[0][0]
                query = "SELECT * FROM Commands WHERE droneID = ?"
                droneCommandResult = self.database.fetchQuery(query, (droneID,))
                droneConfigDialog = ConfigDroneDialog(droneDataResult, droneCommandResult)
                droneConfigDialog.deleteAction.connect(self.deleteDrone)

                if droneConfigDialog.exec():
                    userInput = droneConfigDialog.getNewData()
                    droneInfoValues = userInput[0]
                    commandList = userInput[1]

                    if name == droneInfoValues[0]: # The name value entered on the form is the same as when it started, so we don't need to display an existing drone error message
                        checkExisiting = False
                    else:
                        checkExisiting = True

                    if not self.validateDroneUpdate(droneInfoValues, checkNameTaken=checkExisiting): # NOTE: it is fine for the done to have the same name if it is just beind edited
                        return
                    for cmdInput in commandList:
                        if ' ' in cmdInput:
                            self.showWarningBox("Commands cannot include spaces.", "Error setting drone commands")
                            return

                    droneInfoValues.extend([self.userID, name])
                    droneInfoValues = tuple(droneInfoValues)

                    query = '''
                    UPDATE Drones
                    SET droneName = ?, manufacturer = ?, droneIP = ?, commandPort = ?, videoPort = ?
                    WHERE userID = ? AND droneName = ?
                    '''
                    self.database.executionQuery(query, droneInfoValues)

                    if droneCommandResult:
                        commandList.append(droneID)
                        commandList = tuple(commandList)
                        query = '''
                        UPDATE Commands
                        SET takeOffCommand = ?, landCommand = ?, ascendCommand = ?, descendCommand = ?, hoverCommand = ?, flipCommand = ?, forwardCommand = ?, 
                        backwardCommand = ?, leftCommand = ?, rightCommand = ?, yawLeftCommand = ?, yawRightCommand = ?, cameraOnCommand = ?, cameraOffCommand = ?,
                        pingCommand = ?, emergencyCommand = ?, timeReadCommand = ?, batteryReadCommand = ?, speedReadCommand = ?
                        WHERE droneID = ?
                        '''
                        self.database.executionQuery(query, commandList)
                    else:
                        paramters = [droneID]
                        paramters.extend(commandList)
                        paramters = tuple(paramters)
                        self.database.insertData("Commands", paramters)

                    index = self.droneSelector.currentIndex()
                    self.updateDroneSelector()
                    self.droneSelector.setCurrentIndex(index)
                    self.droneSelectChanged()

class NewDroneDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add a new drone to the database")
        with open("styles/dialog.css", "r") as f:
            self.setStyleSheet(f.read())
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        title = QLabel("Add a new drone")
        title.setProperty("class","title")
        layout.addWidget(title)

        formLayout = QFormLayout()
        self.droneNameInput = QLineEdit()
        formLayout.addRow("Name of Drone:", self.droneNameInput)
        self.manufacturerInput = QLineEdit()
        formLayout.addRow("Manufacturer:", self.manufacturerInput)
        self.droneIPInput = QLineEdit()
        formLayout.addRow("IP Address:", self.droneIPInput)
        self.commandPortInput = QLineEdit()
        formLayout.addRow("Commands Port:", self.commandPortInput)
        self.videoPortInput = QLineEdit()
        formLayout.addRow("Video Port:", self.videoPortInput)

        layout.addLayout(formLayout)

        confirm = QPushButton("Confirm")
        confirm.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)

        layout.addWidget(confirm)
        layout.addWidget(cancel)

    def getDroneData(self):
        droneData = [self.droneNameInput.text(), self.manufacturerInput.text(), self.droneIPInput.text(), self.commandPortInput.text(), self.videoPortInput.text()]
        return droneData
    
class ConfigDroneDialog(QDialog):
    deleteAction = Signal()
    def __init__(self, droneData, droneCommandData):
        super().__init__()
        self.setWindowTitle("Configure Drone")
        with open("styles/dialog.css", "r") as f:
            self.setStyleSheet(f.read())
        self.droneData = droneData
        self.droneCommandData = droneCommandData
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        formLayout = QFormLayout()

        infoLabel = QLabel("Drone Information: ")
        infoLabel.setProperty("class","title")
        formLayout.addRow(infoLabel)

        self.droneNameInput = QLineEdit()
        formLayout.addRow("Name of Drone:", self.droneNameInput)
        self.manufacturerInput = QLineEdit()
        formLayout.addRow("Manufacturer:", self.manufacturerInput)
        self.droneIPInput = QLineEdit()
        formLayout.addRow("IP Address:", self.droneIPInput)
        self.commandPortInput = QLineEdit()
        formLayout.addRow("Commands Port:", self.commandPortInput)
        self.videoPortInput = QLineEdit()
        formLayout.addRow("Video Port:", self.videoPortInput)

        commandLabel = QLabel("Drone Command Format:")
        commandLabel.setProperty("class","title")
        formLayout.addRow(commandLabel)

        self.takeoffCmd = QLineEdit()
        formLayout.addRow("Takeoff:", self.takeoffCmd)
        self.landCmd = QLineEdit()
        formLayout.addRow("Land:", self.landCmd)
        self.ascendCmd = QLineEdit()
        formLayout.addRow("Ascend:", self.ascendCmd)
        self.descendCmd = QLineEdit()
        formLayout.addRow("Descend:", self.descendCmd)
        self.hoverCmd = QLineEdit()
        formLayout.addRow("Hover:", self.hoverCmd)
        self.flipCmd = QLineEdit()
        formLayout.addRow("Flip:", self.flipCmd)
        self.forwardCmd = QLineEdit()
        formLayout.addRow("Forward:", self.forwardCmd)
        self.backwardCmd = QLineEdit()
        formLayout.addRow("Backward:", self.backwardCmd)
        self.leftCmd = QLineEdit()
        formLayout.addRow("Left:", self.leftCmd)
        self.rightCmd = QLineEdit()
        formLayout.addRow("Right:", self.rightCmd)
        self.yawleftCmd = QLineEdit()
        formLayout.addRow("Yaw Left:", self.yawleftCmd)
        self.yawrightCmd = QLineEdit()
        formLayout.addRow("Yaw Right:", self.yawrightCmd)
        self.cameraOnCmd = QLineEdit()
        formLayout.addRow("Camera On:", self.cameraOnCmd)
        self.cameraOffCmd = QLineEdit()
        formLayout.addRow("Camera Off:", self.cameraOffCmd)
        self.pingCommand = QLineEdit()
        formLayout.addRow("Ping:", self.pingCommand)
        self.emergencyCommand = QLineEdit()
        formLayout.addRow("Emergency:", self.emergencyCommand)
        self.timeReadCommand = QLineEdit()
        formLayout.addRow("Read TOF distance (altitude):", self.timeReadCommand)
        self.batteryReadCommand = QLineEdit()
        formLayout.addRow("Read Battery:", self.batteryReadCommand)
        self.speedReadCommand = QLineEdit()
        formLayout.addRow("Read Speed:", self.speedReadCommand)

        self.fillExistingData()

        layout.addLayout(formLayout)

        confirm = QPushButton("Confirm")
        confirm.clicked.connect(self.accept)
        delete = QPushButton("Delete this drone")
        delete.clicked.connect(self.deleteDrone)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)

        layout.addWidget(confirm)
        layout.addWidget(delete)
        layout.addWidget(cancel)

    def deleteDrone(self):
        self.close()
        self.deleteAction.emit()

    def fillExistingData(self):
        self.droneInformationLabels = [self.droneNameInput, self.manufacturerInput, self.droneIPInput, self.commandPortInput, self.videoPortInput]
        self.droneCommandLabels = [
            self.takeoffCmd, self.landCmd, self.ascendCmd, self.descendCmd, self.hoverCmd, self.flipCmd, self.forwardCmd, 
            self.backwardCmd, self.leftCmd, self.rightCmd, self.yawleftCmd, self.yawrightCmd, self.cameraOnCmd, self.cameraOffCmd,
            self.pingCommand, self.emergencyCommand, self.timeReadCommand, self.batteryReadCommand, self.speedReadCommand
        ]
        for data, label in zip(self.droneData[0][2:], self.droneInformationLabels): # [:2] because we don't care about drone and user id
            label.setText(str(data))

        if self.droneCommandData:
            for data, label in zip(self.droneCommandData[0][1:], self.droneCommandLabels):
                label.setText(str(data))

    def getNewData(self):
        droneInfoList = []
        droneCommandList = []
        for lbl in self.droneInformationLabels:
            droneInfoList.append(lbl.text())
        for lbl in self.droneCommandLabels:
            droneCommandList.append(lbl.text())

        return [droneInfoList, droneCommandList]