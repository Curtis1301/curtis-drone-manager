import sys
import ctypes

from PySide6.QtWidgets import (
    QWidget, QMainWindow, QApplication, QLabel, QSplitter, QToolBar, 
    QSizePolicy, QStackedWidget, QVBoxLayout, QLineEdit, QPushButton,
    QDialog, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtGui import QAction, QImage, QPixmap, QKeyEvent, QIcon

from databaseManager import DatabaseManager
from components.droneControl import DroneController
from components.workspace import WorkspaceView
from components.flightControl import FlightControlView
from components.telemetry import TelemetryView
from components.summary import SummaryView
from components.imageProcessing import FrameProcessor

class DroneManagerApp():
    '''Overall class that contains the entire project application. 
    Responsible for managing the display ofthe different windows.
    '''
    def __init__(self): # Initialise the database and login window
        self.app = QApplication(sys.argv)
        self.mainDatabase = DatabaseManager('mainDB.db') 

        self.loginWindow = LoginWindow(self.mainDatabase)
        self.registerWindow = None
        self.mainWindow = None

        self.loginWindow.loginSuccess.connect(self.enterApplication)
        self.loginWindow.registerClick.connect(self.enterRegisterWindow)

    @Slot() 
    def showLoginWindow(self):
        self.registerWindow.close()
        self.loginWindow.show()

    @Slot(int) 
    def enterApplication(self, userID):
        self.loginWindow.close()
        self.mainWindow = MainWindow(self.mainDatabase, userID)
        self.mainWindow.show()

    @Slot() 
    def enterRegisterWindow(self):
        self.loginWindow.close()
        self.registerWindow = RegisterWindow(self.mainDatabase)
        self.registerWindow.returnToLoginClick.connect(self.showLoginWindow) 
        self.registerWindow.show()

    def run(self):
        self.loginWindow.show()
        self.app.exec()

class LoginWindow(QWidget):
    loginSuccess = Signal(int) # Signal emitted upon succesful login
    registerClick = Signal() # Signal emitted when the user clicks the register button
    def __init__(self, database):
        super().__init__()
        self.database = database
        with open("styles/login.css", "r") as f:
            self.setStyleSheet(f.read())
        self.setWindowTitle("Drone Manager Login")
        self.setWindowIcon(QIcon('styles/camera-drone.ico')) # https://www.flaticon.com/free-icons/camera-drone by vectorsmarket15
        self.initUI()

    def initUI(self):
        '''Creates the user interface for the login window. Consists of a username and password entry,
        from which the user can either log in or create a new account.
        '''
        layout = QVBoxLayout()
        self.setLayout(layout)

        heading = QLabel("Welcome to Curtis' Drone Manager")
        heading.setAlignment(Qt.AlignCenter)
        heading.setProperty("class","heading")

        subheading = QLabel("Please enter your username and password to log in")
        subheading.setAlignment(Qt.AlignCenter)
        subheading.setProperty("class","subheading")

        unameLabel = QLabel("Username:")
        self.unameEntry = QLineEdit()
        self.unameEntry.setPlaceholderText("Enter username")
        pwordLabel = QLabel("Password:")
        self.pwordEntry = QLineEdit()
        self.pwordEntry.setPlaceholderText("Enter password")
        self.pwordEntry.setEchoMode(QLineEdit.EchoMode.Password)

        self.errorLabel = QLabel()
        self.errorLabel.setProperty("class","error")
        self.errorLabel.hide()

        confirm = QPushButton("Login")
        confirm.clicked.connect(self.login)
        registerNotice = QLabel("If you don't have an account, you can register a new one by clicking below")
        registerNotice.setProperty("class","smallNotice")
        registerBtn = QPushButton("Register")
        registerBtn.clicked.connect(self.register)

        for w in [heading, subheading, unameLabel, self.unameEntry, pwordLabel, self.pwordEntry,self.errorLabel, confirm, registerNotice, registerBtn]:
            layout.addWidget(w)

    def login(self):
        '''Takes data the user has entered and attempts to log in to the application if they match details stored in the database.
        '''
        enteredUsername = str(self.unameEntry.text())
        enteredPassword = str(self.pwordEntry.text())

        if enteredUsername == "" or enteredPassword == "":
            error = "Username and password cannot be empty"
            self.errorLoggingIn(error)
            return

        query = "SELECT * FROM Users WHERE username = ? AND password = ?"
        result = self.database.fetchQuery(query, (enteredUsername, enteredPassword,))
        if result:
            userID = result[0][0] 
            self.loginSuccess.emit(userID)
        else:
            error = "Username or password is incorrect"
            self.errorLoggingIn(error)

    def errorLoggingIn(self, error): # Shows an error on the login screen when called.
        self.errorLabel.setText(error)
        self.errorLabel.show()

    def register(self): # Takes the user to the register window.
        self.errorLabel.hide()
        self.registerClick.emit()

    def keyPressEvent(self, event): # Attempts to login if the user presses the enter/return key
        if event.key() == Qt.Key_Return:
            self.login()
        event.accept()

class RegisterWindow(QWidget):
    returnToLoginClick = Signal() # Signal emitted when the user returns to the login screen.
    def __init__(self, database):
        super().__init__()
        self.database = database
        with open("styles/login.css", "r") as f:
            self.setStyleSheet(f.read())
        self.setWindowTitle("Register a new account")
        self.setWindowIcon(QIcon('styles/camera-drone.ico')) # https://www.flaticon.com/free-icons/camera-drone by vectorsmarket15
        self.initUI()

    def initUI(self):
        '''Creates the UI for the register window. Contains entry boxes for a username, password and confirm password.
        '''
        layout = QVBoxLayout()
        self.setLayout(layout)

        regHeading = QLabel("Create a new account")
        regHeading.setAlignment(Qt.AlignCenter)
        regHeading.setProperty("class","heading")

        regSubheading = QLabel("Please set a username and password for your account")
        regSubheading.setAlignment(Qt.AlignCenter)
        regSubheading.setProperty("class","subheading")

        unameLabel = QLabel("Enter a username:")
        self.unameEntry = QLineEdit()
        self.unameEntry.setPlaceholderText("Enter username")
        pwordLabel = QLabel("Choose a password:")
        self.pwordEntry = QLineEdit()
        self.pwordEntry.setPlaceholderText("Enter password")
        self.pwordEntry.setEchoMode(QLineEdit.EchoMode.Password)
        pwordConfirmLabel = QLabel("Confirm password:")
        self.pwordConfirmEntry = QLineEdit()
        self.pwordConfirmEntry.setPlaceholderText("Confirm password")
        self.pwordConfirmEntry.setEchoMode(QLineEdit.EchoMode.Password)

        self.errorLabel = QLabel()
        self.errorLabel.setProperty("class","error")
        self.errorLabel.hide()

        confirm = QPushButton("Create My Account")
        confirm.clicked.connect(self.createAccount)
        returnBtn = QPushButton("Return To Login")
        returnBtn.clicked.connect(self.returnToLogin)

        for w in [regHeading, regSubheading, unameLabel, self.unameEntry, pwordLabel, self.pwordEntry, pwordConfirmLabel, self.pwordConfirmEntry,self.errorLabel, confirm, returnBtn]:
            layout.addWidget(w)
    
    def errorRegisteringAccount(self, error): # Updates the error text if the user fails to register the account.
        self.errorLabel.setText(error)
        self.errorLabel.show()

    def createAccount(self):
        '''Captures account data entered by the user and attempts to register the account in the database.
        If successful the user is returned to the login screen, otherwise they're shown an error message.
        '''
        newUsername = self.unameEntry.text()
        newPassword = self.pwordEntry.text()
        newPasswordConfirm = self.pwordConfirmEntry.text()


        if not newUsername or not newPassword or not newPasswordConfirm:
            error = "Fields cannot be left empty."
            self.errorRegisteringAccount(error)
            return
        elif newPassword != newPasswordConfirm:
            error = "Entered passwords do not match."
            self.errorRegisteringAccount(error)
            return
        
        query = "SELECT * FROM Users WHERE username = ?"
        result = self.database.fetchQuery(query, (newUsername,))
        if result:
            error = "That username is taken, please select another username."
            self.errorRegisteringAccount(error)
            return
        
        self.database.insertData("Users", (None, newUsername, newPasswordConfirm,))
        self.returnToLogin()

    def returnToLogin(self): # Returns to the login screen when called.
        self.returnToLoginClick.emit()

    def keyPressEvent(self, event): # Attempts to register the accoutn when the enter/return key is pressed.
        if event.key() == Qt.Key_Return:
            self.createAccount()
        event.accept()

class HelpDialog(QDialog):
    def __init__(self):
        '''Simple QDialog class designed to give some instructions on using the application.
        '''
        super().__init__()
        self.setWindowTitle("Help")
        with open("styles/dialog.css", "r") as f:
            self.setStyleSheet(f.read())
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            '''
            For a full walkthrough of the project, please refer to the project documentation and showcase video.

            A number of actions can be carried out at any time using the toolbar at the top of the screen.

            To begin using the application, please select a drone in the summary section using the relevant dropdown.
            If you don't have any drones, please create one using the relevant dialog box.
            Note: if the drone is newly registered, you will need to set its commands by pressing the configure button.

            Once you have selected a drone, you can begin creating a flight plan.
            Simply click on one of the blocks in the selector and drag it into the workspace - this will create a block at that position.
            If you drag a block onto an existing one, they will connect to form a sequence of blocks.
            Logic blocks are available on all tabs and allow you to make use of sequence, selection and iteration in your flight plans.
            Note: some blocks can be double clicked to set their command (including logic blocks).

            In order to carry out the flight plan, press the confirm button when the workspace is not empty. This will take the application 
            into flight mode and enable the execute button.

            When in flight mode, make sure communication is open by pressing the connect action in the toolbar. 
            Pressing the autonomous/manual button will toggle the manual controls in the bottom right of the screen.
            '''
        ))
        acceptBtn = QPushButton("Okay")
        acceptBtn.setProperty("class","button")
        acceptBtn.clicked.connect(self.accept)
        layout.addWidget(acceptBtn)

class SettingsDialog(QDialog):
    logout = Signal() # Signal emitted when the user attempts to log out of their account.
    def __init__(self, database, userID):
        super().__init__()
        self.setWindowTitle("Settings")
        with open("styles/dialog.css", "r") as f:
            self.setStyleSheet(f.read())
        self.database = database
        self.userID = userID
        self.initUI()
    
    def initUI(self):
        '''Creates the UI for the account settings dialog. Allows users to change their passwords and log out.
        '''
        layout = QVBoxLayout(self)
        heading = QLabel("Account Settings")
        heading.setProperty("class","title")
        layout.addWidget(heading)

        formLayout = QFormLayout()
        layout.addLayout(formLayout)

        self.currentPasswordEntry = QLineEdit()
        self.currentPasswordEntry.setEchoMode(QLineEdit.EchoMode.Password)
        formLayout.addRow("Current Password:", self.currentPasswordEntry)
        self.newPasswordEntry = QLineEdit()
        self.newPasswordEntry.setEchoMode(QLineEdit.EchoMode.Password)
        formLayout.addRow("New Password:", self.newPasswordEntry)
        self.confirmNewEntry = QLineEdit()
        self.confirmNewEntry.setEchoMode(QLineEdit.EchoMode.Password)
        formLayout.addRow("Confirm New Password:", self.confirmNewEntry)

        saveBtn = QPushButton("Save")
        saveBtn.setProperty("class","button")
        saveBtn.clicked.connect(self.accept)
        layout.addWidget(saveBtn)
        closeBtn = QPushButton("Cancel")
        closeBtn.setProperty("class","button")
        closeBtn.clicked.connect(self.reject)
        layout.addWidget(closeBtn)

        logoutBtn = QPushButton("Logout")
        logoutBtn.setProperty("class","button")
        logoutBtn.clicked.connect(self.logoutClick)
        layout.addWidget(logoutBtn)

    def logoutClick(self): # logs out the currently logged in user.
        self.reject()
        self.logout.emit() 
        
    def updatePassword(self):
        '''Attempts to update the user's password in the database.
        Shows an error if the password could not be updated.
        '''
        error = None
        currentPassword = str(self.currentPasswordEntry.text())
        newPassword = str(self.newPasswordEntry.text())
        confirmNewPassword = str(self.confirmNewEntry.text())

        if newPassword == confirmNewPassword:
            query = "SELECT password FROM Users WHERE userID = ?"
            result = self.database.fetchQuery(query, (self.userID,))
            if result:
                password = result[0][0]
                if password == currentPassword:
                    query = "UPDATE Users SET password = ? WHERE userID = ?"
                    self.database.executionQuery(query, (newPassword, self.userID,))
                    return
            error = "Current Password is incorrect"
        elif not currentPassword or not newPassword or not confirmNewPassword:
            error = "Please fill in all fields"
        else:
            error = "Entered Passwords do not match"

        title = "Error changing passwords"
        self.showWarningBox(error, title)

    def showWarningBox(self, text, title): # Shows a warning box with the message as a parameter.
        message = QMessageBox()
        message.setIcon(QMessageBox.Icon.Warning)
        message.setText(text)
        message.setWindowTitle(title)
        message.setStandardButtons(QMessageBox.StandardButton.Ok)
        message.exec()

class MainWindow(QMainWindow):
    '''QMainWindow class that contains all of the drone manager's functionality. 
    The widgets displayed within the main window change dynamically as the application is used.
    This window is only displayed after a sucessful login.
    '''
    def __init__(self, database, userID):
        super().__init__()
        self.database = database
        self.userID = userID
        with open("styles/main.css", "r") as f:
            self.setStyleSheet(f.read())

        self.setWindowTitle("Drone Manager Version 3")
        self.setWindowIcon(QIcon('styles/camera-drone.ico')) # https://www.flaticon.com/free-icons/camera-drone by vectorsmarket15
        self.setMinimumSize(1024,600) 
        # self.showMaximized() 
        self.flightMode = False
        self.cameraRunning = False

        self.FrameProcessor = FrameProcessor(self.database, self.userID) 
        self.DroneController = DroneController(self.database, self.userID) 

        self.initUI() 
        self.initComponents()

    def initComponents(self):
        '''Initialises several components needed for the main window to run properly.'''
        self.FrameProcessor.processedImage.connect(self.updateFrame)
        self.FrameProcessor.faceDetected.connect(self.startFaceDetect)
        self.FrameProcessor.setDroneController(self.DroneController)
        self.DroneController.setFrameProcessor(self.FrameProcessor)
        self.DroneController.droneConnectFail.connect(self.showDroneConnectError)

        self.summaryView.droneSet.connect(self.DroneController.setDrone)
        self.summaryView.droneSet.connect(self.FrameProcessor.setDrone)

    def initUI(self):
        '''Creates the overall UI for the entire application. Splitters are used to divide the screen into different sections'''
        mainSplitter = QSplitter(Qt.Horizontal) 

        self.leftSideWidget = QStackedWidget() 
        mainSplitter.addWidget(self.leftSideWidget) 

        self.workspace = WorkspaceView(self.database, self.userID)
        self.workspace.view.sequences.connect(self.prepareFlightMode) 
        self.workspace.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored) 
        self.leftSideWidget.addWidget(self.workspace) 

        self.TelemetryView = TelemetryView(self.DroneController)
        self.TelemetryView.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored) 
        self.leftSideWidget.addWidget(self.TelemetryView) 

        rightSplitter = QSplitter(Qt.Vertical) 

        self.cameraFeed = QLabel("Camera Feed: Off") 
        self.cameraFeed.setAlignment(Qt.AlignCenter) 
        self.cameraFeed.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.cameraFeed.setProperty("class","cameraFeed")
        rightSplitter.addWidget(self.cameraFeed) 

        self.bottomRight = QStackedWidget() 
        rightSplitter.addWidget(self.bottomRight)

        self.summaryView = SummaryView(self.database, self.userID)
        self.summaryView.commandUpdate.connect(self.workspace.initDroneCommands) 
        self.DroneController.updateBatteryReading.connect(self.summaryView.updateBatteryLevel)
        self.summaryView.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored) 
        self.bottomRight.addWidget(self.summaryView) 

        self.flightControls = FlightControlView(self.DroneController, self.database)
        self.flightControls.modeChange.connect(self.summaryView.updateModeLabel)
        self.flightControls.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored) 
        self.bottomRight.addWidget(self.flightControls) 

        rightSplitter.setSizes((100,100)) 
        mainSplitter.addWidget(rightSplitter) 
        mainSplitter.setSizes((100,100)) 

        self.createToolbar() 
        self.setCentralWidget(mainSplitter)

        for button in self.findChildren(QPushButton):
            button.setFocusPolicy(Qt.NoFocus) 

    def createToolbar(self):
        '''Creates the toolbar at the top of the screen'''
        toolbar = QToolBar("Toolbar") 

        connect = QAction("Connect", self) 
        connect.triggered.connect(self.DroneController.establishConnection)
        disconnect = QAction("Disconnect", self) 
        disconnect.triggered.connect(self.DroneController.disconnect) 
        camera = QAction("Toggle Camera", self) 
        camera.triggered.connect(self.cameraClick) 
        settings = QAction("Account Settings", self)
        settings.triggered.connect(self.settingsClick)
        helpAction = QAction("Help", self) 
        helpAction.triggered.connect(self.helpClick)
        self.toggleFlightModeAction = QAction("Enter Flight Mode", self) 
        self.toggleFlightModeAction.triggered.connect(self.toggleFlightModeUI) 
        tFaceDetect= QAction("Toggle Face detection mode", self) 
        tFaceDetect.triggered.connect(self.faceDetectClick) 

        for action in [connect,disconnect,camera,settings,helpAction,self.toggleFlightModeAction,tFaceDetect]: 
            toolbar.addAction(action) 

        self.addToolBar(toolbar) 
    
    def helpClick(self): # Opens the 'help' QDialog 
        helpDialog = HelpDialog()
        helpDialog.exec()

    def settingsClick(self): # Opens the 'settings' QDialog
        settingsDialog = SettingsDialog(self.database, self.userID)
        settingsDialog.logout.connect(self.logoutApplication)
        if settingsDialog.exec():
            settingsDialog.updatePassword()
        else:
            settingsDialog.close()

    def faceDetectClick(self): # Toggles face detection by calling the method in the frame processor
        self.FrameProcessor.toggleFaceDetect()
        self.summaryView.updateFaceDetectLabel(self.FrameProcessor.detectFaces)

    def cameraClick(self): # Toggles the camera on and off (also by calling the method in the frame processor)
        self.FrameProcessor.cameraToggle() 
        self.cameraRunning = not self.cameraRunning
        self.summaryView.updateCameraLabel(self.cameraRunning)

    def toggleFlightModeUI(self):
        '''Switches the main window into flight mode by hiding and showing certain widgets'''
        self.DroneController.clearActiveSequences() 
        index = self.bottomRight.currentIndex() 
        index = 1 - index 
        self.bottomRight.setCurrentIndex(index) 
        self.leftSideWidget.setCurrentIndex(index) 

        self.flightMode = not self.flightMode 
        if self.flightMode:
            self.toggleFlightModeAction.setText("Exit Flight Mode") 
        else:
            self.toggleFlightModeAction.setText("Enter Flight Mode")
            self.flightControls.executeButton.setDisabled(True)

    @Slot(list) 
    def prepareFlightMode(self, sequences):
        '''Called when the user has confirmed a flight plan in the workspace.
        Sets the application to flight mode and sends the sequences to the flight controller.
        '''
        self.flightControls.executeButton.setEnabled(True) 
        self.toggleFlightModeUI() 
        self.DroneController.recieveCommandSequences(sequences) 

    @Slot(QImage)
    def updateFrame(self, img):
        '''Receives frames as formatted QImages and re-formats them into QPixmaps for display in the UI.'''
        pixmap = QPixmap.fromImage(img) 
        scaledPixmap = pixmap.scaled(self.cameraFeed.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation) 
        self.cameraFeed.setPixmap(scaledPixmap)

    @Slot()
    def showDroneConnectError(self):
        message = QMessageBox()
        message.setIcon(QMessageBox.Icon.Critical)
        message.setText("Failed to connect to the drone's specified address")
        message.setWindowTitle("Connection Failure")
        message.setStandardButtons(QMessageBox.StandardButton.Ok)
        message.exec()

    def logoutApplication(self): # Logs the user out of the application
        self.close()

    def startFaceDetect(self): 
        '''Triggers commands that start with 'On Face Detected' if a face is detected when in flight mode.'''
        if self.flightMode:
            self.DroneController.startFaceDetectedThread()

    def keyPressEvent(self, event: QKeyEvent):
        '''Triggers commands that start with 'On Spacebar Pressed' if the spacebar is pressed in flight mode.'''
        if event.key() == Qt.Key_Space: 
            if self.flightMode:
                self.DroneController.startKeyPressThread()  

        return super().keyPressEvent(event)

if __name__ == "__main__":
    myappid = u'curtis.droneManager.version3.2025'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid) 
    ''' A workaround for dispalying the correct ICO in the taskbar, see this post:
    https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
    '''
    App = DroneManagerApp()
    App.run()