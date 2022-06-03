from PyQt5 import (QtCore, QtWidgets, QtGui)
from PyQt5.QtNetwork import (QNetworkRequest, QNetworkAccessManager, QNetworkReply, QNetworkProxy)
from .Core import (StartMode, UiTab)

class AlisaTab(UiTab):
    rlist=[]
    rows=[]
    def __init__(self, app):
        super().__init__(app)
        self.title = self.app.lang["alisa"]

        self.teConsoleOutput = QtWidgets.QTextEdit(self)
        self.teConsoleOutput.setReadOnly(True)

        self.teConsoleOutput.setStyleSheet("*{background-color: black; color:rgb(0,255,0)}")

        self.btReload = QtWidgets.QPushButton()
        self.btReload.setMaximumSize(QtCore.QSize(100, 16777215))
        self.btReload.setMinimumWidth(200)
        self.btReload.setText(self.app.lang["reload"])


        self.mainLayout = QtWidgets.QHBoxLayout()
        self.scenarioLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addLayout(self.scenarioLayout)
        self.scenarioLayout.addWidget(self.btReload)

        self.mainLayout.addWidget(self.teConsoleOutput)

        self.scenarioWidget = QtWidgets.QWidget()
        self.scenarioButtonsLayout = QtWidgets.QVBoxLayout(self.scenarioWidget)

        self.scrolArea = QtWidgets.QScrollArea()
        self.scrolArea.setWidget(self.scenarioWidget)
        self.scrolArea.setWidgetResizable(True)
        self.scenarioLayout.addWidget(self.scrolArea)

        self.setLayout(self.mainLayout)

        self.btReload.clicked.connect(self.loadScenarios)
        self.loadScenarios()

    def onSslError(self, reply, sslerror):
        pass

    def loadScenarios(self):
        for w in self.rlist:
            self.scenarioButtonsLayout.removeWidget(w)
        self.rlist=[]
        self.req=QNetworkRequest(QtCore.QUrl("https://api.iot.yandex.net/v1.0/user/info"))
        self.req.setRawHeader(b'Accept', b'application/json')
        self.req.setRawHeader(b'Authorization', ('OAuth '+self.app.config["yandex"]["key"]).encode())
        self.reply = self.app.networkManager.get(self.req)

        def handleResponse():
            import json
            er = self.reply.error()
            if er == QNetworkReply.NoError:
                jresp=json.loads(bytes(self.reply.readAll()).decode())
                if "scenarios" in jresp:
                    self.addScenarioButtons(jresp["scenarios"])

            self.req=None
            self.reply=None
            pass

        self.reply.finished.connect(handleResponse)
        self.reply.sslErrors.connect(self.onSslError)

    def addRow(self, row):
        self.rows.append(row)
        if len(self.rows)>20:
            self.rows.pop(0)
        self.teConsoleOutput.setText("\n".join(self.rows))
        self.teConsoleOutput.verticalScrollBar().setValue(self.teConsoleOutput.verticalScrollBar().maximum())
        pass

    def callScenario(self, id):
        self.req=QNetworkRequest(QtCore.QUrl("https://api.iot.yandex.net/v1.0/scenarios/" + str(id) + "/actions"))
        self.req.setRawHeader(b'Accept', b'application/json')
        self.req.setRawHeader(b'Authorization', ('OAuth '+self.app.config["yandex"]["key"]).encode())
        self.reply = self.app.networkManager.post(self.req, None)
        def handleResponse():
            import json
            er = self.reply.error()
            if er == QNetworkReply.NoError:
                jresp=json.loads(bytes(self.reply.readAll()).decode())
                self.addRow(json.dumps(jresp))
            self.req=None
            self.reply=None
            pass

        self.reply.finished.connect(handleResponse)
        self.reply.sslErrors.connect(self.onSslError)
        pass

    def addScenarioButtons(self, scenarios):

        class ScenarioButton(QtWidgets.QPushButton):
            def __init__(self, owner, id):
                super(ScenarioButton, self).__init__()
                self.id=id
                self.owner=owner
            def click(self):
                self.owner.callScenario(self.id)
                pass


        for scenario in scenarios:
            edit = QtWidgets.QLineEdit()
            edit.setText(scenario["id"])
            edit.setReadOnly(True)
            self.scenarioButtonsLayout.addWidget(edit)
            self.rlist.append(edit)
            button = ScenarioButton(self, scenario["id"])
            button.setText(scenario["name"])
            button.clicked.connect(button.click)
            self.scenarioButtonsLayout.addWidget(button)
            self.rlist.append(button)



