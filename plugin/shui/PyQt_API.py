# API to access PyQt modules either from PyQt6 or PyQt5
try:
  from PyQt6 import QtCore, QtWidgets, QtNetwork, QtGui
  from PyQt6.QtCore import Qt, QSize, QByteArray
  from PyQt6.QtGui import QPixmap, QImage, QGuiApplication, QClipboard
  from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkProxy, QNetworkRequest, QNetworkReply, QHttpMultiPart, QHttpPart
except Exception as e:
  try:
    from PyQt5 import QtCore, QtWidgets, QtNetwork, QtGui
    from PyQt5.QtCore import Qt, QSize, QByteArray
    from PyQt5.QtGui import QPixmap, QImage, QGuiApplication, QClipboard
    from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkProxy, QNetworkRequest, QNetworkReply, QHttpMultiPart, QHttpPart
  except Exception as e:
    print("Cannot find either PyQt6 or PyQt5")
    raise
