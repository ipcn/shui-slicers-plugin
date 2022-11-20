import os
import sys
from sys import argv
import json

#from PyQt5 import (QtCore, QtWidgets)
#from PyQt5.QtNetwork import (QNetworkAccessManager, QNetworkProxy)
from .PyQt_API import (QtCore, QtWidgets)
from .PyQt_API import (QNetworkAccessManager, QNetworkProxy)
from .utils import (ConnectionThread, Core, SetupDialog, ConsoleTab, FileTab, PrinterControlTab, TelegramTab, AlisaTab)

class App(QtCore.QObject):
    wifiUart=None
    config=None
    plugin=None
    version="?.?.?"
    selectedPrinter = 0
    startMode = Core.StartMode.UNKNOWN
    outputFileName=None
    inputFileName=None

    onProgress = QtCore.pyqtSignal(object, object)
    onMessage = QtCore.pyqtSignal(object)
    onUploadFinished = QtCore.pyqtSignal(object)
    onUartRow = QtCore.pyqtSignal(object)
    onUartMessage = QtCore.pyqtSignal(object)
    onUartConnect = QtCore.pyqtSignal(object)

    def __init__(self, appStartMode, **kwargs):
        super().__init__()
        self.startMode=appStartMode
        self.inputFileName=None
        if appStartMode==Core.StartMode.PRUSA:
            self.startMode = Core.StartMode.PRUSA
            self.outputFileName = os.getenv('SLIC3R_PP_OUTPUT_NAME')
            if self.outputFileName is not None:
                self.outputFileName=os.path.basename(self.outputFileName)
            if len(sys.argv) > 1:
                self.inputFileName=sys.argv[1]
        elif appStartMode==Core.StartMode.STANDALONE:
            if len(sys.argv) > 1:
                self.inputFileName=sys.argv[1]
            pass
        elif appStartMode==Core.StartMode.CURA:
            if "output_file_name" in kwargs:
                self.outputFileName = kwargs["output_file_name"]

        if self.inputFileName is None:
            self.inputFileName = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", "shui_prusa.gcode")
        if self.outputFileName is None:
            self.outputFileName = os.path.basename(self.inputFileName)
        self.wifiUart = ConnectionThread(self)

        config_file_name="config_local.json" if os.getenv('USER')=='shubin' else "config.json"
        self.config_file=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", config_file_name)
        self.config = self.loadConfig()

        plugin_file_name="plugin_local.json" if os.getenv('USER')=='shubin' else "plugin.json"
        self.plugin_file=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", plugin_file_name)
        self.plugin = self.loadPluginConfig()
        if self.plugin and self.plugin.get("version"):
            self.version = self.plugin.get("version")

        self.lang_file=os.path.join(os.path.dirname(os.path.abspath(__file__)),"langs.json")
        self.langs_cfg = self.loadLang()

        selected=self.config["language"]
        self.lang={}
        if "inherited" in self.langs_cfg[selected]:
            for inh in self.langs_cfg[selected]["inherited"]:
                self.lang=self.langs_cfg[inh]["lang"]
        self.lang.update(self.langs_cfg[selected]["lang"])

        self.proxy=QNetworkProxy()

        if "proxy" in self.config:
            proxy_config=self.config["proxy"]
            if proxy_config["enabled"]:
                if "host" in proxy_config:
                    self.proxy.setHostName(proxy_config["host"])
                if "port" in proxy_config:
                    self.proxy.setPort(proxy_config["port"])
                if "user" in proxy_config:
                    self.proxy.setUser(proxy_config["user"])
                if "password" in proxy_config:
                    self.proxy.setPassword(proxy_config["password"])
                self.proxy.setType(QNetworkProxy.HttpProxy)

        self.networkManager = QNetworkAccessManager()
        self.networkManager.setProxy(self.proxy)
        self.mainWidget = None

        pass

    def selectFile(self):
#        options = QtWidgets.QFileDialog.Options()
        options = QtWidgets.QFileDialog.Option.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self.mainWidget, "Open file", None, "GCODE Files (*.gcode *.gco);;All Files (*)", options=options)
        if fileName:
            self.inputFileName=fileName
            self.outputFileName = os.path.basename(self.inputFileName)
            return True
        return False

    def getLang(self, text):
        if text and self.lang and text in self.lang:
            return self.lang[text]
        return text

    def makePrinterItem(self, p):
        item = "{} ({})".format(p.get("name", "?"), p.get("ip", "?"))
#        if p.get("esp32", False):
#            item += " / " + self.getLang("esp32")
        return item

    def loadLang(self):
        with open(self.lang_file, encoding="utf-8") as lf:
            langs_cfg=json.load(lf)
            lf.close()
            return langs_cfg

    def loadPluginConfig(self):
        with open(self.plugin_file, encoding="utf-8") as jf:
            cfg=json.load(jf)
            jf.close()
            return cfg

    def loadConfig(self):
        with open(self.config_file, encoding="utf-8") as jf:
            cfg=json.load(jf)
            jf.close()
            return cfg

    def saveConfig(self):
        with open(self.config_file, "w", encoding="utf-8") as jf:
            json.dump(self.config, jf, indent=4, ensure_ascii=False)
            jf.close()
        pass

    def onUpdateConfig(self):
        self.saveConfig()
        if self.mainWidget:
            self.mainWidget.updatePrinters()

class MainWidget(QtWidgets.QDialog):
    def __init__(self, app):
        super().__init__()
        self.app=app
        self.app.mainWidget = self
        self.title = "{} (v{})".format(self.app.getLang("title"), self.app.version)
        self.setWindowTitle(self.title)
        self.setFixedWidth(500)
        self.setFixedHeight(300)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.mainLayout.setSpacing(0)

        self.printerSelectLayout = QtWidgets.QHBoxLayout()
        self.cbPrinterSelect = QtWidgets.QComboBox(self)
        self.cbPrinterSelect.currentIndexChanged.connect(self.printerChanged)
        self.updatePrinters()

        self.btConnect = QtWidgets.QPushButton(self)
        self.btConnect.setMaximumSize(QtCore.QSize(100, 16777215))

        self.btSetup = QtWidgets.QPushButton(self)
        self.btSetup.setMaximumSize(QtCore.QSize(100, 16777215))
        self.btSetup.setText(self.app.getLang("setup"))

        self.btClose = QtWidgets.QPushButton(self)
        self.btClose.setMaximumSize(QtCore.QSize(100, 16777215))
        self.btClose.setText(self.app.getLang("close"))

        self.printerSelectLayout.addWidget(self.cbPrinterSelect)
        self.printerSelectLayout.addWidget(self.btConnect)
        self.printerSelectLayout.addWidget(self.btSetup)
        self.printerSelectLayout.addWidget(self.btClose)

        self.printerSelectLayout.setContentsMargins(2, 2, 2, 2)

        self.tabWidget = QtWidgets.QTabWidget(self)
        self.tabWidget.currentChanged.connect(self.tabChanged)

        self.mainLayout.addLayout(self.printerSelectLayout)
        self.mainLayout.addWidget(self.tabWidget)

        self.makeTabs()

        self.btSetup.clicked.connect(self.doSetup)
        self.btConnect.clicked.connect(self.doConnect)
        self.btClose.clicked.connect(self.doClose)
        self.app.onUartConnect.connect(self.doOnConnect)
        self.doOnConnect(False)
        pass

    def tabChanged(self, index):
        self.btConnect.setVisible(self.tabs[index].view_connect)
        pass

    def doClose(self):
        self.close()
        pass

    def makeTabs(self):
        self.tabs = []

        tab = FileTab(self.app)
        self.tabs.append(tab)
        self.tabWidget.addTab(tab, tab.title)

        tab = PrinterControlTab(self.app)
        self.tabs.append(tab)
        self.tabWidget.addTab(tab, tab.title)

        tab = ConsoleTab(self.app)
        self.tabs.append(tab)
        self.tabWidget.addTab(tab, tab.title)

        tg_config=self.app.config.get("telegram")
        if tg_config and tg_config.get("enabled", False) and tg_config.get("key") and tg_config.get("chat_id"):
                tab = TelegramTab(self.app)
                self.tabs.append(tab)
                self.tabWidget.addTab(tab, tab.title)
        yandex_config=self.app.config.get("yandex")
        if yandex_config and yandex_config.get("enabled", False) and yandex_config.get("key"):
            tab = AlisaTab(self.app)
            self.tabs.append(tab)
            self.tabWidget.addTab(tab, tab.title)
        pass

    def doSetup(self):
        dialog = SetupDialog(self, self.app) 
        dialog.exec()

    def doConnect(self):
        if self.app.wifiUart.connected:
            self.app.wifiUart.disconnect()
        else:
            self.app.wifiUart.connect(self.app.config["printers"][self.app.selectedPrinter]["ip"])
        pass

    def doOnConnect(self, connected):
        if connected:
            self.btConnect.setText(self.app.getLang("disconnect"))
        else:
            self.btConnect.setText(self.app.getLang("connect"))

    def updatePrinters(self):
        printers = self.app.config.get("printers", [])
        items = [self.app.makePrinterItem(p) for p in printers]
        idx = self.app.selectedPrinter
        self.cbPrinterSelect.clear()
        self.cbPrinterSelect.addItems(items)
        if (idx < 0):
            idx = 0
        if (idx >= len(printers)):
            idx = len(printers) - 1
        self.app.selectedPrinter = idx
        self.cbPrinterSelect.setCurrentIndex(idx)
        pass

    def printerChanged(self, index):
        if index >= 0:
            self.app.selectedPrinter = index
        pass

def makeForm(startMode, **kwargs):
    app=App(startMode, **kwargs)
    form = MainWidget(app)
    form.show()
    printers = app.config.get("printers", [])
    if len(printers) <= 0:
        form.doSetup() 
    return form

def cura_application(**kwargs):
    return makeForm(Core.StartMode.CURA, **kwargs)

def qt_application(startMode):
    import sys
    application = QtWidgets.QApplication(sys.argv)
    form = makeForm(startMode)
    sys.exit(application.exec())
