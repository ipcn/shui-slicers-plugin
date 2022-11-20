from .FileSaver import NetworkSender
from ..PyQt_API import (QtCore)
from ..PyQt_API import (QHttpMultiPart, QHttpPart, QNetworkRequest, QNetworkAccessManager, QNetworkReply, QNetworkProxy)

class WifiSender(NetworkSender):
    reply=None
    request=None
    postData=None

    def save(self, rows, **kwargs):
        if len(self.app.config["printers"]) <= 0:
            self.app.onMessage.emit("{}: {}".format(self.app.getLang("error"), self.app.getLang("error-no-printers")))
            self.app.onUploadFinished.emit(False)
            return

        self.app.wifiUart.disconnect()
        try:
            rows=self.makeBytes(rows)
            ip = self.app.config["printers"][self.app.selectedPrinter]["ip"]
            esp32 = self.app.config["printers"][self.app.selectedPrinter]["esp32"]
            request = QNetworkRequest(QtCore.QUrl("http://%s/upload" % ip))
            post_data = None
            if "start" in kwargs:
                if kwargs["start"]:
                    request.setRawHeader(b'Start-Printing', b'1')
            if esp32:
                post_data = rows
                request.setRawHeader(b'Content-Type', b'application/octet-stream')
                request.setRawHeader(b'File-Name', self.fileName.encode())
            else:
                post_data = QHttpMultiPart(QHttpMultiPart.ContentType.FormDataType)
                part = QHttpPart()
                part.setHeader(QNetworkRequest.KnownHeaders.ContentDispositionHeader,
                               "form-data; name=\"file\"; filename=\"%s\"" % self.fileName)
                part.setBody(rows)
                post_data.append(part)
                request.setRawHeader(b'Content-Type', b'multipart/form-data; boundary='+post_data.boundary())
            self.postData=post_data

            self.app.onMessage.emit(self.app.getLang("connecting"))
            proxy=QNetworkProxy()
            proxy.setType(QNetworkProxy.ProxyType.NoProxy)
            self.app.networkManager.setProxy(proxy)
            self.reply = self.app.networkManager.post(request, post_data)
            self.reply.finished.connect(self.handleResponse)
            self.reply.uploadProgress.connect(self.onUploadProgress)
            self.reply.sslErrors.connect(self.onSslError)
        except Exception as e:
            self.app.onMessage.emit("{0}: {1}".format(self.app.getLang("error"), str(e)))
            print(str(e))
            self.postData=None
            self.reply=None
            self.app.onUploadFinished.emit(False)
        pass

    def handleResponse(self):
        state = True
        er = self.reply.error()
        if er == QNetworkReply.NetworkError.NoError:
            self.app.onMessage.emit(self.app.getLang("success"))
        else:
            self.app.onMessage.emit("{0} {1}:{2}".format(self.app.getLang("error"), er, self.reply.errorString()))
            state = False

        self.reply=None
        self.postData=None
        self.app.onUploadFinished.emit(state)
        pass
