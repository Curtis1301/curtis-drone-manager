from PySide6.QtWidgets import (
    QLabel, QSplitter, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTabWidget, QGraphicsScene, QGraphicsView, QGroupBox, QGridLayout, 
    QInputDialog
)
from PySide6.QtCore import Qt, Signal, QMimeData, QPointF, Slot
from PySide6.QtGui import QPixmap, QDrag, QColor

from components.blocks import *

class WorkspaceView(QWidget):
    updateSequenceCommands = Signal()
    def __init__(self, database, userID):
        super().__init__()
        self.database = database
        self.userID = userID
        self.droneID = None
        self.logicBlocks = ["If/Else", "Wait", "Repeat For"] 
        self.blockTypes = { 
            "Event": ["On Start", "On Spacebar Press"],
            "Altitude": ["Takeoff", "Land", "Ascend","Descend","Hover","Flip"],
            "Orientation": ["Forwards","Backwards","Left","Right","Yaw Left","Yaw Right"],
            "Camera": ["Camera Toggle", "Take Photo", "Start Recording", "Stop Recording"],
            "Face Detection": ["On Face Detected", "Face Detection Toggle"],
        }
        
        logicColour = QColor("#E67E22")
        eventColour = QColor("#C94C4C")
        altitudeColour = QColor("#F5A623")
        orientationColour = QColor("#27AE60")
        cameraColour = QColor("#2A9D8F")
        facialColour = QColor("#A67BC5")
        self.blockToCommandMap = { 
            "If/Else": [None, logicColour],
            "Wait": [None, logicColour],
            "Repeat For": [None, logicColour],
            "On Start": [None, eventColour],
            "On Spacebar Press": [None, eventColour],
            "Takeoff": [NotImplemented, altitudeColour],
            "Land": [NotImplemented, altitudeColour],
            "Ascend": [NotImplemented, altitudeColour],
            "Descend": [NotImplemented, altitudeColour],
            "Hover": [NotImplemented, altitudeColour],
            "Flip": [NotImplemented, altitudeColour],
            "Forwards": [NotImplemented, orientationColour],
            "Backwards": [NotImplemented, orientationColour],
            "Left": [NotImplemented, orientationColour],
            "Right": [NotImplemented, orientationColour],
            "Yaw Left": [NotImplemented, orientationColour],
            "Yaw Right": [NotImplemented, orientationColour],
            "Camera Toggle": [None, cameraColour],
            "Take Photo": [None, cameraColour],
            "Start Recording": [None, cameraColour],
            "Stop Recording": [None, cameraColour],
            "Face Detection Toggle": [None, facialColour],
            "On Face Detected": [None, facialColour],
        }

        self.initUI()

    @Slot(str) # triggered when the user sets a drone
    def initDroneCommands(self, droneName):
        query = "SELECT droneID FROM Drones WHERE userID = ? AND droneName = ?"
        result = self.database.fetchQuery(query, (self.userID, droneName,))
        if result:
            self.droneID = result[0][0]
            query = "SELECT * FROM Commands WHERE droneID = ?"
            result = self.database.fetchQuery(query, (self.droneID,))
            if result:
                commandSet = result[0][1:] # get the pure list of commands without the droneID
                upadateList = ["Takeoff", "Land", "Ascend", "Descend", "Hover", "Flip", "Forwards", "Backwards", "Left", "Right", "Yaw Left", "Yaw Right"]
                commandCounter = 0
                for block, values in self.blockToCommandMap.items():
                    if block in upadateList:
                        colour = values[1]
                        command = commandSet[commandCounter]
                        if block not in ["Takeoff", "Land", "Hover"]:
                            command = f"{command} %s"
                        self.blockToCommandMap[block] = [command, colour]
                        commandCounter += 1 

                self.updateSequenceCommands.emit()

    def initUI(self):
        overallLayout = QVBoxLayout(self) 
        splitter = QSplitter(Qt.Vertical) 
        splitter.setHandleWidth(0)
        
        self.blockSelector = QTabWidget(splitter) 
        tabLabels = ["Event","Altitude","Orientation","Camera","Face Detection"] 
        for lbl in tabLabels:
            self.blockSelector.addTab(self.createBlockMenuWidget(lbl), lbl) 

        self.blockSpace = BlockSpace(cmdMap=self.blockToCommandMap) 
        self.updateSequenceCommands.connect(self.blockSpace.updateDroneCommands)
        self.view = BlockView(scene=self.blockSpace) 
        splitter.addWidget(self.view) 

        overallLayout.addWidget(splitter) 

    def createBlockMenuWidget(self, label): 
        splitter = QSplitter(Qt.Horizontal) 
        splitter.setHandleWidth(0) 

        logic = QGroupBox("Logic Commands")
        logic.setAlignment(Qt.AlignCenter)
        logicLayout = QGridLayout(logic) 
    
        for i, logicText in enumerate(self.logicBlocks):
            btn = BlockButton(logicText)
            btn.setProperty("class",f"blockButton logicBtn")
            logicLayout.addWidget(btn, i, 0) 

        commands = QGroupBox(label) 
        commands.setAlignment(Qt.AlignCenter)
        commandLayout = QGridLayout(commands) 

        for i, text in enumerate(self.blockTypes[label]): 
            blockButton = BlockButton(text)
            label = label if label != "Face Detection" else "Face" 
            blockButton.setProperty("class",f"blockButton {label}")
            commandLayout.addWidget(blockButton,i%2 ,i//2) 

        splitter.addWidget(logic) 
        splitter.addWidget(commands) 

        return splitter

class BlockButton(QPushButton): 
    def __init__(self, txt):
        super().__init__()
        self.setText(txt) 

    def mousePressEvent(self, event): 
        if event.buttons() == Qt.MouseButton.LeftButton:
            drag = QDrag(self) 
            mime = QMimeData() 
            mime.setText(self.text()) 
            drag.setMimeData(mime) 

            pixmap = QPixmap(self.size()) 
            self.render(pixmap) 
            drag.setPixmap(pixmap) 
            drag.setHotSpot(pixmap.rect().center()) 

            drag.exec(Qt.DropAction.MoveAction) 
            
class BlockView(QGraphicsView): 
    sequences = Signal(list)
    def __init__(self, scene):
        super().__init__(scene)
        self.scaleFactor = 1 
        self.mainLayout = QHBoxLayout(self) 
        self.setDragMode(QGraphicsView.ScrollHandDrag) 
        self.setAcceptDrops(True) 
        self.createButtons() 
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate) 

    def createButtons(self):
        self.btnContainer = QWidget() 
        vLayout = QVBoxLayout(self.btnContainer) 

        hLayout = QHBoxLayout() 

        self.confirmButton = QPushButton("CONFIRM") 
        self.confirmButton.setProperty("class","workspaceButton")
        self.confirmButton.clicked.connect(self.confirm)
        hLayout.addWidget(self.confirmButton, 3)

        self.clearBtn = QPushButton("Clear")
        self.clearBtn.setProperty("class","workspaceButton")
        self.clearBtn.clicked.connect(self.clear)
        hLayout.addWidget(self.clearBtn, 1) 
        vLayout.addLayout(hLayout) 

        infoLabel = QLabel("Double click on a block to change its command")
        vLayout.addWidget(infoLabel) 

        self.mainLayout.addWidget(self.btnContainer, alignment=Qt.AlignRight | Qt.AlignBottom) 
    
    def confirm(self): 
        sequences = self.scene().sequences 
        if sequences == []: return
        for s in sequences: 
            print("--- sequence ---")
            current = s[0]
            while current is not None:
                print(current.blockType)
                current = current.nextBlock
            print("--- end sequence ---")

        self.sequences.emit(sequences) 
        
    def clear(self): 
        for item in self.items():
            self.scene().removeItem(item)
        self.scene().sequences = [] 

    def zoomIn(self): 
        if self.scaleFactor <= 2:
            self.scale(2,2) 
            self.scaleFactor *= 2 

    def zoomOut(self): 
        if self.scaleFactor >= 0.25:
            self.scale(0.5,0.5) 
            self.scaleFactor *= 0.5 

    def wheelEvent(self, event): 
        pixels = event.angleDelta().y() 
        if pixels > 0: self.zoomIn() 
        if pixels < 0: self.zoomOut() 
        
class BlockSpace(QGraphicsScene): 
    def __init__(self, cmdMap): 
        super().__init__()
        self.cmdMap = cmdMap 
        self.sequences = [] 
        self.draggedItemPos = QPointF(0,0) 
        self.deadZone = 10
        self.blockOverlap = 0.1 
        self.setSceneRect(-1500,-1500,2000,2000) 
        self.numericCommands = [["Forwards","cm"],["Backwards","cm"], 
            ["Left","cm"],["Right","cm"],
            ["Yaw Left","degrees"],["Yaw Right","degrees"],
            ["Ascend","cm"],["Descend","cm"]]

    def dragEnterEvent(self, event): 
        if event.mimeData().hasText(): 
            event.acceptProposedAction() 

    def dragMoveEvent(self, event): 
        event.acceptProposedAction() 

    def dropEvent(self, event): 
        if event.mimeData().hasText(): 
            scenePos = event.scenePos() 
            blockType = event.mimeData().text() 
            command = self.getCommand(blockType) 
            colour = self.getBlockColour(blockType) 

            if blockType == "Wait": 
                item = WaitBlock("Wait", command, scenePos, colour) 
                self.addItem(item)
                self.updateNewBlock(item) 
            elif blockType == "Repeat For": 
                repeatBlock = RepeatBlock("Repeat", command, scenePos, colour) 
                endBlock = EndRepeat("EndRepeat", command, scenePos, colour) 
                endBlock.repBlock = repeatBlock 
                repeatBlock.repEnd = endBlock

                self.addItem(repeatBlock)
                self.updateNewBlock(repeatBlock) 
                endBlock.setPos(repeatBlock.scenePos())
                self.addItem(endBlock)
                self.updateNewBlock(endBlock)
            elif blockType == "If/Else": 
                ifBlock = IfBlock("If", command, scenePos, colour)
                elseBlock = ElseBlock("Else", command, scenePos, colour)
                endIfBlock = EndIfBlock("End If", command, scenePos, colour)

                ifBlock.elseBlock = elseBlock 
                ifBlock.endBlock = endIfBlock

                elseBlock.ifBlock = ifBlock 
                elseBlock.endBlock = endIfBlock

                endIfBlock.ifBlock = ifBlock 
                endIfBlock.elseBlock = elseBlock

                self.addItem(ifBlock) 
                self.updateNewBlock(ifBlock)
                elseBlock.setPos(ifBlock.scenePos())
                self.addItem(elseBlock)
                self.updateNewBlock(elseBlock)
                endIfBlock.setPos((elseBlock.scenePos()))
                self.addItem(endIfBlock)
                self.updateNewBlock(endIfBlock)
            else: 
                item = BlockItem(blockType, command, scenePos, colour)
                self.addItem(item)
                self.updateNewBlock(item)

            event.acceptProposedAction()

    def mousePressEvent(self, event):
        item = self.getItemAtPos(event.scenePos()) 
        if event.buttons() == Qt.MouseButton.RightButton: 
            if item:
                if item.blockType == "Repeat": 
                    self.removeRepeatStatement(item, item.repEnd)
                elif item.blockType == "EndRepeat":
                    self.removeRepeatStatement(item.repBlock, item)
                elif item.blockType == "If": 
                    self.removeIfStatement(item, item.elseBlock, item.endBlock)
                elif item.blockType == "Else": 
                    self.removeIfStatement(item.ifBlock, item, item.endBlock)
                elif item.blockType == "End If": 
                    self.removeIfStatement(item.ifBlock, item.elseBlock, item)
                else:
                    self.removeFoundItem(item)
        elif event.buttons() == Qt.MouseButton.LeftButton: 
            self.draggedItemPos = event.scenePos() 
            if item:
                if item.blockType in ["EndRepeat", "Else", "End If"]: 
                    event.ignore()
                    return
                item.setZValue(1) 
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event): 
        if self.checkDeadZone(event): 
            event.ignore() 
        else:
            super().mouseMoveEvent(event) 

    def mouseReleaseEvent(self, event): 
        if event.button() == Qt.MouseButton.LeftButton: 
            item = self.getItemAtPos(event.scenePos()) 
            delta = event.scenePos() - self.draggedItemPos 
            if item and delta != QPointF(0,0): 
                if item.blockType == "Repeat": 
                    self.unindentRepeatStatement(item)
                elif item.blockType == "If": 
                    self.unindentIfStatement(item)
                item.setZValue(0) 
                if item.previousBlock:
                    if item.collidesWithItem(item.previousBlock): 
                        self.alignSequence(item)
                self.updateNewBlock(item) 
    
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event): 
        item = self.getItemAtPos(event.scenePos()) 
        try:
            if item:
                command = item.droneCommand 
                if item.blockType == "EndRepeat": 
                    newCondition, ok = QInputDialog.getInt(None, "Set Repeat Count", f"Current Number of Repeats: {item.repCount}", item.repCount, 1, 99) 
                    if ok and newCondition > 0:
                        item.setRepCount(newCondition)
                elif item.blockType == "If": 
                    newConditionDialog = SetNewIfCondition(item) 
                    newConditionDialog.exec() 
                elif item.blockType == "Wait": 
                    newWaitTime, ok = QInputDialog.getInt(None, "Set Wait Time", f"Current Wait Time: {item.waitTime} seconds", item.waitTime, 2, 99) 
                    if ok and newWaitTime >= 2:
                        item.setWaitTime(newWaitTime) 
                elif item.blockType == "Flip": 
                    directionDict = {"Forwards": "f", "Backwards": "b", "Left": "l", "Right": "r"} 
                    cmd = command.split(" ")[0] 
                    val = command.split(" ")[1] if command.split(" ")[1] != "%s" else "f"
                    newDirection, ok = QInputDialog.getItem(None, "Set Flip Direction", f"Please Select a Direction:", ["Forwards","Backwards","Left","Right"], 10, False) 
                    if ok:
                        cmd = f"{cmd} {directionDict[newDirection]}" 
                        label = f"{item.blockType} {newDirection}" 
                        item.updateDroneCommand(cmd, label) 
                else: 
                    for blockData in self.numericCommands: 
                        if blockData[0] == item.blockType: 
                            unit = blockData[1]
                            cmd = command.split(" ")[0] 
                            val = command.split(" ")[1] if command.split(" ")[1] != "%s" else 20 
                            newCommandValue, ok = QInputDialog.getInt(None, "Set Command", f"Current Command: {item.blockType} (in {unit})", int(val), 20, 360) 
                            if ok:
                                cmd = f"{cmd} {str(newCommandValue)}"
                                label = f"{item.blockType} {str(newCommandValue)} {unit}"
                                item.updateDroneCommand(cmd, label)

        except AttributeError:
            pass
        
        super().mouseDoubleClickEvent(event) 

    def connectToNeighbour(self, item, neighbour): 
        if neighbour.nextBlock:
            neighbour.nextBlock.setPreviousBlock(item) 
            item.setNextBlock(neighbour.nextBlock) 
        else:
            item.setNextBlock(None) 

        item.setPreviousBlock(neighbour) 
        neighbour.setNextBlock(item) 

        for seq in self.sequences: 
            for i, block in enumerate(seq):
                if block == neighbour:
                    seq.insert(i+1, item) 
                    break

        item.indentLevel = neighbour.indentLevel 
        
        if item.previousBlock.blockType == "If" and item.blockType != "Else":
            item.indentLevel = item.previousBlock.indentLevel + 1 
        elif item.previousBlock.blockType == "Else" and item.blockType != "End If":
            item.indentLevel = item.previousBlock.indentLevel + 1
        elif item.previousBlock.blockType == "Repeat" and item.blockType != "EndRepeat":
            item.indentLevel = item.previousBlock.indentLevel + 1
        
        self.alignSequence(item) 

    def updateNewBlock(self, item): 
        neighbours = item.collidingItems() 
        for n in neighbours:
            if isinstance(n, ConditionText): 
                neighbours.remove(n) 

        self.removeFromSequence(item)
        self.alignSequence(item.previousBlock)
        self.removalUpdate(item)

        if neighbours:
            previous = min(neighbours, key=lambda x: (x.pos() - item.pos()).manhattanLength()) 
            if previous:
                if isinstance(previous, ConditionText):
                    previous = previous.parentItem() 
                print(f"Connecting {item.blockType} to {previous.blockType}")
                self.connectToNeighbour(item, previous) 
        else:
            
            item.setPreviousBlock(None)
            item.setNextBlock(None)
            self.sequences.append([item])
            item.indentLevel = 0

        self.moveDependentBlocks(item) 

    def removeFoundItem(self, item):
        self.removeItem(item) 
        self.removeFromSequence(item) 
        if item.nextBlock:
            self.alignSequence(item.nextBlock) 
        self.removalUpdate(item) 

    def getItemAtPos(self, pos): 
        item = self.itemAt(pos, self.views()[0].transform()) 
        if item:
            if isinstance(item, ConditionText):
                item = item.parentItem() 
        return item

    def unindentRepeatStatement(self, repeatBlock): 
        dependentBlocks = repeatBlock.compileRepeatingBlocks() 

        for block in dependentBlocks: 
            block.indentLevel -= 1 

    def removeRepeatStatement(self, pRepeatBlock, endRepeatBlock):
        self.unindentRepeatStatement(pRepeatBlock) 
        
        self.removeFoundItem(pRepeatBlock) 
        self.removeFoundItem(endRepeatBlock) 

    def unindentIfStatement(self, ifBLock):
        trueBlocks = ifBLock.compileTrueBranch() 
        falseBlocks = ifBLock.compileFalseBranch() 

        for tBlock in trueBlocks:
            tBlock.indentLevel -= 1
        for fBlock in falseBlocks:
            fBlock.indentLevel -= 1

    def removeIfStatement(self, pIfBLock, elseBlock, endBlock):
        self.unindentIfStatement(pIfBLock) 
        self.removeFoundItem(pIfBLock) 
        self.removeFoundItem(elseBlock) 
        self.removeFoundItem(endBlock) 
        
    def checkDeadZone(self, event):
        delta = event.scenePos() - self.draggedItemPos 
        if abs(delta.x()) < self.deadZone and abs(delta.y()) < self.deadZone: 
            return True
        else:
            return False

    def getBlockColour(self, blockType):
        return self.cmdMap[blockType][1] 

    @Slot()
    def updateDroneCommands(self):
        for seq in self.sequences:
            for block in seq:
                command = self.cmdMap.get(block.blockType, None)
                if command: 
                    command = command[0]
                    block.updateDroneCommand(command, block.blockType)

    def getCommand(self, txt): 
        if txt in self.cmdMap:
            print(f"setting the command for blocktype {txt}, command set to {self.cmdMap[txt][0]}")
            return self.cmdMap[txt][0]
        else:
            return None

    def alignSequence(self, item): 
        for seq in self.sequences: 
            if item in seq: 
                firstBlock = seq[0] 
                for i, block in enumerate(seq[1:]): 
                    block.setPos(firstBlock.scenePos() + QPointF((block.indentLevel * 20), (i+1) * (block.height - self.blockOverlap))) 
                return

    def removalUpdate(self, item): 
        if item.nextBlock:
            item.nextBlock.setPreviousBlock(item.previousBlock) 
        if item.previousBlock:
            item.previousBlock.setNextBlock(item.nextBlock) 

    def removeFromSequence(self, item): 
        for seq in self.sequences:
            if item in seq:
                seq.remove(item)
                if seq == []: self.sequences.remove(seq) 

    def moveDependentBlocks(self, item):
        if item.blockType == "Repeat": 
            if item.repEnd:
                item.repEnd.setPos(item.scenePos()) 
                self.updateNewBlock(item.repEnd) 
        elif item.blockType == "If": 
            if item.elseBlock:
                item.elseBlock.setPos(item.scenePos()) 
                self.updateNewBlock(item.elseBlock) 
            if item.endBlock:
                item.endBlock.setPos(item.scenePos() + QPointF(0, item.height)) 
                self.updateNewBlock(item.endBlock) 