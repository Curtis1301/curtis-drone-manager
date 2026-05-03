from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QSlider, QGroupBox, QLabel
)
from PySide6.QtCore import Qt, Signal

class FlightControlView(QWidget):
    modeChange = Signal(str)
    def __init__(self, droneController, database):
        super().__init__()
        self.DroneController = droneController
        self.database = database
        self.mode = "AUTONOMOUS" 

        self.initUI() 

    def initUI(self):
        self.manualControls = ManualControlSystem(controller=self.DroneController) 
        flightLayout = QVBoxLayout() 
        
        controlButtons = QHBoxLayout() 
        self.executeButton = QPushButton("EXECUTE")
        self.executeButton.setDisabled(True)
        self.executeButton.clicked.connect(self.DroneController.startTransmissionThread) 
        
        land = QPushButton("LAND")
        land.clicked.connect(lambda: self.DroneController.sendManualFlightCommand(1, None))

        self.manual = QPushButton("AUTONOMOUS")
        self.manual.setProperty("class","workspaceButton")
        self.manual.clicked.connect(self.toggleMode)

        emergency = QPushButton("EMERGENCY")
        emergency.clicked.connect(self.DroneController.emergency) 

        for lbl, className in zip([self.executeButton, land, emergency],["executeBtn","landBtn","emergencyBtn"]):
            lbl.setProperty("class",f"topbarButton {className}")
            controlButtons.addWidget(lbl)

        controlButtons.addWidget(self.manual)
        flightLayout.addLayout(controlButtons) 
        flightLayout.addWidget(self.manualControls) 

        self.setLayout(flightLayout) 
    
    def toggleMode(self):
        if self.mode == "AUTONOMOUS":
            self.mode = "MANUAL"
            self.manual.setText("MANUAL")
            for widget in self.manualControls.findChildren(QPushButton): 
                widget.setEnabled(True)
            self.manualControls.valueSlider.setEnabled(True)
        else:
            self.mode = "AUTONOMOUS"
            self.manual.setText("AUTONOMOUS")
            for widget in self.manualControls.findChildren(QPushButton): 
                widget.setDisabled(True)
            self.manualControls.valueSlider.setDisabled(True)
        
        self.modeChange.emit(self.mode)

class ManualControlSystem(QGroupBox): 
    def __init__(self, controller):
        super().__init__()
        self.DroneController = controller
        self.setTitle("Manual Control System")
        self.setProperty("class","manualControls")
        self.baseAmount = 50 
        self.initUI() 
        
    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        controlsLayout = QGridLayout()
        sliderLayout = QHBoxLayout()

        self.valueLabel = QLabel(f"Use the slider to set a value for the manual commands.\nCurrent Value: {self.baseAmount}")
        self.valueLabel.setProperty("class","sliderLabel")
        self.valueLabel.setAlignment(Qt.AlignCenter)
        sliderLayout.addWidget(self.valueLabel)

        self.valueSlider = QSlider(Qt.Horizontal)
        self.valueSlider.setProperty("class","slider")
        self.valueSlider.setMaximum(360)
        self.valueSlider.setMinimum(20)
        self.valueSlider.setValue(self.baseAmount)
        self.valueSlider.valueChanged.connect(self.updateAmount)
        self.valueSlider.setDisabled(True)
        sliderLayout.addWidget(self.valueSlider)
        layout.addLayout(sliderLayout)

        ascendBtn = QPushButton("Ascend")
        ascendBtn.clicked.connect(lambda: self.DroneController.sendManualFlightCommand(2, self.baseAmount)) 
        controlsLayout.addWidget(ascendBtn, 0, 1)
        descendBtn = QPushButton("Descend")
        descendBtn.clicked.connect(lambda: self.DroneController.sendManualFlightCommand(3, self.baseAmount))
        controlsLayout.addWidget(descendBtn, 3, 1)

        fwrdBtn = QPushButton("Forwards")
        fwrdBtn.clicked.connect(lambda: self.DroneController.sendManualFlightCommand(6, self.baseAmount))
        controlsLayout.addWidget(fwrdBtn, 1, 1)
        bwrdBtn = QPushButton("Backwards")
        bwrdBtn.clicked.connect(lambda: self.DroneController.sendManualFlightCommand(7, self.baseAmount))
        controlsLayout.addWidget(bwrdBtn, 2, 1)
        leftBtn = QPushButton("Left")
        leftBtn.clicked.connect(lambda: self.DroneController.sendManualFlightCommand(8, self.baseAmount))
        controlsLayout.addWidget(leftBtn, 1, 0)
        rightBtn = QPushButton("Right")
        rightBtn.clicked.connect(lambda: self.DroneController.sendManualFlightCommand(9, self.baseAmount))
        controlsLayout.addWidget(rightBtn, 1, 2)

        lYawBtn = QPushButton("Yaw Left")
        lYawBtn.clicked.connect(lambda: self.DroneController.sendManualFlightCommand(10, self.baseAmount))
        controlsLayout.addWidget(lYawBtn, 2, 0)
        rYawBtn = QPushButton("Yaw Right")
        rYawBtn.clicked.connect(lambda: self.DroneController.sendManualFlightCommand(11, self.baseAmount))
        controlsLayout.addWidget(rYawBtn, 2, 2)

        layout.addLayout(controlsLayout)
        
        for wdg in self.findChildren(QPushButton): 
            wdg.setDisabled(True)

    def updateAmount(self, val):
        self.baseAmount = val
        self.valueLabel.setText(f"Use the slider to set a value for the manual commands.\nCurrent Value: {self.baseAmount}")