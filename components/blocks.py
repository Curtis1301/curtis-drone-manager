from PySide6.QtWidgets import (QGraphicsItem, QGraphicsTextItem, 
QDialog, QHBoxLayout, QComboBox, QLabel, QSpinBox, QVBoxLayout, QPushButton)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QBrush, QPen, QFont

class BlockItem(QGraphicsItem): # custom graphics item for the actual block itself
    def __init__(self, txt, cmd, pos, colour, units=None):
        super().__init__()
        self.width = 150
        self.height = 50
        self.colour = colour
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setPos(pos - QPointF(self.width / 2, self.height / 2))
        self.indentLevel = 0
        self.blockType = txt
        self.droneCommand = cmd
        self.nextBlock = None
        self.previousBlock = None
        self.units = units

        if self.blockType not in ["EndRepeat", "If", "Wait"]: # draw the block text, if not a special case
            self.conditionText = ConditionText(self.blockType, self) 
            
    def boundingRect(self):
        return QRectF(0,0,self.width,self.height)
    
    def paint(self, painter, option, widget):
        rect = self.boundingRect()
        painter.setBrush(QBrush(self.colour))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(rect)

    def setNextBlock(self, pBlock):
        self.nextBlock = pBlock
    
    def setPreviousBlock(self, pBlock):
        self.previousBlock = pBlock

    def updateDroneCommand(self, cmd, label):
        self.droneCommand = cmd
        self.conditionText.setHtml(f"<div style='text-align:center;'>{label}</div>")
        self.conditionText.updatePosition()
        
class WaitBlock(BlockItem):
    def __init__(self, txt, cmd, pos, colour):
        super().__init__(txt, cmd, pos, colour)
        self.waitTime = 5 # intiial fixed amount used for debugging and testing

        self.conditionText = ConditionText(f"Wait for {self.waitTime} seconds", self)
 
    def setWaitTime(self, pTime):
        self.waitTime = pTime
        self.conditionText.setPlainText(f"")
        self.conditionText.setHtml(f"<div style='text-align:center;'>Wait for {self.waitTime} seconds</div>")
        self.conditionText.updatePosition()

class IfBlock(BlockItem):
    def __init__(self, txt, cmd, pos, colour):
        super().__init__(txt, cmd, pos, colour)
        self.elseBlock = None
        self.endBlock = None

        self.conditionText = ConditionText(f"If (No condition set)", self)

        self.firstCondition = None
        self.secondCondition = None
        self.operator = None
    
    def setCondition(self, first, second, operator, text):
        self.firstCondition = first
        self.secondCondition = second
        self.operator = operator
        self.conditionText.setHtml(f"<div style='text-align:center;'>{text}</div>")
        self.conditionText.updatePosition()

    def compileTrueBranch(self):
        trueBlocks = []
        next = self.nextBlock
        while next != self.elseBlock and next is not None:
            trueBlocks.append(next)
            next = next.nextBlock
        return trueBlocks

    def compileFalseBranch(self):
        falseBlocks = []
        next = self.elseBlock.nextBlock
        while next != self.endBlock and next is not None:
            falseBlocks.append(next)
            next = next.nextBlock
        return falseBlocks

class ElseBlock(BlockItem):
    def __init__(self, txt, cmd, pos, colour):
        super().__init__(txt, cmd, pos, colour)
        self.ifBlock = None
        self.endBlock = None

class EndIfBlock(BlockItem):
    def __init__(self, txt, cmd, pos, colour):
        super().__init__(txt, cmd, pos, colour)
        self.ifBlock = None
        self.elseBlock = None

class RepeatBlock(BlockItem):
    def __init__(self, txt, cmd, pos, colour):
        super().__init__(txt, cmd, pos, colour)
        self.repEnd = None # Points to the block that contains the loop counter / ends the loop

    def compileRepeatingBlocks(self):
        repeatList = []
        next = self.nextBlock
        while next != self.repEnd and next is not None:
            repeatList.append(next)
            next = next.nextBlock
        return repeatList # excluding the terminating block itself

class EndRepeat(BlockItem):
    def __init__(self, txt, cmd, pos, colour):
        super().__init__(txt, cmd, pos, colour)
        self.repBlock = None
        self.repCount = 2 # No of times the code will be repeated

        self.conditionText = ConditionText(f"For {self.repCount} Times", self)

    def setRepCount(self, pCount): # Sets the number of times the code will be repeated
        self.repCount = pCount
        self.conditionText.setHtml(f"<div style='text-align:center;'>For {self.repCount} Times</div>")
        self.conditionText.updatePosition()

class ConditionText(QGraphicsTextItem): # Acts as the text for the logic blocks
    def __init__(self, text, parent):
        super().__init__(text)
        self.setFont(QFont("Calibri", 11))
        self.setTextWidth(140)
        self.setHtml(f"<div style='text-align:center;'>{text}</div>")
         
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setParentItem(parent)
        self.updatePosition()

    def updatePosition(self):
        width = self.boundingRect().width()
        height = self.boundingRect().height()
        parentWidth = self.parentItem().boundingRect().width()
        parentHeight = self.parentItem().boundingRect().height()

        self.setPos((parentWidth - width) / 2, (parentHeight - height) / 2)

class SetNewIfCondition(QDialog):
    def __init__(self, ifBlock):
        super().__init__()
        self.ifBlock = ifBlock
        self.operators = ["Equal To", "Less Than", "Greater Than"]
        self.setWindowTitle("Change the If condition")
        mainLayout = QVBoxLayout(self)
        layout = QHBoxLayout()
        mainLayout.addLayout(layout)

        lbl1 = QLabel("If")
        lbl1.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl1)
        
        self.firstCondition = QComboBox()
        self.firstCondition.addItems(["Altitude", "Airspeed", "Horizontal velocity", "Vertical velocity", "Time of flight", "Battery level", "Face detected"])
        self.firstCondition.currentIndexChanged.connect(self.firstConditionChanged)
        layout.addWidget(self.firstCondition)

        lbl2 = QLabel("is")
        lbl2.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl2)

        self.operatorSelect = QComboBox()
        self.operatorSelect.addItems(self.operators)
        layout.addWidget(self.operatorSelect)

        self.secondCondition = QSpinBox()
        self.secondCondition.setFixedWidth(100)
        self.secondCondition.setMinimum(1)
        self.secondCondition.setMaximum(999)
        self.secondCondition.setValue(10)
        layout.addWidget(self.secondCondition)

        self.unitLbl = QLabel("cm")
        self.unitLbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.unitLbl)

        conf = QPushButton("Confirm")
        conf.clicked.connect(self.confirmCondition)
        mainLayout.addWidget(conf)

    def confirmCondition(self):
        first = self.firstCondition.currentText()
        second = self.secondCondition.value()
        operator = self.operatorSelect.currentText()
        if first != "Face detected": # If the first condition is "Face detected" then the second condition is disabled
            txt = f"If {first} {operator} {second} {self.unitLbl.text()}"
            
            self.ifBlock.setCondition(first, second, operator, txt)
            self.ifBlock.conditionText.updatePosition()
        else:
            txt = f"If {first}"
            self.ifBlock.setCondition(first, None, None, txt)
            self.ifBlock.conditionText.updatePosition()

        self.close()
        self.ifBlock.scene().setFocus()

    def firstConditionChanged(self):
        first = self.firstCondition.currentText()
        units = {
            "Time of flight": "s",
            "Battery level": "%",
            "Face detected": "",
            "Airspeed": "cm/s",
            "Horizontal velocity": "cm/s",
            "Vertical velocity": "cm/s",
        }
        self.unitLbl.setText(units.get(first, "cm"))
        if first == "Face detected":
            self.secondCondition.setDisabled(True)
            self.operatorSelect.setDisabled(True)
        else:
            self.secondCondition.setDisabled(False)
            self.operatorSelect.setDisabled(False)