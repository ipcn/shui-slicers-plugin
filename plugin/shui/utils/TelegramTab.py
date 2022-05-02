from PyQt5 import (QtCore, QtWidgets)
import requests
import json
from .Core import (StartMode, UiTab)


class TgClient(QtCore.QThread):
    tg_url = None
    onMessage = QtCore.pyqtSignal(object)

    def __init__(self, app):
        QtCore.QThread.__init__(self)
        self.tg_url="https://api.telegram.org/bot"+app.config["telegram"]["key"]+"/"
        self.app=app

    def transac(self, method, data):
        return json.loads(requests.post(self.tg_url+method, json=data, verify=False).content)

    def listen(self):
        self.start()
        pass

    def kill(self):
        if self.isRunning():
            self.exit(0)

    def on_message(self, message):
        self.onMessage.emit(message)
        pass

    def run(self):
        pooling_data={"limit":1, "offset":-1, "timeout":120}
        while True:
            resp_json = self.transac("getUpdates", pooling_data)
            for result_json in resp_json["result"]:
                pooling_data["offset"]=result_json["update_id"]+1
                if result_json["message"]:
                    self.on_message(result_json["message"])
        pass

class TelegramTab(UiTab):
    rows = []
    tg = None

    def __init__(self, app):
        super().__init__(app)
        self.title = self.app.lang["telegram"]

        self.teConsoleOutput = QtWidgets.QTextEdit(self)
        self.teConsoleOutput.setReadOnly(True)

        self.teConsoleOutput.setStyleSheet("*{background-color: black; color:rgb(255,255,0)}")
        self.slGCodeMessage = QtWidgets.QLineEdit(self)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.slGCodeMessage.sizePolicy().hasHeightForWidth())

        self.slGCodeMessage.setSizePolicy(sizePolicy)
        self.teConsoleOutput.setSizePolicy(sizePolicy)

        self.btSenb = QtWidgets.QPushButton()
        self.btSenb.setMaximumSize(QtCore.QSize(100, 16777215))
        self.btSenb.setMinimumWidth(100)
        self.btSenb.setText(self.app.lang["send"])
        #self.btSenb.setDisabled(True)


        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.addWidget(self.teConsoleOutput)
        #self.setLayout(self.mainLayout)

        self.sendLayout = QtWidgets.QHBoxLayout()
        self.sendLayout.addWidget(self.slGCodeMessage)
        self.sendLayout.addWidget(self.btSenb)
        self.sendLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addLayout(self.sendLayout)

        self.btSenb.clicked.connect(self.doSend)
        self.addRow(self.app.lang["telegram-bot-welcome"])

        self.tg=TgClient(self.app)
        self.tg.listen()
        self.tg.onMessage.connect(self.onMessage)

        pass

    def onMessage(self, message):
        if (message["text"]):
            sender_chat=message.get("sender_chat")
            if sender_chat!=None:
                name=sender_chat["title"]
            else:
                name=None
                fn=message["from"].get("first_name")
                ln=message["from"].get("last_name")
                if fn:
                    name=fn
                if ln:
                    if name:
                        name=name+" "
                    name=name+ln
            self.addRow("{0}: {1}".format(name, message["text"]))
        pass

    def start(self):
        pass

    def __del__(self):
        self.tg.kill()
        pass

    def keyPressEvent(self, event):
        if not self.doSendKeyPress(event):
            super().keyPressEvent(event)


    def addRow(self, row):
        self.rows.append(row)
        if len(self.rows)>20:
            self.rows.pop(0)
        self.teConsoleOutput.setText("\n".join(self.rows))
        self.teConsoleOutput.verticalScrollBar().setValue(self.teConsoleOutput.verticalScrollBar().maximum())
        pass

    def doSend(self):
        text=self.slGCodeMessage.text()
        if (len(text)>0):
            self.tg.transac("sendMessage", {"chat_id":self.app.config["telegram"]["chat_id"], "text":text})
            self.slGCodeMessage.setSelection(0, len(text))
            self.addRow(text)
        pass

    def doSendKeyPress(self, event):
        if (event.key() == QtCore.Qt.Key_Enter) or (event.key() == QtCore.Qt.Key_Return):
            self.doSend()
            return True
        return False


