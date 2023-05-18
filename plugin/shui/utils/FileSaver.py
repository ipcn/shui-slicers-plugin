from ..PyQt_API import (QtCore)


class GCodeSaver(QtCore.QObject):
    def __init__(self, app):
        super().__init__()
        self.app=app

    def makeBytes(self, rows):
        d=[]
        for r in rows:
            d+=r.encode()
        return bytearray(d)

class NetworkSender(GCodeSaver):

    def __init__(self, app, file_name):
        super().__init__(app)
        if len(file_name) == 0:
            self.fileName="SHUIWIFI"
        else:
            self.fileName=file_name

    def onUploadProgress(self, bytes_sent, bytes_total):
        if bytes_sent==0 and bytes_total==0:
            self.app.onProgress.emit(0, 1)
        else:
            self.app.onProgress.emit(bytes_sent, bytes_total)
            self.app.onMessage.emit("{}: {:d}/{:d}".format(self.app.getLang("sent"), bytes_sent, bytes_total))
        pass

    def onSslError(self, reply, sslerror):
        pass

class FileSaver(GCodeSaver):

    def save(self, rows, filename = None):
        state = True
        try:
            import os
            dir = self.app.config.get("saveFileDir")
            if not dir and self.app.inputFileName:
                dir = os.path.dirname(os.path.abspath(self.app.inputFileName))
            if dir:
                filename = os.path.join(dir, filename)
            filename = self.app.selectFileDialog(self.app.getLang("save-to-file"), dir, filename)
            if filename:
                self.app.saveFileDir("saveFileDir", None, filename)
                i=0
                c=len(rows)/100
                with open(filename, "w", encoding="utf-8") as out_file:
                    for r in rows:
                        if i%100==0:
                            self.app.onProgress.emit(i/100, c)
                        i=i+1
                        out_file.write(r)
                    self.app.onProgress.emit(1, 1)
                    out_file.close()
                    self.app.onMessage.emit(self.app.getLang("success"))
            else:
                state = False
        except Exception as e:
            self.app.onMessage.emit("{0}: {1}".format(self.app.getLang("error"), str(e)))
            print(str(e))
            state = False
        self.app.onUploadFinished.emit(state)
        pass
