import base64
from enum import Enum
from ..PyQt_API import (QtCore, QtWidgets, QtGui, Qt)

class StartMode(Enum):
    UNKNOWN = 0
    CURA = 1
    PRUSA = 2
    STANDALONE = 3

PreviewModes = {
    "none": 0,
    "small": 50,
    "big": 100
}

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

class PreviewGenerator:
    def has_preview(self, rows):
        if rows is not None:
            for d in rows:
                if d.startswith(";SHUI PREVIEW"):
                    return True
        return False

    def generate_header(self, width, height, rows):
        rows.append(";SHUI PREVIEW {}x{}\n".format(width, height))

    def generate_data_preview(self, data, width, rows):
        index=0
        row = bytearray()
        for d in data:
            r=d[0]>>3
            g=d[1]>>2
            b=d[2]>>3
            rgb = (r << 11) | (g << 5) | b
            row.append((rgb >> 8) & 0xFF)
            row.append(rgb & 0xFF)
            index+=1
            if (index==width):
                index=0;
                rows.append(";" + base64.b64encode(row).decode('utf-8') + "\n")
                row = bytearray()

    def generate_image_preview(self, img, rows):
        self.generate_data_preview(img.getdata(), img.width, rows)

    def generate_qimage_preview(self, img, size, rows):
        b_image = img.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio)
        img_size = b_image.size()
        datasize = 0
        for i in range(img_size.height()):
          row = bytearray()
          for j in range(img_size.width()):
            pixel_color = b_image.pixelColor(j, i)
            r = pixel_color.red() >> 3
            g = pixel_color.green() >> 2
            b = pixel_color.blue() >> 3
            rgb = (r << 11) | (g << 5) | b
            row.append((rgb >> 8) & 0xFF)
            row.append(rgb & 0xFF)
          row = ";" + base64.b64encode(row).decode('utf-8') + "\n"
          rows.append(row)
    
    def generate_old_preview(self, preview, rows):
        size=preview.width
        index=0
        row = bytearray()
        for d in preview.getdata():
            r=d[0]>>3
            g=d[1]>>2
            b=d[2]>>3
            rgb = (r << 11) | (g << 5) | b
            row.append((rgb >> 8) & 0xFF)
            row.append(rgb & 0xFF)
            index+=1
            if (index==size):
                index=0;
                rows.append(";" + base64.b64encode(row).decode('utf-8') + "\n")
                row = bytearray()
