# v1.0.0

import base64
import json
import ssl
import time
import threading
import urllib

from krita import *

VERSION = 100

class Stablehorde(Extension):
   def __init__(self, parent):
      super().__init__(parent)

   def setup(self):
      pass

   def createActions(self, window):
      action = window.createAction("generate", "Stablehorde", "tools/scripts")
      action.triggered.connect(self.openDialog)

   def openDialog(self):
      dialog = Dialog()
      dialog.exec()

class Dialog(QDialog):
   def __init__(self):
      super().__init__(None)
      global worker

      settings = self.readSettings()

      self.setWindowTitle("Stablehorde")
      self.layout = QFormLayout()

      # Prompt Strength
      label = QLabel("Prompt Strength")
      slider = QSlider(Qt.Orientation.Horizontal, self)
      slider.setRange(0, 20)
      slider.setTickInterval(1)
      slider.setValue(settings["promptStrength"])
      self.promptStrength = slider
      labelPromptStrength = QLabel(str(self.promptStrength.value()))
      self.promptStrength.valueChanged.connect(lambda: labelPromptStrength.setText(str(self.promptStrength.value())))
      layout = QHBoxLayout()
      layout.addWidget(self.promptStrength)
      layout.addWidget(labelPromptStrength)
      container = QWidget()
      container.setLayout(layout)
      self.layout.addRow("Prompt Strength", container)

      # Steps
      slider = QSlider(Qt.Orientation.Horizontal, self)
      slider.setRange(10, 200)
      slider.setTickInterval(1)
      slider.setValue(settings["steps"])
      self.steps = slider
      labelSteps = QLabel(str(self.steps.value()))
      self.steps.valueChanged.connect(lambda: labelSteps.setText(str(self.steps.value())))
      layout = QHBoxLayout()
      layout.addWidget(self.steps)
      layout.addWidget(labelSteps)
      container = QWidget()
      container.setLayout(layout)
      self.layout.addRow("Steps", container)

      # Seed
      self.seed = QLineEdit()
      self.seed.setText(settings["seed"])
      self.layout.addRow("Seed (optional)", self.seed)

      # NSFW
      self.nsfw = QCheckBox()
      self.nsfw.setCheckState(settings["nsfw"])
      self.layout.addRow("NSFW",self.nsfw)

      # Prompt
      self.prompt = QTextEdit()
      self.prompt.setText(settings["prompt"])
      self.layout.addRow("Prompt", self.prompt)

      # API Key
      self.apikey = QLineEdit()
      self.apikey.setText(settings["apikey"])
      self.layout.addRow("API Key (optional)", self.apikey)

      # Max Wait
      slider = QSlider(Qt.Orientation.Horizontal, self)
      slider.setRange(1, 10)
      slider.setTickInterval(1)
      slider.setValue(settings["maxWait"])
      self.maxWait = slider
      labelMaxWait = QLabel(str(self.maxWait.value()))
      self.maxWait.valueChanged.connect(lambda: labelMaxWait.setText(str(self.maxWait.value())))
      layout = QHBoxLayout()
      layout.addWidget(self.maxWait)
      layout.addWidget(labelMaxWait)
      container = QWidget()
      container.setLayout(layout)
      self.layout.addRow("Max Wait (minutes)", container)

      # Status
      self.statusDisplay = QTextEdit()
      self.statusDisplay.setEnabled(False)
      self.layout.addRow("Status", self.statusDisplay)

      # Generate
      self.generateButton = QPushButton("Generate")
      self.generateButton.clicked.connect(self.generate)
      self.layout.addWidget(self.generateButton)

      # Space
      layout = QHBoxLayout()
      layout.addSpacing(50)
      container = QWidget()
      container.setLayout(layout)
      self.layout.addWidget(container)

      # Cancel
      cancelButton = QPushButton("Cancel")
      cancelButton.setFixedWidth(100)
      cancelButton.clicked.connect(self.cancelled)
      self.layout.addWidget(cancelButton)
      self.layout.setAlignment(cancelButton, Qt.AlignRight)

      self.setLayout(self.layout)
      self.resize(350, 300)

      update = utils.checkUpdate()

      if update["update"] is True:
         self.statusDisplay.setText(update["message"])

   def generate(self):
      doc = Application.activeDocument()

      if doc == None:
         utils.errorMessage("Please add a document with minimum size 512x512.", "For image generation a document with a layer is needed.")
         return
      else:
         self.writeSettings()
         self.setEnabledStatus(False)

         try:
            worker.generate(self)
         except Exception as ex:
            self.setEnabledStatus(True)
            self.statusDisplay.setText("An error occurred: " + str(ex))

   def readSettings(self):
      settings = Application.readSetting("Stablehorde", "Config", None)

      if not settings:
         settings = {
            "prompt": "",
            "promptStrength": 8,
            "steps": 50,
            "seed": "",
            "nsfw": 0,
            "apikey": "",
            "maxWait": 5
         }
      else:
         settings = json.loads(settings)

      return settings

   def writeSettings(self):
      settings = {
         "prompt": self.prompt.toPlainText(),
         "promptStrength": self.promptStrength.value(),
         "steps": int(self.steps.value()),
         "seed": self.seed.text(),
         "nsfw": self.nsfw.checkState(),
         "apikey": self.apikey.text(),
         "maxWait": self.maxWait.value()
      }

      settings = json.dumps(settings)
      Application.writeSetting ("Stablehorde", "Config", settings)

   def cancelled(self):
      global worker
      worker.cancel()
      self.writeSettings()
      self.close()

   def handleError(self):
      self.setEnabledStatus(True)

   def setEnabledStatus(self, status):
      self.promptStrength.setEnabled(status)
      self.steps.setEnabled(status)
      self.seed.setEnabled(status)
      self.nsfw.setEnabled(status)
      self.prompt.setEnabled(status)
      self.apikey.setEnabled(status)
      self.maxWait.setEnabled(status)
      self.generateButton.setEnabled(status)

class Worker():
   API_ROOT = "https://stablehorde.net/api/v2/"
   CHECK_WAIT = 5

   dialog = None
   checkMax = None
   checkCounter = 0
   id = None
   cancelled = False

   ssl._create_default_https_context = ssl._create_unverified_context

   def displayGenerated(self, images):
      for image in images:
         seed = image["seed"]
         data = image["img"].encode("ascii")
         bytearr = QtCore.QByteArray.fromBase64(data)
         image = QtGui.QImage()
         image.loadFromData(bytearr, 'WEBP')
         ptr = image.bits()
         ptr.setsize(image.byteCount())

         doc = Application.activeDocument()
         root = doc.rootNode()
         node = doc.createNode("Stablehorde " + str(seed), "paintLayer")
         root.addChildNode(node, None)
         node.setPixelData(QByteArray(ptr.asstring()), 0, 0, image.width(), image.height())
         doc.waitForDone()
         doc.refreshProjection()

   def getImages(self):
      url = self.API_ROOT + "generate/status/" + self.id
      response = urllib.request.urlopen(url)
      data = response.read()
      data = json.loads(data)

      return data["generations"]

   def checkStatus(self):
      try:
         url = self.API_ROOT + "generate/check/" + self.id
         response = urllib.request.urlopen(url)
         data = response.read()
         data = json.loads(data)

         self.checkCounter = self.checkCounter + 1
         print("checkCounter: " + str(self.checkCounter))
         print("cancelled: " + str(self.cancelled))

         if self.checkCounter < self.checkMax and data["done"] == False and self.cancelled == False:
            timer = threading.Timer(self.CHECK_WAIT, self.checkStatus)
            timer.start()
         elif self.checkCounter == self.checkMax and self.cancelled == False:
            minutes = (self.checkMax * self.CHECK_WAIT)/60
            raise Exception("Image generation timed out after " + str(minutes) + " minutes. Please try it again later.")
         elif data["done"] == True and self.cancelled == False:
            images = self.getImages()
            self.displayGenerated(images)
            self.dialog.close()
            print("Done! Image count: " + str(len(images)))

         return
      except Exception as ex:
         print(ex)
         self.dialog.handleError()

   def generate(self, dialog):
      self.dialog = dialog
      self.checkCounter = 0
      self.cancelled = False
      self.id = None
      self.checkMax = (self.dialog.maxWait.value() * 60)/self.CHECK_WAIT

      self.dialog.statusDisplay.setText("")

      nsfw = True if self.dialog.nsfw.isChecked() else False

      data = {
         "prompt": self.dialog.prompt.toPlainText(),
         "params": {
            "cfg_scale": self.dialog.promptStrength.value(),
            "height": 512,
            "width": 512,
            "steps": int(self.dialog.steps.value()),
            "seed": self.dialog.seed.text()
         },
         "nsfw": nsfw,
         "censor_nsfw": False
      }

      print(data)
      data = json.dumps(data).encode("utf-8")

      apikey = "0000000000" if self.dialog.apikey.text() == "" else self.dialog.apikey.text()
      headers = {"Content-Type": "application/json", "Accept": "application/json", "apikey": apikey}
      print(headers)

      url = self.API_ROOT + "generate/async"

      request = urllib.request.Request(url=url, data=data, headers=headers)
      self.dialog.statusDisplay.setText("Waiting for generated image...")

      try:
         response = urllib.request.urlopen(request)
         data = response.read()

         try:
            data = json.loads(data)
            self.id = data["id"]
         except Exception as ex:
            raise Exception(data)

         self.checkStatus()
      except Exception as ex:
         raise ex

      return

   def cancel(self):
      print("generation cancelled")
      self.cancelled = True

class Utils():
   updateChecked = False

   def errorMessage(self, text, detailed):
      msgBox = QMessageBox()
      msgBox.setWindowTitle("Stablehorde")
      msgBox.setText(text)
      msgBox.setDetailedText(detailed)
      msgBox.setStyleSheet("QLabel{min-width: 300px;}")
      msgBox.exec()

   def checkUpdate(self):
      if self.updateChecked is False:
         try:
            url = "https://raw.githubusercontent.com/blueturtleai/krita-stable-diffusion/main/version.json"
            response = urllib.request.urlopen(url)
            data = response.read()
            data = json.loads(data)

            self.updateChecked = True

            if VERSION < int(data["version"]):
               return {"update": True, "message": data["message"]}
            else:
               return {"update": False}
         except Exception as ex:
            return {"update": False}
      else:
         return {"update": False}

Krita.instance().addExtension(Stablehorde(Krita.instance()))
worker = Worker()
utils = Utils()
#dialog = Dialog()
#dialog.exec()
