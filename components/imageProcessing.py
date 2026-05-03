import queue
import threading
import cv2
import os

from PySide6.QtCore import Signal, QObject, Slot
from PySide6.QtGui import QImage

class FrameProcessor(QObject):
    faceDetected = Signal()
    processedImage = Signal(QImage) 
    def __init__(self, database, userID):
        super().__init__()
        self.database = database
        self.userID = userID
        self.videoURL = None 
        self.DroneController = None

        self.frameQueue = queue.Queue(maxsize=5) 
        self.captureThreadRunning = False 
        self.displayThreadRunning = False 
        self.isRecording = False
        self.cap = None
        self.videoWriter = None

        self.classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml') 
        self.detectFaces = True
        self.faceCurrentlyDetected = False

        query = "SELECT username FROM Users WHERE userID = ?"
        result = self.database.fetchQuery(query, (self.userID,))
        if result:
            self.username = result[0][0]

    def setDroneController(self, controller): 
        self.DroneController = controller

    @Slot(str) 
    def setDrone(self, droneName):
        if droneName == "No Drone Selected":
            return
        query = "SELECT droneIP, videoPort FROM Drones WHERE userID = ? AND droneName = ?"
        results = self.database.fetchQuery(query, (self.userID, droneName,))
        if results:
            droneIP = results[0][0]
            videoPort = results[0][1]
            url = f"udp://{droneIP}:{videoPort}"
            self.videoURL = url

        else:
            self.videoURL = None

    def stop(self): 
        self.displayThreadRunning = False 
        self.captureThreadRunning = False 
        if self.cap:
            self.cap.release() 
        self.DroneController.streamOff() 

    def startCapThread(self): 
        if not self.captureThreadRunning:
            self.DroneController.streamOn() 
            self.captureThreadRunning = True 
            self.capThread = threading.Thread(target=self.captureFrames) 
            self.capThread.daemon = True 
            self.capThread.start() 

    def captureFrames(self):
        if self.videoURL:
            try:
                self.cap = cv2.VideoCapture(self.videoURL) 
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
            except cv2.error as e:
                return e

            while self.captureThreadRunning: 
                try:
                    ret, frame = self.cap.read() 
                    if not ret:
                        continue 
                    if self.frameQueue.full(): 
                        self.frameQueue.get() 
                    self.frameQueue.put(frame) 

                    if self.isRecording:
                        self.videoWriter.write(frame) 
                except cv2.error:
                    self.captureThreadRunning = False

    def setVideoWriter(self):
        if self.cap:
            frameWidth = int(self.cap.get(3)) 
            frameHeight = int(self.cap.get(4)) 
            fourccCode = cv2.VideoWriter_fourcc(*'mp4v')

            fileIndex = 1
            while os.path.exists(f"media/recording{self.username}{fileIndex}.mp4"):
                fileIndex += 1

            filename = f"media/recording{self.username}{fileIndex}.mp4"
            self.videoWriter = cv2.VideoWriter(filename, fourccCode, 24, (frameWidth,  frameHeight), ) 

    def startDisplayThread(self): 
        self.displayThreadRunning = True
        self.dThread = threading.Thread(target=self.displayThread) 
        self.dThread.daemon = True 
        self.dThread.start()

    def displayThread(self):
        while self.displayThreadRunning: 
            try:
                if self.frameQueue.qsize() > 0: 
                    frame = self.frameQueue.get() 
                    frame = self.faceDetectionCheck(frame) 

                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 

                    converted = QImage(image.data, image.shape[1], image.shape[0], QImage.Format_RGB888) 
                    self.processedImage.emit(converted) 
                    
                if cv2.waitKey(1) == ord('q'): 
                    break
            except Exception:
                continue

    def takePhoto(self):
        frame = self.frameQueue.get() 
        frame = self.faceDetectionCheck(frame) 

        fileIndex = 1
        while os.path.exists(f"media/img{self.username}{fileIndex}.png"):
            fileIndex += 1

        cv2.imwrite(f"media/img{self.username}{fileIndex}.png", frame) 

    def faceDetectionCheck(self, frame):
        if frame is not None and self.detectFaces: 
            grayImage = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
            face = self.classifier.detectMultiScale( 
                grayImage, scaleFactor=1.1, minNeighbors=5,minSize=(40,40)
                )
            
            if len(face) != 0:
                self.faceCurrentlyDetected = True
                self.faceDetected.emit()
            else:
                self.faceCurrentlyDetected = False

            for (x,y,w,h) in face: 
                cv2.rectangle(frame, (x,y), (x + w, y + h), (0, 255, 0), 4) 

        return frame

    def startRecording(self):
        self.setVideoWriter()
        self.isRecording = True

    def stopRecording(self):
        if self.videoWriter:
            self.videoWriter.release()
            self.videoWriter = None
        self.isRecording = False 

    def cameraToggle(self):
        if self.captureThreadRunning:
            self.stop() 
        else:
            self.startCapThread() 
            self.startDisplayThread() 

    def toggleFaceDetect(self):
        if self.detectFaces: 
            self.detectFaces = False 
        else: 
            self.detectFaces = True 
