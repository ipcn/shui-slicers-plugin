from ..PyQt_API import (QtCore, QtWidgets)
import json
from .Core import (StartMode, UiTab)
from ..PyQt_API import (QNetworkRequest, QNetworkAccessManager, QNetworkReply, QNetworkProxy)

class TelegramTab(UiTab):
    rows = []
    tg = None
    pooling_data={"limit":1, "offset":-1, "timeout":120}

    def __init__(self, app):
        super().__init__(app)
        self.title = self.app.getLang("telegram")
        self.tg_config = app.config.get("telegram")

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
        self.btSenb.setText(self.app.getLang("send"))
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
        self.addRow(self.app.getLang("telegram-bot-welcome"))

        #self.tg=TgClient(self.app)
        #self.tg.listen()
        #self.tg.onMessage.connect(self.onMessage)
        self.pooling()

    def pooling(self):
        tg_key = self.tg_config.get("key")
        if not tg_key:
            return
        try:
            import json
            tg_url="https://api.telegram.org/bot"+tg_key+"/getUpdates"
            self.req=QNetworkRequest(QtCore.QUrl(tg_url))
            self.req.setRawHeader(b'Content-Type', b'application/json')
            post_data=json.dumps(self.pooling_data).encode("utf-8")
            self.reply = self.app.networkManager.post(self.req, post_data)
            def handleResponse():
                er = self.reply.error()
                if er == QNetworkReply.NetworkError.NoError:
                    jresp=json.loads(bytes(self.reply.readAll()).decode())
                    for result_json in jresp["result"]:
                        self.pooling_data["offset"]=result_json["update_id"]+1
                        if "message" in result_json:
                            self.onMessage(result_json["message"])
                self.req=None
                self.reply=None
                self.pooling()
                pass

            self.reply.finished.connect(handleResponse)
            self.reply.sslErrors.connect(self.onSslError)
        except Exception as err:
            self.showMessage("<error>", str(err))
        pass

    def onSslError(self, reply, sslerror):
        pass

    def onMessage(self, message):
        text = message.get("text")
        if text:
            name="<chat>"
            sender_chat=message.get("sender_chat")
            if sender_chat!=None:
                name=sender_chat.get("title")
            else:
                name_from=message.get("from")
                if name_from:
                    fn=name_from.get("first_name")
                    ln=name_from.get("last_name")
                    if fn:
                        name=fn
                    if ln:
                        if name:
                            name=name+" "
                        name=name+ln
            self.showMessage(name, text)
        pass

    def showMessage(self, name, text):
        self.addRow("{0}: {1}".format(name, text))
    
    def start(self):
        pass

    def __del__(self):
#        if self.tg:
#            self.tg.kill()
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
            tg_url="https://api.telegram.org/bot"+self.tg_config.get("key")+"/sendMessage"
            self.req_sm=QNetworkRequest(QtCore.QUrl(tg_url))
            self.req_sm.setRawHeader(b'Content-Type', b'application/json')
            post_data=json.dumps({"chat_id":self.tg_config.get("chat_id"), "text":text}).encode("utf-8")
            self.reply_sm = self.app.networkManager.post(self.req_sm, post_data)

            def handleResponse():
                self.req_sm=None
                self.reply_sm=None
                pass

            self.reply_sm.finished.connect(handleResponse)
            self.reply_sm.sslErrors.connect(self.onSslError)

            self.slGCodeMessage.setSelection(0, len(text))
            self.addRow(text)
        pass

    def doSendKeyPress(self, event):
        if (event.key() == QtCore.Qt.Key.Key_Enter) or (event.key() == QtCore.Qt.Key.Key_Return):
            self.doSend()
            return True
        return False
