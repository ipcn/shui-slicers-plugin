from PyQt5 import (QtCore, QtWidgets, QtGui)
from .Core import (StartMode, UiTab)

class FileTab(UiTab):
    parser = None
    locked = False

    def __init__(self, app):
        super().__init__(app)
        self.title = self.app.lang["file"]
        self.app.onUploadFinished.connect(self.onFinised)
        self.app.onProgress.connect(self.onProgress)
        self.app.onMessage.connect(self.onMessage)


        self.bigPic = QtWidgets.QLabel()
        self.bigPic.setFixedWidth(200)
        self.bigPic.setFixedHeight(200)


        self.cbStartPrinting = QtWidgets.QCheckBox(self.app.lang["start-printing"])
        self.cbStartPrinting.setChecked(True)

        self.leFileName = QtWidgets.QLineEdit()
        self.leFileName.setMaxLength(64)

        self.progress=QtWidgets.QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)

        self.progress_label=QtWidgets.QLabel()
        self.progress_label.setText("---")
        self.okButton = QtWidgets.QPushButton("OK")

        mainLayout=QtWidgets.QHBoxLayout()
        self.setLayout(mainLayout)
        mainLayout.addWidget(self.bigPic)
        rightArea = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(rightArea)

        fileNameLayout = QtWidgets.QHBoxLayout()
        fileNameLayout.addWidget(QtWidgets.QLabel(self.app.lang["output-name"]))
        fileNameLayout.addWidget(self.leFileName)

        if self.app.startMode!=StartMode.CURA:
            self.btFileSelect = QtWidgets.QToolButton()
            self.btFileSelect.setText(self.app.lang["select"])
            fileNameLayout.addWidget(self.btFileSelect)
            self.btFileSelect.clicked.connect(self.selectFile)

        rightArea.addLayout(fileNameLayout)
        rightArea.addWidget(self.cbStartPrinting)
        rightArea.addStretch()
        rightArea.addWidget(self.progress)
        rightArea.addWidget(self.progress_label)

        buttonsLayout = QtWidgets.QHBoxLayout()
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.okButton)
        rightArea.addLayout(buttonsLayout)

        self.okButton.clicked.connect(self.onOk)

        if self.app.inputFileName is not None:
            self.loadSource()
        pass

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
            menu=QtWidgets.QMenu(self)

            newAct = QtWidgets.QAction(self.app.lang["save-to-file"], menu)
            newAct.triggered.connect(self.onSaveToFile)
            menu.addAction(newAct)

            newAct = QtWidgets.QAction(self.app.lang["send-to-printer"], menu)
            newAct.triggered.connect(self.onSendToWifi)
            menu.addAction(newAct)

            yandex_config=self.app.config.get("yandex")
            if yandex_config and (yandex_config.get("key")!=""):
                newAct = QtWidgets.QAction(self.app.lang["send-to-yandex"], menu)
                newAct.triggered.connect(self.onSendToYandexDisk)
                menu.addAction(newAct)

            menu.exec_(self.mapToGlobal(self.okButton.pos()))

    def onProgress(self, current, max):
        self.progress.setMaximum(max)
        self.progress.setValue(current)
        pass

    def onMessage(self, message):
        self.progress_label.setText(message)
        pass

    def onSaveToFile(self):
        try:
            self.onProgress(0, 1)
            from .FileSaver import FileSaver
            fileSaver=FileSaver(self.app)
            fileSaver.save(self.parser.getProcessedGcode())
        except Exception as e:
            self.onMessage(str(e))
        pass

    def onSendToYandexDisk(self):
        try:
            self.onProgress(0, 1)
            from .YandexSender import YandexSender
            self.lockUILock(True)
            wifiSender=YandexSender(self.app, self.leFileName.text())
            self.sender=wifiSender
            wifiSender.save(self.parser.getProcessedGcode())
        except Exception as e:
            self.onMessage(str(e))
            self.onFinised(False)
        pass

    def onSendToWifi(self):
        try:
            self.onProgress(0, 1)
            from .WifiSender import WifiSender
            wifiSender=WifiSender(self.app, self.leFileName.text())
            self.lockUILock(True)
            wifiSender.save(self.parser.getProcessedGcode(), start=self.cbStartPrinting.checkState()==QtCore.Qt.Checked)
            self.sender=wifiSender
        except Exception as e:
            self.onMessage(str(e))
            self.onFinised(False)
        pass

    def lockUILock(self, locked):
        if locked:
            self.okButton.setText("Terminate")
        else:
            self.okButton.setText("Ok")
        self.locked=locked
        pass

    def loadSource(self):
        if self.app.startMode==StartMode.PRUSA or self.app.startMode==StartMode.STANDALONE:
            from .PrusaGcodeParser import PrusaGCodeParser
            self.parser=PrusaGCodeParser(self.app.inputFileName)
        elif self.app.startMode==StartMode.CURA:
            from .CuraGCodeParser import CuraGCodeParser
            self.parser=CuraGCodeParser()

        if self.parser is not None:
            preview = self.parser.getLargePreview()
            if preview is None:
                self.parser.parse()
                preview = self.parser.getLargePreview()
                if preview is not None:
                    self.bigPic.setPixmap(preview)

        if self.app.outputFileName is not None:
            self.leFileName.setText(self.app.outputFileName)

    def onFinised(self, state):
        self.lockUILock(False)
        self.sender=None
        pass