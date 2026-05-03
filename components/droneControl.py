import socket as soc
import threading
import time
from PySide6.QtCore import QObject, Signal, Slot

class DroneController(QObject): # Main drone controller that handles communication
    ''' The main Drone Controller object, handles the communication to and from the drone.
    '''
    updateLog = Signal(str)
    updateBatteryReading = Signal(int)
    telemetryRecieved = Signal(str)
    droneConnectFail = Signal()
    def __init__(self, database, userID):
        super().__init__()
        self.database = database
        self.userID = userID
        self.commandAddress = None
        self.standardCommands = None
        self.logBattery = False
        self.socket = None
        self.FrameProcessor = None

        self.activeExecInstructions = []
        self.keyPressInstructions = []
        self.faceDetectedInstructions = []
        self.detectFaceThreadRunning = False
        self.telemetryRec = False

        self.socketLock = False

    @Slot(str)
    def setDrone(self, droneName):
        ''' Called when the user sets a drone in the summary section.
        Sets the drone commands to the ones retrieved from the database and attempts to open the s  ocket.
        '''
        self.logBattery = False
        self.standardCommands = None
        self.commandAddress = None
        if droneName == "No Drone Selected":
            return
        query = "SELECT droneID, droneIP, commandPort FROM Drones WHERE userID = ? AND droneName = ?"
        results = self.database.fetchQuery(query, (self.userID, droneName,))
        if results:
            self.droneID = results[0][0]
            ip = results[0][1]
            cmdPort = results[0][2]
            print(f"Drone controller found drone with name {droneName}, ip {ip}, cmd port {cmdPort}")
            if ip and cmdPort:
                self.commandAddress = (ip, cmdPort)
            self.setStandardCommands()

    def setStandardCommands(self):
        '''Gets the commands from the database and sets them'''
        query = "SELECT * FROM Commands WHERE droneID = ?"
        results = self.database.fetchQuery(query, (self.droneID,))
        if results:
            self.standardCommands = results[0][1:] # exclude the droneID from the list as it is not needed

    def setFrameProcessor(self, processor):
        '''Sets the frame processor'''
        self.FrameProcessor = processor

    def openSocket(self):
        '''Opens the communication socket for commands and telemetry (they are bound to the host computer 9000, 8890)'''
        if self.socket:
            self.closeSocket()
        try:
            self.socket = soc.socket(soc.AF_INET, soc.SOCK_DGRAM) # command socket
            self.socket.bind(('', 9000))
            self.socket.settimeout(1)

            self.stateSock = soc.socket(soc.AF_INET, soc.SOCK_DGRAM) # state / telemetry socket
            self.stateSock.bind(('', 8890))
            self.stateSock.settimeout(1)
        except soc.error as e:
            return e

    def closeSocket(self):
        '''Closes any sockets that are currently open'''
        self.socket.close()
        self.stateSock.close()
        self.socket = None
        self.stateSock = None

    def send(self, command, logMessage=True):
        '''Sends a string to the drone via the command socket.
        logMessage is a flag determining whether the command should be logged to the telemetry section.
        '''
        if not self.socketLock: # socketLock prevents the socket sending more than one command at any given instant
            self.socketLock = True
            try:
                if logMessage:
                    logMessage = f"{command.upper()} command sent to drone with IP {self.commandAddress[0]}"
                    self.updateLog.emit(logMessage)
                    print(str(logMessage))
                self.socket.sendto(command.encode(), self.commandAddress)
            except Exception or soc.error as e:
                print(e)
            self.socketLock = False
        else:
            time.sleep(0.1)
            self.send(command, logMessage)

    def receive(self):
        '''Receive a response from the drone via the command socket.
        Returns a string with the response that was received, otherwise None if there is an error.
        '''
        try:
            response, ip_address = self.socket.recvfrom(1024)
            print(response)
            return response.decode(encoding='utf-8')
        except Exception or soc.error as e:
            return None
    
    def receiveState(self):
        '''Receive a response from the telemetry socket.
        Returns the telemetry data as an unformatted string.
        '''
        try:
            data, address = self.stateSock.recvfrom(1024)
            address = address[0]
            return data.decode()
        except soc.error:
            return None
        except Exception as e:
            return None

    ## STANDARD COMMANDS

    def sendManualFlightCommand(self, index, amount):
        if self.standardCommands:
            if amount:
                self.send(f"{self.standardCommands[index]} {amount}")
            else:
                self.send(self.standardCommands[index])
            resp = self.receive()
            return resp
        return None

    def streamOn(self): # Turn on the video stream.
        if self.standardCommands:
            self.send(self.standardCommands[12])
            resp = self.receive()
            return resp
        return None

    def streamOff(self): # Turn off the video stream.
        if self.standardCommands:
            self.send(self.standardCommands[13])
            resp = self.receive()
            return resp
        return None

    def establishConnection(self): # Open the socket and attempt to ping the drone.
        self.openSocket()
        if self.standardCommands:
            self.send(self.standardCommands[14])
            resp = self.receive()
            if resp and not self.logBattery:
                self.startBatteryLogThread()
            return resp
        self.droneConnectFail.emit()
        return None
        
    def emergency(self): # Sends the drone's ermergency command
        if self.standardCommands:
            self.send(self.standardCommands[15])
            resp = self.receive()
            return resp
        return None

    def disconnect(self): # Send the emergency command and close the socket.
        if self.standardCommands:
            self.send(self.standardCommands[15])
            self.logBattery = False
        if self.socket:
            self.closeSocket()

    ## READ COMMANDS

    def readFlightTime(self): # Returns the current flight time from the telemetry.
        if self.standardCommands:
            self.send(self.standardCommands[16])
            resp = self.receive()
            if resp is not None:
                resp = resp.strip("\r\n")[:-1]
            return resp
        return None

    def readBattery(self, logMessage=True): # Returns the current battery level (%) from the telemetry.
        if self.standardCommands:
            self.send(self.standardCommands[17], logMessage)
            resp = self.receive()
            if resp is not None:
                resp = resp.strip("\r\n")
            return resp
        return None
    
    def readSpeed(self): # Returns the current speed of the drone from the telemetry.
        if self.standardCommands:
            self.send(self.standardCommands[18])
            resp = self.receive()
            if resp is not None:
                resp = resp.strip("\r\n")[:-1]
            return resp
        return None

    def readValueFromTelemetry(self, string):
        ''' Some block commands need access to data that is only sent via the telemetry socket.
        Takes in a string with the requested data as an argument.
        Searches for and returns the corresponding data value for the data requested, otherwise None.
        '''
        data = self.receiveState()
        if data is None:
            return None
        data = data.strip("\n\r")
        data = data.split(";")

        typeDict = {
            "Vertical velocity": 'vgz',
            "Altitude": 'h',
        }

        if string != "Horizontal velocity":
            searchTerm = typeDict[string]
            return self.searchForValue(data, searchTerm)
        else:
            searchOne = float(self.searchForValue(data, "vgx"))
            searchTwo = float(self.searchForValue(data, "vgy"))
            resultant = (searchOne ** 2 + searchTwo ** 2) ** 0.5
            return resultant

    def searchForValue(self, data, searchTerm):
        for d in data:
            term = d.split(":")[0]
            if term == searchTerm:
                return d.split(":")[1]
            
    def checkIfFaceDetected(self):
        if self.FrameProcessor.faceCurrentlyDetected:
            return True
        else:
            return False

    ### BACKGROUND / BATTERY LOG / TELEMETRY ###

    def startBatteryLogThread(self): # Begin the background thread for logging the drone's current battery level.
        self.logBatteryThread = threading.Thread(target=self.batteryLogThread)
        self.logBatteryThread.daemon = True
        self.logBattery = True
        self.logBatteryThread.start()

    def batteryLogThread(self): # Repeatedly receives the drone's current battery level and emits it for display.
        while self.logBattery:
            batteryLevel = self.readBattery(logMessage=False)
            if batteryLevel:
                try:
                    self.updateBatteryReading.emit(int(batteryLevel))
                except ValueError:
                    continue
            time.sleep(5)
    
    def startTelThread(self): # Begin the telemetry thread, if a socket exists.
        if self.socket:
            self.telemetryRec = True
            self.telThread = threading.Thread(target=self.getStateThread)
            self.telThread.daemon = True
            self.telThread.start()

    def getStateThread(self): # Repeatedly receive the telemetry data from the telemetry socket.
        while self.telemetryRec:
            resp = self.receiveState()
            self.telemetryRecieved.emit(resp)

    ### SEQUENCE COMMUNICATION ###

    def startFaceDetectedThread(self): # Start thread for sending the 'On Face Detected' commands.
        if not self.detectFaceThreadRunning:
            self.detectFaceThreadRunning = True
            self.faceDetectedThread = threading.Thread(target=self.sendSequences, args=(self.faceDetectedInstructions,))
            self.faceDetectedThread.daemon = True
            self.faceDetectedThread.start()

    def startKeyPressThread(self): # Start thread for sending the 'On Spacebar Press' commands.
        self.keyPressTransmissionThread = threading.Thread(target=self.sendSequences, args=(self.keyPressInstructions,))
        self.keyPressTransmissionThread.daemon = True
        self.keyPressTransmissionThread.start()

    def startTransmissionThread(self): # Start thread for sending the 'On Start' commands.
        self.transmissionThread = threading.Thread(target=self.sendSequences, args=(self.activeExecInstructions,))
        self.transmissionThread.daemon = True
        self.transmissionThread.start()

    def recieveCommandSequences(self, sequences):
        '''Recieves the list of command sequences from the GUI
        Checks the first block for each sequence and adds subsequent blocks into the correct list for sending.
        '''
        for blockList in sequences:
            blockType = blockList[0].blockType
            blockList = self.expandRepeatBlocks(blockList)
            if blockType == "On Start":
                self.activeExecInstructions.extend(blockList)
            elif blockType == "On Spacebar Press":
                self.keyPressInstructions.extend(blockList)
            elif blockType == "On Face Detected":
                self.faceDetectedInstructions.extend(blockList)

    def expandRepeatBlocks(self, blockList):
        '''If the sequences contain a 'repeat for' block, the sequence needs to be expanded.
        This is done recursively, by repeatedly expanding any repeat blocks that get encountered.
        '''
        i = 0
        while i < len(blockList):
            if blockList[i].blockType == "Repeat": # If a repeat block is encoutnered
                count = blockList[i].repEnd.repCount - 1 # Get the number of times the blocks should be repeated
                repeatedCommands = blockList[i].compileRepeatingBlocks() # compile the list of repeated commands (up to the end repeat block)
                nRepeatedCommands = repeatedCommands * count # carry out the repeated commands for a set number of times
                blockList = blockList[:i] + nRepeatedCommands + blockList[i+1:] # replace the 'repeat for' block with the expanded sequence
                blockList = self.expandRepeatBlocks(blockList) # recursively check the new list for any nested repeat blocks
            i += 1
        return blockList

    def evaluateIfBlock(self, block):
        '''If the command sequence has an if block, it needs to be evaluated at tun time.
        Takes in the block as a parameter.
        '''
        conditionToValueMap = { # each if block condition has a corresponding method used to get the value needed.
            "Airspeed": self.readSpeed,
            "Battery level": self.readBattery,
            "Horizontal velocity": self.readValueFromTelemetry,
            "Vertical velocity": self.readValueFromTelemetry,
            "Time of flight": self.readFlightTime,
            "Altitude": self.readValueFromTelemetry,
            "Face detected": self.checkIfFaceDetected
        }
        operatorToValueMap = {
            "Greater Than": ">",
            "Less Than": "<",
            "Equal To": "==",
        }

        if not block.operator or not block.firstCondition or not block.secondCondition:
            return False
        conditionOne = block.firstCondition
        conditionTwo = block.secondCondition
        operator = operatorToValueMap[block.operator]

        firstValue = conditionToValueMap[conditionOne] # Identify the correct function needed to get the data value
        if firstValue == self.readValueFromTelemetry:
            firstValue = firstValue(conditionOne) # Call the function passing in the required telemetry item
        else:
            firstValue = firstValue() # Just call the specific function as normal
        
        if firstValue:
            secondValue = conditionTwo
            condition = f"{firstValue} {operator} {secondValue}"
            return eval(condition) # Return whether the if block evaluates to true or false
        
    def manualCopy(self, objList): # Takes a command sequence and returns a copy of it
        arr = []
        for obj in objList:
            arr.append(obj)
        return arr

    def sendSequences(self, instructionsSequence):
        '''Takes a sequence of commands as a list and sends each one to the drone, taking the command list as a parameter.
        This algorithm handles logic blocks and blocks that don't have commands to send.
        A copy of the instruction sequence is made and gets restored once the sequence has run.
        A time delay of 2 seconds is included between the sending of commands.
        '''
        instructionsSequenceCopy = self.manualCopy(instructionsSequence)
        if instructionsSequenceCopy != []:
            for cmd in instructionsSequenceCopy:
                if cmd.blockType == "Wait": # Handling of wait blocks
                    time.sleep(cmd.waitTime)
                elif cmd.blockType == "If": # Handling of if blocks
                    branchTrue = self.evaluateIfBlock(cmd)
                    if branchTrue:
                        elseBlock = cmd.elseBlock
                        nextB = elseBlock.nextBlock
                        while nextB != cmd.endBlock and nextB is not None:
                            instructionsSequenceCopy.remove(nextB)
                            nextB = nextB.nextBlock
                        instructionsSequenceCopy.remove(elseBlock)
                    else:
                        nextB = cmd.nextBlock
                        while nextB != cmd.elseBlock and nextB is not None:
                            print(nextB.blockType)
                            instructionsSequenceCopy.remove(nextB)
                            nextB = nextB.nextBlock
                else: # Every other block
                    nonSendList = { # If the block does not have a command handle it
                        "Take Photo": self.FrameProcessor.takePhoto,
                        "Camera Toggle":  self.FrameProcessor.cameraToggle,
                        "Start Recording": self.FrameProcessor.startRecording,
                        "Stop Recording": self.FrameProcessor.stopRecording,
                        "Face Detection Toggle": self.FrameProcessor.toggleFaceDetect,
                    }
                    if cmd.blockType in nonSendList: # The block has a more complex command that will be handled
                        action = nonSendList.get(cmd.blockType, None)
                        action()
                    elif cmd.droneCommand:
                        for i in range(2): # Send the command 2 times to ensure it gets through
                            self.send(cmd.droneCommand)
                            rec = self.receive()
                            time.sleep(0.1)
                    else:
                        continue # If the block does not have a command, skip it (like on start, endif etc.)

                time.sleep(4) # Wait 4 seconds before sending the next command. NOTE: This is gives the drone time to process the command

    def clearActiveSequences(self):
        '''Clear the instruction sequences permanently
        '''
        self.activeExecInstructions = []
        self.keyPressInstructions = []
        self.faceDetectedInstructions = []
        self.detectFaceThreadRunning = False