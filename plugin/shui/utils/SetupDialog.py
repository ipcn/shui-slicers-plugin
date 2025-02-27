from ..PyQt_API import (QtCore, QtWidgets, QtGui)
from .Core import (PreviewModes)

class SetupDialog(QtWidgets.QDialog):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app=app
        self.title = "{} - {}".format(self.app.getLang("setup"), self.app.title)
        self.setWindowTitle(self.title)

        self.config = self.makeConfig()
        owner = self

        self.printerIdx = 0
        self.printer = None

        # printers list with buttons
#        self.printersLabel = QtWidgets.QLabel(self.app.getLang("printers-list"), owner)
        self.printersList = QtWidgets.QListWidget(owner)
        self.printersList.setMaximumHeight(4 * 20)

        printerListLayout = QtWidgets.QVBoxLayout()
#        printerListLayout.addWidget(self.printersLabel)
        printerListLayout.addWidget(self.printersList)

        # printer property with buttons
#        self.printerLabel = QtWidgets.QLabel(self.app.getLang("printer-property"), owner)
        self.nameEditInput = QtWidgets.QLineEdit(owner)
        self.ipEditInput = QtWidgets.QLineEdit(owner)
        self.esp32EditCheck = QtWidgets.QCheckBox(self.app.getLang("esp32"), owner)
        self.savePrinterButton = QtWidgets.QPushButton(self.app.getLang("printer-apply"), owner)
        self.delPrinterButton = QtWidgets.QPushButton(self.app.getLang("printer-delete"), owner)

        printerButtonsLayout = QtWidgets.QHBoxLayout()
        printerButtonsLayout.addWidget(self.delPrinterButton)
        printerButtonsLayout.addWidget(self.savePrinterButton)

        # edit printers box
        editPrinterLayout = QtWidgets.QVBoxLayout()
#        editPrinterLayout.addLayout(langsLayout)
        editPrinterLayout.addStretch()
#        editPrinterLayout.addWidget(self.printerLabel)
        editPrinterLayout.addWidget(self.nameEditInput)
        editPrinterAddrLayout = QtWidgets.QHBoxLayout()
        editPrinterAddrLayout.addWidget(self.ipEditInput)
        editPrinterAddrLayout.addWidget(self.esp32EditCheck)
        editPrinterLayout.addLayout(editPrinterAddrLayout)
        editPrinterLayout.addLayout(printerButtonsLayout)

        printersBoxLayout = QtWidgets.QHBoxLayout()
        printersBoxLayout.addLayout(printerListLayout)
        printersBoxLayout.addLayout(editPrinterLayout)
        printersBox =  QtWidgets.QGroupBox(self.app.getLang("printers-options"), owner)
        printersBox.setLayout(printersBoxLayout)

        # edit printers actions
        self.savePrinterButton.clicked.connect(self.onSavePrinter)
        self.delPrinterButton.clicked.connect(self.onDeletePrinter)
        self.printersList.currentRowChanged.connect(self.onSelectPrinter)
        self.nameEditInput.textChanged.connect(self.onPrinterChanged)
        self.ipEditInput.textChanged.connect(self.onPrinterChanged)
        self.esp32EditCheck.stateChanged.connect(self.onPrinterChanged)

        # plugin options: languages & preview
        langsLabel = QtWidgets.QLabel(self.app.getLang("language"), owner)
        self.langsSelect = QtWidgets.QComboBox(owner)
        previewLabel = QtWidgets.QLabel(self.app.getLang("preview"), owner)
        self.previewSelect = QtWidgets.QComboBox(owner)
        self.previewAspectRatioCheck = QtWidgets.QCheckBox(self.app.getLang("preview-aspect-ratio"), owner)
        self.previewAspectRatioCheck.clicked.connect(self.onChangedPreviewAspectRatio)
        self.autoCloseCheck = QtWidgets.QCheckBox(self.app.getLang("auto-close"), owner)
        self.autoCloseCheck.clicked.connect(self.onChangedAutoClose)

        optsLayout = QtWidgets.QHBoxLayout()
        optsLayout.addWidget(langsLabel)
        optsLayout.addWidget(self.langsSelect)
        optsLayout.addWidget(previewLabel)
        optsLayout.addWidget(self.previewSelect)
        optsLayout.addWidget(self.previewAspectRatioCheck)
        optsLayout.addWidget(self.autoCloseCheck)
        optsLayout.addStretch()
        optsBox =  QtWidgets.QGroupBox(self.app.getLang("plugin-options"), owner)
        optsBox.setLayout(optsLayout)

        # proxy
        self.proxyCheck = QtWidgets.QCheckBox(self.app.getLang("proxy"), owner)
        self.proxyCheck.clicked.connect(self.onProxyEnabled)
        self.proxyHostEdit = QtWidgets.QLineEdit(owner)
        self.proxyHostEdit.setPlaceholderText("host")
        self.proxyPortEdit = QtWidgets.QLineEdit(owner)
        self.proxyPortEdit.setPlaceholderText("port")
        self.proxyUserEdit = QtWidgets.QLineEdit(owner)
        self.proxyUserEdit.setPlaceholderText("user")
        self.proxyPassEdit = QtWidgets.QLineEdit(owner)
        self.proxyPassEdit.setPlaceholderText("password")
        proxyLayout = QtWidgets.QHBoxLayout()
        proxyLayout.addWidget(self.proxyCheck)
        proxyLayout.addWidget(self.proxyHostEdit)
        proxyLayout.addWidget(self.proxyPortEdit)
        proxyLayout.addWidget(self.proxyUserEdit)
        proxyLayout.addWidget(self.proxyPassEdit)

        # yandex
        self.yandexCheck = QtWidgets.QCheckBox(self.app.getLang("yandex"), owner)
        self.yandexCheck.clicked.connect(self.onYandexEnabled)
        self.yandexKeyEdit = QtWidgets.QLineEdit(owner)
        self.yandexKeyEdit.setPlaceholderText("token")
        self.yandexOverrideCheck = QtWidgets.QCheckBox(self.app.getLang("override"), owner)
        yandexLayout = QtWidgets.QHBoxLayout()
        yandexLayout.addWidget(self.yandexCheck)
        yandexLayout.addWidget(self.yandexKeyEdit)
        yandexLayout.addWidget(self.yandexOverrideCheck)

        # telegram 
        self.telegramCheck = QtWidgets.QCheckBox(self.app.getLang("telegram"), owner)
        self.telegramCheck.clicked.connect(self.onTelegramEnabled)
        self.telegramKeyEdit = QtWidgets.QLineEdit(owner)
        self.telegramKeyEdit.setPlaceholderText("bot token")
        self.telegramChatIdEdit = QtWidgets.QLineEdit(owner)
        self.telegramChatIdEdit.setPlaceholderText("chat id")
        telegramLayout = QtWidgets.QHBoxLayout()
        telegramLayout.addWidget(self.telegramCheck)
        telegramLayout.addWidget(self.telegramKeyEdit)
        telegramLayout.addWidget(self.telegramChatIdEdit)

        # network box
        networkLayout = QtWidgets.QVBoxLayout()
        networkLayout.addLayout(proxyLayout)
        networkLayout.addLayout(yandexLayout)
        networkLayout.addLayout(telegramLayout)
        networkBox =  QtWidgets.QGroupBox(self.app.getLang("network-options"), owner)
        networkBox.setLayout(networkLayout)

        # save & discard buttons
        self.statusLabel = QtWidgets.QLabel("", owner)
        self.saveButton = QtWidgets.QPushButton(self.app.getLang("save"), owner)
        self.discardButton = QtWidgets.QPushButton(self.app.getLang("discard"), owner)
        buttonsLayout = QtWidgets.QHBoxLayout()
        buttonsLayout.addWidget(self.statusLabel)
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.discardButton)
        buttonsLayout.addWidget(self.saveButton)

        self.saveButton.clicked.connect(self.onSaveData)
        self.discardButton.clicked.connect(self.onDiscardData)

        # main layout 
        mainLayout=QtWidgets.QVBoxLayout()
        mainLayout.addWidget(printersBox)
        mainLayout.addWidget(optsBox)
        mainLayout.addWidget(networkBox)
#        mainLayout.addLayout(langsLayout)
#        mainLayout.addLayout(printersBoxLayout)
#        mainLayout.addLayout(networkLayout)
        mainLayout.addLayout(buttonsLayout)
        self.setLayout(mainLayout)

        self.showData()
        pass

    def makeConfig(self):
        cfg = {
            "printers": [],
            "language": "en",
            "preview": "small",
            "autoClose": False,
            "nativeFileDialog": True,
            "keepPreviewAspectRatio": True,
            "proxy": {"enabled":False, "host":"host.proxy.ru", "port": 8080, "user": "user", "password":"password"},
            "yandex": {"enabled":False, "key":"key", "override":False},
            "telegram": {"enabled":False, "key":"key", "chat_id":"chat_id"},
        }
        if self.app.config:
            for key in cfg.keys():
                val = self.app.config.get(key)
                if val is not None:
                    if key == "printers":
                        cfg[key] = [{k:p.get(k) for k in p.keys()} for p in val]
                    else:
                        cfg[key] = val
        return cfg

    def showError(self, text):
        self.statusLabel.setText(text)

    def showData(self):
        langs = list(self.app.langs_cfg.keys())
        lang = self.config.get("language", "en")
        self.langsSelect.clear()
        self.langsSelect.addItems(langs)
        try:
            lang_idx = langs.index(lang)
            self.langsSelect.setCurrentIndex(lang_idx)
        except:
            pass

        preview_modes = list(PreviewModes.keys())
        preview_mode = self.config.get("preview", "small")
        self.previewSelect.clear()
        self.previewSelect.addItems(preview_modes)
        try:
            preview_idx = preview_modes.index(preview_mode)
            self.previewSelect.setCurrentIndex(preview_idx)
        except:
            pass

        self.autoCloseCheck.setChecked(self.config.get("autoClose", False))
        self.previewAspectRatioCheck.setChecked(self.config.get("keepPreviewAspectRatio", True))

        cfg = self.config.get("proxy")
        self.proxyCheck.setChecked(cfg.get("enabled", False))
        self.proxyHostEdit.setText(cfg.get("host", ""))
        self.proxyPortEdit.setText(str(cfg.get("port", "")))
        self.proxyUserEdit.setText(cfg.get("user", ""))
        self.proxyPassEdit.setText(cfg.get("password", ""))
        self.onProxyEnabled()

        cfg = self.config.get("yandex")
        self.yandexCheck.setChecked(cfg.get("enabled", False))
        self.yandexKeyEdit.setText(cfg.get("key", ""))
        self.yandexOverrideCheck.setChecked(cfg.get("override", False))
        self.onYandexEnabled()

        cfg = self.config.get("telegram")
        self.telegramCheck.setChecked(cfg.get("enabled", False))
        self.telegramKeyEdit.setText(cfg.get("key", ""))
        self.telegramChatIdEdit.setText(cfg.get("chat_id", ""))
        self.onTelegramEnabled()

        self.updatePrinters()

    def saveData(self):
        self.config["language"] = self.langsSelect.currentText()
        self.config["preview"] = self.previewSelect.currentText()
        self.config["autoClose"] = self.autoCloseCheck.isChecked()
        self.config["keepPreviewAspectRatio"] = self.previewAspectRatioCheck.isChecked()

        self.config["proxy"] = {
            "enabled": self.proxyCheck.isChecked(),
            "host": self.proxyHostEdit.text(),
            "port": int(self.proxyPortEdit.text()),
            "user": self.proxyUserEdit.text(),
            "password": self.proxyPassEdit.text(),
        }
        self.config["yandex"] = {
            "enabled": self.yandexCheck.isChecked(),
            "key": self.yandexKeyEdit.text(),
            "override": self.yandexOverrideCheck.isChecked(),
        }
        self.config["telegram"] = {
            "enabled": self.telegramCheck.isChecked(),
            "key": self.telegramKeyEdit.text(),
            "chat_id": self.telegramChatIdEdit.text(),
        }

        if not self.app.config:
            self.app.config = {}
        for key in list(self.config.keys()):
            self.app.config[key] = self.config[key]
        self.app.onUpdateConfig()
 
    def doClose(self):
        self.close()

    def onDiscardData(self):
        self.doClose()
        pass

    def onSaveData(self):
        self.showError("")
        try:
            self.saveData()
        except Exception as e:
            self.showError(str(e))
            return
        self.doClose()

    def updatePrinters(self):
        items = []
        self.printersList.clear()
        printers = self.config.get("printers", [])
        for p in self.config["printers"]:
            item = self.app.makePrinterItem(p)
            self.printersList.addItem(item)
        self.printersList.addItem(self.app.getLang("printer-new"))
        self.selectPrinter(self.printerIdx)
        pass

    def selectPrinter(self, idx):
        self.printerIdx = idx
        deletable = False
        saveable = False
        printers = self.config.get("printers", [])
        if self.printerIdx >= 0 and self.printerIdx < len(printers):
            self.printer = self.config["printers"][self.printerIdx]
            deletable = True
        else:
            self.printer = {
                "name": self.app.getLang("printer-name"),
                "ip": self.app.getLang("printer-ip"),
                "esp32": True
            }
            saveable = True

        self.nameEditInput.setText(self.printer["name"])
        self.ipEditInput.setText(self.printer["ip"])
        self.esp32EditCheck.setChecked(self.printer["esp32"])

        self.printersList.setCurrentRow(self.printerIdx)
        self.savePrinterButton.setEnabled(saveable)
        self.delPrinterButton.setEnabled(deletable)
        pass

    def onPrinterChanged(self):
        self.savePrinterButton.setEnabled(True)
        pass

    def onSelectPrinter(self):
        idx = self.printersList.currentRow()
        if (idx >= 0):
            self.selectPrinter(idx)
        pass

    def onSavePrinter(self):
        self.printer["name"] = self.nameEditInput.text()
        self.printer["ip"] = self.ipEditInput.text()
        self.printer["esp32"] = self.esp32EditCheck.isChecked()

        if not (self.printer["name"] and self.printer["ip"]):
            return
        printers = self.config.get("printers", [])
        if self.printerIdx >= len(self.config["printers"]):
            printers.append(self.printer)

#        self.app.onUpdateConfig()
        self.updatePrinters()
        pass

    def onDeletePrinter(self):
        printers = self.config.get("printers", [])
        if self.printerIdx >= 0 and self.printerIdx < len(printers):
            printers.pop(self.printerIdx)
        else:
            return
#        self.app.onUpdateConfig()
        self.updatePrinters()
        pass

    def onProxyEnabled(self):
        enabled = self.proxyCheck.isChecked()
        self.proxyHostEdit.setEnabled(enabled)
        self.proxyPortEdit.setEnabled(enabled)
        self.proxyUserEdit.setEnabled(enabled)
        self.proxyPassEdit.setEnabled(enabled)

    def onYandexEnabled(self):
        enabled = self.yandexCheck.isChecked()
        self.yandexKeyEdit.setEnabled(enabled)
        self.yandexOverrideCheck.setEnabled(enabled)

    def onTelegramEnabled(self):
        enabled = self.telegramCheck.isChecked()
        self.telegramKeyEdit.setEnabled(enabled)
        self.telegramChatIdEdit.setEnabled(enabled)

    def onChangedAutoClose(self):
        self.autoClose = self.autoCloseCheck.isChecked()

    def onChangedPreviewAspectRatio(self):
        self.previewAspectRatio = self.previewAspectRatioCheck.isChecked()
