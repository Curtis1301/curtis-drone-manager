from PySide6.QtWidgets import ( QLabel, QSplitter,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QGridLayout, QDial
)
from PySide6.QtCore import Qt, Slot

class TelemetryView(QWidget):
    def __init__(self, droneController):
        super().__init__()
        self.DroneController = droneController
        self.DroneController.telemetryRecieved.connect(self.updateTelemetry) # If a telemetry update is given carry out the relevant method
        self.DroneController.updateLog.connect(self.updateCommandLog)
        self.setProperty("class", "telemetryView")

        self.initUI()

    def initUI(self):
        overallLayout = QVBoxLayout(self) # This is the overall layout of the workspace
        splitter = QSplitter(Qt.Vertical)

        self.commandLog = QGroupBox("Communication Log") # SECTION THAT SHOWS THE MOST RECENTLY SENT AND UPCOMING COMMANDS
        commandLogLayout = QHBoxLayout(self.commandLog)
        self.lastSentCommand = QLabel("Commands sent to the drone will appear here")
        self.lastSentCommand.setProperty("class","commandLogLabel")
        commandLogLayout.addWidget(self.lastSentCommand)
        splitter.addWidget(self.commandLog)

        self.telemetryDisplay = QGroupBox("Displays and Indicators")
        self.telemetryDisplayLayout = QGridLayout()
        self.telemetryDisplayLayout.setRowStretch(0,0)
        self.telemetryDisplayLayout.setRowStretch(1,1)
        self.telemetryDisplay.setLayout(self.telemetryDisplayLayout)

        self.airspeedLabel = QLabel("Airspeed: 0cm/s")
        self.airspeedLabel.setAlignment(Qt.AlignCenter)
        self.airspeedLabel.setProperty("class","dialLabel")
        self.telemetryDisplayLayout.addWidget(self.airspeedLabel, 0, 0)
        self.heightLabel = QLabel("Altitude: 0cm")
        self.heightLabel.setAlignment(Qt.AlignCenter)
        self.heightLabel.setProperty("class","dialLabel")
        self.telemetryDisplayLayout.addWidget(self.heightLabel, 0, 1)
        
        self.createGauges()

        toggleTelBtn = QPushButton("Click to toggle telemetry logging")
        toggleTelBtn.setProperty("class","workspaceButton")
        toggleTelBtn.clicked.connect(self.toggleTelThread)

        self.telemetryDisplayLayout.addWidget(toggleTelBtn, 2, 0, 1, 2)
        splitter.addWidget(self.telemetryDisplay)

        self.telBox = QGroupBox("Live Telemetry Readings")
        self.telBoxLayout = QGridLayout(self.telBox)

        self.pitch = QLabel("Pitch: ")
        self.roll = QLabel("Roll: ")
        self.yaw = QLabel("Yaw: ")
        self.xSpeed = QLabel("X Speed: ")
        self.ySpeed = QLabel("Y Speed: ")
        self.zSpeed = QLabel("Z Speed: ")
        self.tempLow = QLabel("Temp Low: ")
        self.tempHigh = QLabel("Temp High: ")
        self.tofAltitude = QLabel("Altitutde: ")
        self.height = QLabel("Height above start: ")
        self.bat = QLabel("Battery: ")
        self.baro = QLabel("Barometer: ")
        self.time = QLabel("Flight Time: ")
        self.resAccel = QLabel("Acceleration: ")

        self.telemetryWidgets = [
            self.pitch, self.roll, self.yaw, self.xSpeed, self.ySpeed, self.zSpeed,
            self.tempLow, self.tempHigh, self.tofAltitude, self.height, self.bat, 
            self.baro, self.time, self.resAccel
        ]
        
        for i, wdg in enumerate(self.telemetryWidgets):
            self.telBoxLayout.addWidget(wdg, i//3, i%3)

        splitter.addWidget(self.telBox)
        splitter.setSizes([200,400,400])
        overallLayout.addWidget(splitter)
        self.setLayout(overallLayout) # Set the overall layout
    
    def createGauges(self):
        self.speedometer = QDial()
        self.speedometer.setMaximum(100)
        self.speedometer.setNotchesVisible(True)
        self.speedometer.setDisabled(True)
        self.telemetryDisplayLayout.addWidget(self.speedometer, 1, 0)

        self.altimeter = QDial()
        self.altimeter.setMaximum(500)
        self.altimeter.setNotchesVisible(True)
        self.altimeter.setDisabled(True)
        self.telemetryDisplayLayout.addWidget(self.altimeter, 1, 1)

    def formatTelemetry(self, txt):
        txt = txt.strip("\n\r")
        txt = txt.split(";")
        txt.pop()
        return txt

    @Slot(str)
    def updateTelemetry(self, msg):
        splitMsg = self.formatTelemetry(msg)
        if splitMsg:
            for data, wdg in zip(splitMsg, self.telemetryWidgets):
                label = wdg.text().split(": ")[0] # get the prefix for the telemetry type
                data = data.split(":")[1]
                wdg.setText(f"{label}: {data}")

            xVelocity = int(splitMsg[3].split(":")[1])
            yVelocity = int(splitMsg[4].split(":")[1])
            zVelocity = int(splitMsg[5].split(":")[1])
            resultantSpeed = (xVelocity ** 2 + yVelocity ** 2 + zVelocity ** 2) ** 0.5
            airspeedValue = round(resultantSpeed)
            tofAltitudeValue = int(splitMsg[8].split(":")[1])

            self.airspeedLabel.setText(f"Airspeed: {airspeedValue}cm/s")
            self.speedometer.setValue(airspeedValue)
            self.heightLabel.setText(f"Altitude: {tofAltitudeValue}cm")    
            self.altimeter.setValue(tofAltitudeValue)

    def toggleTelThread(self): # Turns the thread on/off
        if not self.DroneController.telemetryRec:
            self.DroneController.telemetryRec = True
            self.DroneController.startTelThread()
        else: 
            self.DroneController.telemetryRec = False

    @Slot(str)
    def updateCommandLog(self, recentCommand):
        self.lastSentCommand.setText(recentCommand)