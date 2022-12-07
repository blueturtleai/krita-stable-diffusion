# v1.3.3

import base64
import json
import ssl
import threading
import urllib
import math

from krita import *

VERSION = 133

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

      settings = self.readSettings()

      self.setWindowTitle("Stablehorde")
      self.layout = QVBoxLayout()

      # Basic Tab
      tabBasic = QWidget()
      layout = QFormLayout()

      # Generation Mode
      box = QGroupBox()
      self.modeText2Img = QRadioButton("Text -> Image")
      self.modeImg2Img = QRadioButton("Image -> Image")
      self.modeInpainting = QRadioButton("Inpainting")
      layoutV = QVBoxLayout()
      layoutV.addWidget(self.modeText2Img)
      layoutV.addWidget(self.modeImg2Img)
      layoutV.addWidget(self.modeInpainting)
      box.setLayout(layoutV)
      label = QLabel("Generation Mode")
      label.setStyleSheet("QLabel{margin-top:12px;}")
      layout.addRow(label, box)

      group = QButtonGroup()
      group.addButton(self.modeText2Img, worker.MODE_TEXT2IMG)
      group.addButton(self.modeImg2Img, worker.MODE_IMG2IMG)
      group.addButton(self.modeInpainting, worker.MODE_INPAINTING)
      group.button(settings["generationMode"]).setChecked(True)
      self.generationMode = group
      self.generationMode.buttonClicked.connect(self.handleModeChanged)

      mode = self.generationMode.checkedId()

      # NSFW
      self.nsfw = QCheckBox()
      self.nsfw.setCheckState(settings["nsfw"])
      layout.addRow("NSFW",self.nsfw)

      # Seed
      self.seed = QLineEdit()
      self.seed.setText(settings["seed"])
      layout.addRow("Seed (optional)", self.seed)

      # Prompt
      self.prompt = QTextEdit()
      self.prompt.setText(settings["prompt"])
      layout.addRow("Prompt", self.prompt)

      # Status
      self.statusDisplay = QTextEdit()
      self.statusDisplay.setReadOnly(True)
      layout.addRow("Status", self.statusDisplay)

      # Generate
      self.generateButton = QPushButton("Generate")
      self.generateButton.clicked.connect(self.generate)
      layout.addWidget(self.generateButton)

      # Space
      layoutH = QHBoxLayout()
      layoutH.addSpacing(50)
      container = QWidget()
      container.setLayout(layoutH)
      layout.addWidget(container)

      # Cancel
      cancelButton = QPushButton("Cancel")
      cancelButton.setFixedWidth(100)
      cancelButton.clicked.connect(self.reject)
      layout.addWidget(cancelButton)
      layout.setAlignment(cancelButton, Qt.AlignRight)

      tabBasic.setLayout(layout)

      # Advanced Tab
      tabAdvanced = QWidget()
      layout = QFormLayout()

      # Init Strength
      slider = QSlider(Qt.Orientation.Horizontal, self)
      slider.setRange(0, 10)
      slider.setTickInterval(1)
      slider.setValue(settings["initStrength"])
      self.initStrength = slider
      labelInitStrength = QLabel(str(self.initStrength.value()/10))
      self.initStrength.valueChanged.connect(lambda: labelInitStrength.setText(str(self.initStrength.value()/10)))
      layoutH = QHBoxLayout()
      layoutH.addWidget(self.initStrength)
      layoutH.addWidget(labelInitStrength)
      container = QWidget()
      container.setLayout(layoutH)
      layout.addRow("Init Strength", container)

      if mode == worker.MODE_TEXT2IMG or mode == worker.MODE_INPAINTING:
         self.initStrength.setEnabled(False)

      # Prompt Strength
      slider = QSlider(Qt.Orientation.Horizontal, self)
      slider.setRange(0, 20)
      slider.setTickInterval(1)
      slider.setValue(settings["promptStrength"])
      self.promptStrength = slider
      labelPromptStrength = QLabel(str(self.promptStrength.value()))
      self.promptStrength.valueChanged.connect(lambda: labelPromptStrength.setText(str(self.promptStrength.value())))
      layoutH = QHBoxLayout()
      layoutH.addWidget(self.promptStrength)
      layoutH.addWidget(labelPromptStrength)
      container = QWidget()
      container.setLayout(layoutH)
      layout.addRow("Prompt Strength", container)

      # Steps
      slider = QSlider(Qt.Orientation.Horizontal, self)
      slider.setRange(10, 200)
      slider.setTickInterval(1)
      slider.setValue(settings["steps"])
      self.steps = slider
      labelSteps = QLabel(str(self.steps.value()))
      self.steps.valueChanged.connect(lambda: labelSteps.setText(str(self.steps.value())))
      layoutH = QHBoxLayout()
      layoutH.addWidget(self.steps)
      layoutH.addWidget(labelSteps)
      container = QWidget()
      container.setLayout(layoutH)
      layout.addRow("Steps", container)

      # API Key
      self.apikey = QLineEdit()
      self.apikey.setText(settings["apikey"])
      layout.addRow("API Key (optional)", self.apikey)

      # Max Wait
      slider = QSlider(Qt.Orientation.Horizontal, self)
      slider.setRange(1, 5)
      slider.setTickInterval(1)
      slider.setValue(settings["maxWait"])
      self.maxWait = slider
      labelMaxWait = QLabel(str(self.maxWait.value()))
      self.maxWait.valueChanged.connect(lambda: labelMaxWait.setText(str(self.maxWait.value())))
      layoutH = QHBoxLayout()
      layoutH.addWidget(self.maxWait)
      layoutH.addWidget(labelMaxWait)
      container = QWidget()
      container.setLayout(layoutH)
      layout.addRow("Max Wait (minutes)", container)

      tabAdvanced.setLayout(layout)

      tabs = QTabWidget()
      tabs.addTab(tabBasic, "Basic")
      tabs.addTab(tabAdvanced, "Advanced")
      self.layout.addWidget(tabs)

      self.setLayout(self.layout)
      self.resize(350, 300)

      webpSupport = utils.checkWebpSupport()

      if webpSupport is False:
         self.generateButton.setEnabled(False)
         self.statusDisplay.setText("Your operating system doesn't support the webp image format. Please check troubleshooting section of readme on GitHub for solution.")

      update = utils.checkUpdate()

      if update["update"] is True:
         self.statusDisplay.setText(update["message"])

   def handleModeChanged(self):
      mode = self.generationMode.checkedId()

      if mode == worker.MODE_TEXT2IMG or mode == worker.MODE_INPAINTING:
         self.initStrength.setEnabled(False)
      elif mode == worker.MODE_IMG2IMG:
         self.initStrength.setEnabled(True)

   def generate(self):
      mode = self.generationMode.checkedId()
      doc = Application.activeDocument()

      # no document
      if doc is None:
         utils.errorMessage("Please open a document. Please check details.", "For image generation a document with a size between 384x384 and 1024x1024, color model 'RGB/Alpha', color depth '8-bit integer' and a paint layer is needed.")
         return
      # document has invalid color model or depth
      elif doc.colorModel() != "RGBA" or doc.colorDepth() != "U8":
         utils.errorMessage("Invalid document properties. Please check details.", "For image generation a document with color model 'RGB/Alpha', color depth '8-bit integer' is needed.")
         return
      # document too small or large
      elif doc.width() < 384 or doc.width() > 1024 or doc.height() < 384 or doc.height() > 1024:
         utils.errorMessage("Invalid document size. Please check details.", "Document needs to be between 384x384 and 1024x1024.")
         return
      # img2img/inpainting: missing init image layer
      elif (mode == worker.MODE_IMG2IMG or mode == worker.MODE_INPAINTING) and worker.getInitNode() is None:
         utils.errorMessage("Please add a visible layer which shows the init/inpainting image.", "")
         return
      # img2img/inpainting: selection has to be removed otherwise crashes krita when creating init image
      elif (mode == worker.MODE_IMG2IMG or mode == worker.MODE_INPAINTING) and doc.selection() is not None:
         utils.errorMessage("Please remove the selection by clicking on the image.", "")
         return
      # no prompt
      elif len(self.prompt.toPlainText()) == 0:
         utils.errorMessage("Please enter a prompt.", "")
         return
      else:
         self.writeSettings()
         self.setEnabledStatus(False)
         self.statusDisplay.setText("Waiting for generated image...")
         worker.generate(self)

   #override
   def customEvent(self, ev):
      if ev.type() == worker.eventId:
         if ev.updateType == UpdateEvent.TYPE_CHECKED:
            self.statusDisplay.setText(ev.message)
         elif ev.updateType == UpdateEvent.TYPE_INFO:
            self.statusDisplay.setText(ev.message)
            self.setEnabledStatus(True)
         elif ev.updateType == UpdateEvent.TYPE_ERROR:
            self.statusDisplay.setText("An error occurred: " + ev.message)
            self.setEnabledStatus(True)
         elif ev.updateType == UpdateEvent.TYPE_FINISHED:
            self.close()

   #override
   def reject(self):
      worker.cancel()
      self.writeSettings()
      super().reject()

   def readSettings(self):
      defaults = {
         "generationMode": worker.MODE_TEXT2IMG,
         "initStrength": 3,
         "prompt": "",
         "promptStrength": 8,
         "steps": 50,
         "seed": "",
         "nsfw": 0,
         "apikey": "",
         "maxWait": 5
      }

      try:
         settings = Application.readSetting("Stablehorde", "Config", None)

         if not settings:
            settings = defaults
         else:
            settings = json.loads(settings)
            missing = False

            for key in defaults:
               if not key in settings:
                  missing = True
                  break

            if missing is True:
               settings = defaults
      except Exception as ex:
         settings = defaults

      return settings

   def writeSettings(self):
      settings = {
         "generationMode": self.generationMode.checkedId(),
         "initStrength": self.initStrength.value(),
         "prompt": self.prompt.toPlainText(),
         "promptStrength": self.promptStrength.value(),
         "steps": int(self.steps.value()),
         "seed": self.seed.text(),
         "nsfw": self.nsfw.checkState(),
         "apikey": self.apikey.text(),
         "maxWait": self.maxWait.value()
      }

      try:
         settings = json.dumps(settings)
         Application.writeSetting("Stablehorde", "Config", settings)
      except Exception as ex:
         ex = ex

   def setEnabledStatus(self, status):
      self.modeText2Img.setEnabled(status)
      self.modeImg2Img.setEnabled(status)
      self.modeInpainting.setEnabled(status)

      if self.generationMode.checkedId() == worker.MODE_IMG2IMG:
         self.initStrength.setEnabled(status)

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
   MODE_TEXT2IMG = 1
   MODE_IMG2IMG = 2
   MODE_INPAINTING = 3

   dialog = None
   checkMax = None
   checkCounter = 0
   id = None
   cancelled = False

   eventId = QEvent.registerEventType()

   ssl._create_default_https_context = ssl._create_unverified_context

   def getInitImage(self):
      doc = Application.activeDocument()
      nodeInit = self.getInitNode()

      if nodeInit is not None:
         if doc.selection() is not None:
            raise Exception("Selection has to be removed before creating init image.")

         bytes = nodeInit.pixelData(0, 0, doc.width(), doc.height())
         image = QImage(bytes.data(), doc.width(), doc.height(), QImage.Format_RGBA8888).rgbSwapped()
         bytes = QByteArray()
         buffer = QBuffer(bytes)
         image.save(buffer, "WEBP")
         data = base64.b64encode(bytes.data())
         data = data.decode("ascii")
         return data
      else:
         raise Exception("No layer with init image found.")

   def getInitNode(self):
      doc = Application.activeDocument()
      nodes = doc.topLevelNodes()

      nodeInit = None

      for node in nodes:
         if node.visible() is True:
            nodeInit = node

      return nodeInit

   def displayGenerated(self, images):
      for image in images:
         seed = image["seed"]
         bytes = base64.b64decode(image["img"])
         bytes = QByteArray(bytes)
         image = QImage()
         image.loadFromData(bytes, 'WEBP')
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

         if self.checkCounter < self.checkMax and data["done"] is False and self.cancelled is False:
            if data["is_possible"] is True:
               if data["processing"] == 0:
                  message = "Queue position: " + str(data["queue_position"]) + ", Wait time: " + str(data["wait_time"]) + "s"
               elif data["processing"] > 0:
                  message = "Generating..."

               ev = UpdateEvent(worker.eventId, UpdateEvent.TYPE_CHECKED, message)
               QApplication.postEvent(self.dialog, ev)

               timer = threading.Timer(self.CHECK_WAIT, self.checkStatus)
               timer.start()
            else:
               self.cancelled = True
               message = "Currently no worker available to generate your image. Please try again later."
               ev = UpdateEvent(worker.eventId, UpdateEvent.TYPE_INFO, message)
               QApplication.postEvent(self.dialog, ev)
         elif self.checkCounter == self.checkMax and self.cancelled == False:
            self.cancelled = True
            minutes = (self.checkMax * self.CHECK_WAIT)/60
            message = "Image generation timed out after " + str(minutes) + " minutes. Please try it again later."
            ev = UpdateEvent(worker.eventId, UpdateEvent.TYPE_INFO, message)
            QApplication.postEvent(self.dialog, ev)
         elif data["done"] == True and self.cancelled == False:
            images = self.getImages()
            self.displayGenerated(images)

            ev = UpdateEvent(worker.eventId, UpdateEvent.TYPE_FINISHED)
            QApplication.postEvent(self.dialog, ev)

         return
      except urllib.error.HTTPError as ex:
         try:
            data = ex.read()
            data = json.loads(data)

            if "message" in data:
               message = data["message"]
            else:
               message = str(ex)
         except Exception:
            message = str(ex)

         ev = UpdateEvent(worker.eventId, UpdateEvent.TYPE_ERROR, message)
         QApplication.postEvent(self.dialog, ev)
      except Exception as ex:
         ev = UpdateEvent(worker.eventId, UpdateEvent.TYPE_ERROR, str(ex))
         QApplication.postEvent(self.dialog, ev)

   def generate(self, dialog):
      self.dialog = dialog
      self.checkCounter = 0
      self.cancelled = False
      self.id = None
      self.checkMax = (self.dialog.maxWait.value() * 60)/self.CHECK_WAIT

      try:
         nsfw = True if self.dialog.nsfw.isChecked() else False

         params = {
            "cfg_scale": self.dialog.promptStrength.value(),
            "steps": int(self.dialog.steps.value()),
            "seed": self.dialog.seed.text()
         }

         data = {
            "prompt": self.dialog.prompt.toPlainText(),
            "params": params,
            "nsfw": nsfw,
            "censor_nsfw": False,
            "r2": False
         }

         doc = Application.activeDocument()

         if doc.width() % 64 != 0:
            width = math.floor(doc.width()/64) * 64
         else:
            width = doc.width()

         if doc.height() % 64 != 0:
            height = math.floor(doc.height()/64) * 64
         else:
            height = doc.height()

         params.update({"width": width})
         params.update({"height": height})

         mode = self.dialog.generationMode.checkedId()

         if mode == worker.MODE_IMG2IMG:
            init = self.getInitImage()
            data.update({"source_image": init})
            data.update({"source_processing": "img2img"})
            params.update({"denoising_strength": round((1 - self.dialog.initStrength.value()/10), 1)})
         elif mode == worker.MODE_INPAINTING:
            init = self.getInitImage()
            models = ["stable_diffusion_inpainting"]
            data.update({"source_image": init})
            data.update({"source_processing": "inpainting"})
            data.update({"models": models})

         data = json.dumps(data).encode("utf-8")

         apikey = "0000000000" if self.dialog.apikey.text() == "" else self.dialog.apikey.text()
         headers = {"Content-Type": "application/json", "Accept": "application/json", "apikey": apikey}

         url = self.API_ROOT + "generate/async"

         request = urllib.request.Request(url=url, data=data, headers=headers)
         self.dialog.statusDisplay.setText("Waiting for generated image...")

         response = urllib.request.urlopen(request)
         data = response.read()

         try:
            data = json.loads(data)
            self.id = data["id"]
         except Exception as ex:
            raise Exception(data)

         self.checkStatus()
      except urllib.error.HTTPError as ex:
         try:
            data = ex.read()
            data = json.loads(data)

            if "message" in data:
               message = data["message"]
            else:
               message = str(ex)
         except Exception:
            message = str(ex)

         ev = UpdateEvent(worker.eventId, UpdateEvent.TYPE_ERROR, message)
         QApplication.postEvent(self.dialog, ev)
      except Exception as ex:
         ev = UpdateEvent(worker.eventId, UpdateEvent.TYPE_ERROR, str(ex))
         QApplication.postEvent(self.dialog, ev)

      return

   def cancel(self):
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

   def checkWebpSupport(self):
      formats = QImageReader.supportedImageFormats()
      found = False

      for format in formats:
         if format.data().decode("ascii").lower() == "webp":
            found = True
            break

      return found

class UpdateEvent(QEvent):
   TYPE_CHECKED = 0
   TYPE_ERROR = 1
   TYPE_INFO = 2
   TYPE_FINISHED = 3

   def __init__(self, eventId, updateType, message = ""):
      self.updateType = updateType
      self.message = message
      super().__init__(eventId)

Krita.instance().addExtension(Stablehorde(Krita.instance()))
utils = Utils()
worker = Worker()
#dialog = Dialog()
#dialog.exec()
