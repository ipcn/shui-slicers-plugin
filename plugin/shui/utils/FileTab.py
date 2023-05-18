import os
from ..PyQt_API import (QtCore, QtWidgets, QtGui)
from .Core import (StartMode, UiTab, Preview)

class FileTab(UiTab):
    preview_size = 200
    preview = None
    parser = None
    locked = False

    def __init__(self, app):
        super().__init__(app)
        self.title = self.app.getLang("file")
        self.app.onUploadFinished.connect(self.onFinished)
        self.app.onProgress.connect(self.onProgress)
        self.app.onMessage.connect(self.onMessage)

        # preview picture
        self.bigPic = QtWidgets.QLabel()
        self.bigPic.setFixedWidth(self.preview_size)
        self.bigPic.setFixedHeight(self.preview_size)

        # preview buttons
        self.previewLabel = QtWidgets.QLabel(self.app.getLang("load-preview"))
        self.loadPreviewButton = QtWidgets.QPushButton(self.app.getLang("from-file"))
        self.pastePreviewButton = QtWidgets.QPushButton(self.app.getLang("from-clipboard"))

#        self.cbStartPrinting = QtWidgets.QCheckBox(self.app.getLang("start-printing"))
#        self.cbStartPrinting.setChecked(True)

        # print options
        self.cbAutoClose = QtWidgets.QCheckBox(self.app.getLang("auto-close"))
        self.cbAutoClose.setChecked(self.app.config.get("autoClose", False))

        # print filename
        self.leFileName = QtWidgets.QLineEdit()
        self.leFileName.setMaxLength(64)

        # print actions
#        actionsLabel = QtWidgets.QLabel(self.app.getLang("action"))
        self.actionsSelect = QtWidgets.QComboBox()
        self.actionsMap = self.makeActionsMap()
        actions = [self.app.getLang(act) for act in self.actionsMap.keys()]
        self.actionsSelect.addItems(actions)
        self.actionsSelect.setCurrentIndex(0)

        # print progress
        self.progress=QtWidgets.QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)

        # print log
        self.progress_label=QtWidgets.QLabel()
        self.progress_label.setWordWrap(True)
        self.progress_label.setText("---")
        self.okButton = QtWidgets.QPushButton(self.app.getLang("ok"))

	    # left area layout
        previewButtons = QtWidgets.QHBoxLayout()
        previewButtons.addWidget(self.previewLabel)
        previewButtons.addWidget(self.loadPreviewButton)
        previewButtons.addWidget(self.pastePreviewButton)

        leftArea = QtWidgets.QVBoxLayout()
        leftArea.addWidget(self.bigPic)
        leftArea.addStretch()
        leftArea.addLayout(previewButtons)

        # right area layout
        fileNameLayout = QtWidgets.QHBoxLayout()
        fileNameLayout.addWidget(QtWidgets.QLabel(self.app.getLang("output-name")))
        fileNameLayout.addWidget(self.leFileName)

        if self.app.startMode!=StartMode.CURA:
            self.btFileSelect = QtWidgets.QToolButton()
            self.btFileSelect.setText(self.app.getLang("select"))
            fileNameLayout.addWidget(self.btFileSelect)
            self.btFileSelect.clicked.connect(self.selectFile)

        actionsLayout = QtWidgets.QHBoxLayout()
#        actionsLayout.addWidget(actionsLabel)
        actionsLayout.addWidget(self.actionsSelect)
        actionsLayout.addStretch()

        buttonsLayout = QtWidgets.QHBoxLayout()
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.okButton)

        rightArea = QtWidgets.QVBoxLayout()
        rightArea.addLayout(fileNameLayout)
#        rightArea.addWidget(self.cbStartPrinting)
        rightArea.addLayout(actionsLayout)
        rightArea.addWidget(self.cbAutoClose)
        rightArea.addWidget(self.progress)
        rightArea.addWidget(self.progress_label)
        rightArea.addStretch()
        rightArea.addLayout(buttonsLayout)

        # main layout
        mainLayout=QtWidgets.QHBoxLayout()
        self.setLayout(mainLayout)
        mainLayout.addLayout(leftArea)
        mainLayout.addLayout(rightArea)
        
        # button actions
        self.loadPreviewButton.clicked.connect(self.onLoadPreview)
        self.pastePreviewButton.clicked.connect(self.onPastePreview)
        self.okButton.clicked.connect(self.onOk)

        self.startPrint = False
        self.preview = Preview()
        self.preview_mode = self.app.config.get("preview", "small")
        
        self.loadSource()
        pass

    def makeActionsMap(self):
        actions = {
            "print-to-printer": self.onSendToWifi,
            "send-to-printer": self.onSendToWifi,
            "save-to-file": self.onSaveToFile,
        }
        yandex_config = self.app.config.get("yandex")
        if yandex_config and (yandex_config.get("key")!="") \
                and yandex_config.get("enabled", True):
            actions["send-to-yandex"] = self.onSendToYandexDisk
        return actions

    def selectFile(self):
        dir = self.app.config.get("loadFileDir")
        if not dir and self.app.inputFileName:
            dir = os.path.dirname(os.path.abspath(self.app.inputFileName))
        if self.app.selectFile(dir):
            self.app.saveFileDir("loadFileDir", None, self.app.inputFileName)
            self.loadSource()
        pass

    def onLoadPreview(self):
        pattern = "Image Files (*.png *.jpg *.jpeg *.gif *.tif *.tiff *.bmp);;All Files (*)"
        try:
            dir = self.app.config.get("loadImageDir")
            if not dir:
                dir = self.app.config.get("loadFileDir")
            if not dir and self.app.inputFileName:
                dir = os.path.dirname(os.path.abspath(self.app.inputFileName))
            filename = self.app.selectFileDialog(self.app.getLang("open-file"), dir, None, pattern)
            if filename:
                self.app.saveFileDir("loadImageDir", None, filename)
                self.preview.loadFromFile(filename)
                self.showPreview()
        except Exception as err:
            self.onErrorMessage(str(err))
#            raise
        pass
    
    def onPastePreview(self):
        try:
            self.preview.loadFromClipboard()
            self.showPreview()
        except Exception as err:
            self.onErrorMessage(str(err))
#            raise
        pass
        
    def onOk(self, a):
        if self.locked:
            if self.sender is not None and self.sender.reply is not None:
                if self.sender.reply.isRunning():
                    self.sender.reply.abort()
        else:
            idx = self.actionsSelect.currentIndex()
            actions = list(self.actionsMap.keys())
            actionName = actions[idx]
            self.startPrint = (actionName == "print-to-printer")
            action = self.actionsMap.get(actionName)
            if action == None:
                self.onErrorMessage(self.app.getLang("error-unsupported-action"))
            else:
                self.onMessage("---")
                action()
        pass

    def onProgress(self, current, max):
        self.progress.setMaximum(int(max))
        self.progress.setValue(int(current))
        pass

    def onMessage(self, message):
        self.progress_label.setText(message)
        pass

    def onErrorMessage(self, message):
        self.onMessage("{}: {}".format(self.app.getLang("error"), message))
        pass

    def onSaveToFile(self):
        try:
            self.onProgress(0, 1)
            filename = self.leFileName.text()
            from .FileSaver import FileSaver
            self.lockUILock(True)
            fileSaver=FileSaver(self.app)
#            self.sender=fileSaver
            rows = self.parser.getProcessedGcode()
            fileSaver.save(rows, filename)
        except Exception as e:
            self.onErrorMessage(str(e))
            self.onFinished(False)
#            raise

    def onSendToYandexDisk(self):
        try:
            self.onProgress(0, 1)
            from .YandexSender import YandexSender
            self.lockUILock(True)
            wifiSender=YandexSender(self.app, self.leFileName.text())
            self.sender=wifiSender
            rows = self.parser.getProcessedGcode()
            wifiSender.save(rows)
        except Exception as e:
            self.onErrorMessage(str(e))
            self.onFinished(False)

    def onSendToWifi(self):
        try:
            self.onProgress(0, 1)
            from .WifiSender import WifiSender
            wifiSender=WifiSender(self.app, self.leFileName.text())
            self.lockUILock(True)
            rows = self.parser.getProcessedGcode()
            wifiSender.save(rows, start=self.startPrint)
            self.sender=wifiSender
        except Exception as e:
            self.onErrorMessage(str(e))
            self.onFinished(False)

    def lockUILock(self, locked):
        if locked:
            self.okButton.setText(self.app.getLang("terminate"))
        else:
            self.okButton.setText(self.app.getLang("ok"))
        self.locked=locked
        pass

    def showPreview(self):
        keep_aspect_ratio = self.app.config.get("keepPreviewAspectRatio")
        # QPixmap pixmap
        pixmap = self.preview.getVisualPixmap(self.preview_size, self.preview_size, keep_aspect_ratio)
        if pixmap is not None:
            self.bigPic.setPixmap(pixmap)
        if True:
            qimg = self.preview.getImage()
            fmt = self.preview.getFormat()
            if False:
                if qimg:
                    self.onMessage("{}: {}".format(self.app.getLang("info"), "loaded preview: " + str(fmt)))
                else:
                    self.onMessage("{}: {}".format(self.app.getLang("info"), "no preview"))
        pass

    def loadSource(self):
        # choose proper gcode parser
        if self.app.startMode==StartMode.PRUSA or self.app.startMode==StartMode.STANDALONE:
            if self.app.inputFileName is None or not os.path.exists(self.app.inputFileName):
                return
            from .PrusaGcodeParser import PrusaGCodeParser
            self.parser=PrusaGCodeParser(self.app, self.preview, self.app.inputFileName)
        elif self.app.startMode==StartMode.CURA:
            from .CuraGCodeParser import CuraGCodeParser
            self.parser=CuraGCodeParser(self.app, self.preview)

        # parse gcode and extract preview
        self.bigPic.clear()
        self.parser.parse()
        #self.preview.loadFromParser(self.parser)
        self.showPreview()

        # set uptput file naem
        if self.app.outputFileName is not None:
            self.leFileName.setText(self.app.outputFileName)
        pass

    def onFinished(self, state):
        self.lockUILock(False)
        self.sender=None
        autoClose = self.cbAutoClose.isChecked()
        if state and autoClose and self.app.mainWidget:
            self.app.mainWidget.doClose()
        pass
