from ..PyQt_API import (QtCore)
import socket

class ConnectionThread(QtCore.QThread):

    address=None
    connected=False

    def __init__(self, app):
        QtCore.QThread.__init__(self)
        self.app=app
        self.sock=None

    def send(self, message):
        message=message.replace('|', '\n')
        message=message+"\n\r"
        if self.sock:
            try:
                self.sock.send(message.encode())
            except Exception as e:
                self.app.onUartMessage.emit("Error: "+str(e))
        pass

    def notifyConnect(self, c):
        self.connected = c;
        self.app.onUartConnect.emit(c)
        pass

    def disconnect(self):
        if self.isRunning():
            self.exit(0)
        if self.connected:
            self.notifyConnect(False)
            self.sock.close()
#            self.sock=None
        pass

    def connect(self, address):
        if (self.address!=address) or not self.connected:
            self.disconnect()
            self.address=address
            self.app.onUartMessage.emit("Connecting... "+address)
            self.start()
        pass

    def run(self):
        try:
            reading=False
            self.sock = socket.socket()
            self.sock.connect((self.address, 8080))
            self.notifyConnect(True)
            reading=True
            buf=bytearray()
            while(True):
                data = self.sock.recv(1024)
                for a in data:
                    if a==10:
                        self.app.onUartRow.emit(buf.decode('utf-8'))
                        buf=bytearray()
                    else:
                        buf.append(a)
        except Exception as e:
            if self.connected or not reading:
                self.app.onUartMessage.emit("Error: "+str(e))
        self.disconnect()
        pass
