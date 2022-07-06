from enum import Enum
from ..PyQt_API import (QtCore, QtWidgets, QtGui)

class StartMode(Enum):
    UNKNOWN = 0
    CURA = 1
    PRUSA = 2
    STANDALONE = 3


class UiTab(QtWidgets.QWidget):
    view_connect=False
    def __init__(self, app):
        super().__init__()
        self.app=app
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

class GCodeSource:
    def __init__(self):
        pass

    def getProcessedGcode(self) -> None: ...

    def parse(self) -> None: ...

    def getLargePreview(self) -> None: ...

