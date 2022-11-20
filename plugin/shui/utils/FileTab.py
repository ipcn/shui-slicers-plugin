import os
from ..PyQt_API import (QtCore, QtWidgets, QtGui)
from .Core import (StartMode, UiTab)

class FileTab(UiTab):
    parser = None
    locked = False

    def __init__(self, app):
        super().__init__(app)
        self.title = self.app.getLang("file")
        self.app.onUploadFinished.connect(self.onFinised)
        self.app.onProgress.connect(self.onProgress)
        self.app.onMessage.connect(self.onMessage)

        self.bigPic = QtWidgets.QLabel()
        self.bigPic.setFixedWidth(200)
        self.bigPic.setFixedHeight(200)

#        self.cbStartPrinting = QtWidgets.QCheckBox(self.app.getLang("start-printing"))
#        self.cbStartPrinting.setChecked(True)

        self.cbAutoClose = QtWidgets.QCheckBox(self.app.getLang("auto-close"))
        self.cbAutoClose.setChecked(False)

        self.leFileName = QtWidgets.QLineEdit()
        self.leFileName.setMaxLength(64)

        self.progress=QtWidgets.QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)

        self.progress_label=QtWidgets.QLabel()
        self.progress_label.setWordWrap(True)
        self.progress_label.setText("---")
        self.okButton = QtWidgets.QPushButton(self.app.getLang("ok"))

        mainLayout=QtWidgets.QHBoxLayout()
        self.setLayout(mainLayout)
#        mainLayout.addWidget(self.bigPic)
        leftArea = QtWidgets.QVBoxLayout()
        leftArea.addWidget(self.bigPic)
        leftArea.addStretch()
        mainLayout.addLayout(leftArea)
        rightArea = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(rightArea)

        fileNameLayout = QtWidgets.QHBoxLayout()
        fileNameLayout.addWidget(QtWidgets.QLabel(self.app.getLang("output-name")))
        fileNameLayout.addWidget(self.leFileName)

        if self.app.startMode!=StartMode.CURA:
            self.btFileSelect = QtWidgets.QToolButton()
            self.btFileSelect.setText(self.app.getLang("select"))
            fileNameLayout.addWidget(self.btFileSelect)
            self.btFileSelect.clicked.connect(self.selectFile)

#        actionsLabel = QtWidgets.QLabel(self.app.getLang("action"))
        self.actionsSelect = QtWidgets.QComboBox()
        self.actionsMap = self.makeActionsMap()
        actions = [self.app.getLang(act) for act in self.actionsMap.keys()]
        self.actionsSelect.addItems(actions)
        self.actionsSelect.setCurrentIndex(0)

        actionsLayout = QtWidgets.QHBoxLayout()
#        actionsLayout.addWidget(actionsLabel)
        actionsLayout.addWidget(self.actionsSelect)
        actionsLayout.addStretch()

        buttonsLayout = QtWidgets.QHBoxLayout()
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.okButton)

        rightArea.addLayout(fileNameLayout)
#        rightArea.addWidget(self.cbStartPrinting)
        rightArea.addLayout(actionsLayout)
        rightArea.addWidget(self.cbAutoClose)
        rightArea.addWidget(self.progress)
        rightArea.addWidget(self.progress_label)
        rightArea.addStretch()
        rightArea.addLayout(buttonsLayout)

        self.okButton.clicked.connect(self.onOk)

        self.startPrint = False

        if self.app.inputFileName is not None and os.path.exists(self.app.inputFileName):
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
        if self.app.selectFile():
            self.loadSource()
        pass

    def onOk(self, a):
        if self.locked:
            if self.sender is not None and self.sender.reply is not None:
                if self.sender.reply.isRunning():
                    self.sender.reply.abort()
        else:
            '''
            menu=QtWidgets.QMenu(self)

            newAct = QtWidgets.QWidgetAction(menu)
            newAct.setText(self.app.getLang("save-to-file"))
            newAct.triggered.connect(self.onSaveToFile)
            menu.addAction(newAct)

            newAct = QtWidgets.QWidgetAction(menu)
            newAct.setText(self.app.getLang("send-to-printer"))
            newAct.triggered.connect(self.onSendToWifi)
            menu.addAction(newAct)

            yandex_config=self.app.config.get("yandex")
            if yandex_config and (yandex_config.get("key")!="") \
                    and yandex_config.get("enabled", True):
                newAct = QtWidgets.QWidgetAction(menu)
                newAct.setText(self.app.getLang("send-to-yandex"))
                newAct.triggered.connect(self.onSendToYandexDisk)
                menu.addAction(newAct)

            menu.exec(self.mapToGlobal(self.okButton.pos()))
            '''
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
            if self.app.inputFileName:
                dir = os.path.dirname(os.path.abspath(self.app.inputFileName))
                filename = os.path.join(dir, filename)
            preview_mode = self.app.config.get("preview", "small")
            from .FileSaver import FileSaver
            self.lockUILock(True)
            fileSaver=FileSaver(self.app)
#            self.sender=fileSaver
            fileSaver.save(self.parser.getProcessedGcode(preview_mode), filename)
        except Exception as e:
            self.onErrorMessage(str(e))
            self.onFinised(False)

    def onSendToYandexDisk(self):
        try:
            preview_mode = self.app.config.get("preview", "small")
            self.onProgress(0, 1)
            from .YandexSender import YandexSender
            self.lockUILock(True)
            wifiSender=YandexSender(self.app, self.leFileName.text())
            self.sender=wifiSender
            wifiSender.save(self.parser.getProcessedGcode(preview_mode))
        except Exception as e:
            self.onErrorMessage(str(e))
            self.onFinised(False)

    def onSendToWifi(self):
        try:
            preview_mode = self.app.config.get("preview", "small")
            self.onProgress(0, 1)
            from .WifiSender import WifiSender
            wifiSender=WifiSender(self.app, self.leFileName.text())
            self.lockUILock(True)
            wifiSender.save(self.parser.getProcessedGcode(preview_mode), start=self.startPrint)
            self.sender=wifiSender
        except Exception as e:
            self.onErrorMessage(str(e))
            self.onFinised(False)

    def lockUILock(self, locked):
        if locked:
            self.okButton.setText(self.app.getLang("terminate"))
        else:
            self.okButton.setText(self.app.getLang("ok"))
        self.locked=locked
        pass

    def loadSource(self):
        if self.app.startMode==StartMode.PRUSA or self.app.startMode==StartMode.STANDALONE:
            from .PrusaGcodeParser import PrusaGCodeParser
            self.parser=PrusaGCodeParser(self.app.inputFileName)
        elif self.app.startMode==StartMode.CURA:
            from .CuraGCodeParser import CuraGCodeParser
            self.parser=CuraGCodeParser()

        self.bigPic.clear()
        preview = None
        if self.parser is not None:
            preview = self.parser.getLargePreview()
            if preview is None:
                self.parser.parse()
                preview = self.parser.getLargePreview()
        if preview is None:
            preview = self.parser.getDefaultPreview()
 
        if preview is not None:
            self.bigPic.setPixmap(preview)

        if self.app.outputFileName is not None:
            self.leFileName.setText(self.app.outputFileName)

    def onFinised(self, state):
        self.lockUILock(False)
        self.sender=None
        autoClose = self.cbAutoClose.isChecked()
        if state and autoClose and self.app.mainWidget:
            self.app.mainWidget.doClose()
        pass
