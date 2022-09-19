import re
from PIL import Image
import base64
from io import BytesIO
from ..PyQt_API import (Qt, QPixmap, QImage, QSize)
from .Core import GCodeSource, PreviewGenerator, PreviewModes

class PrusaGCodeParser(GCodeSource):
    large_preview=None
    small_preview=None
    image_format=None

    def __init__(self, fileName):
        super().__init__()
        self.gcode=None
        self.thumbs=[]
        self.fileName=fileName
        self.gen = PreviewGenerator()

    def getLargePreview(self):
        im = None
        if self.large_preview is not None:
            im = self.large_preview
        elif self.small_preview is not None:
            im = self.small_preview.resize((200, 200))
        else:
            return None

        if im is not None:
            im = im.convert("RGBA")
            data = im.tobytes("raw","RGBA")
            qim = QImage(data, im.size[0], im.size[1], QImage.Format.Format_ARGB32)
            return QPixmap.fromImage(qim)
        return None

    def getDefaultPreview(self):
        qpm = QPixmap(QSize(200, 200))
        qpm.fill(Qt.GlobalColor.black)
        return qpm

    def makeImageForQOI(self, bytes):
        import qoi
        im = qoi.decode(bytes)
        image = Image.fromarray(im)
        return image

    def parse(self):
        self.image_format=None
        self.large_preview=None
        self.small_preview=None

        with open(self.fileName, "r", encoding="utf-8") as g_file:
            self.gcode=g_file.readlines()
            g_file.close()
        current_thumb=None

        index=0
        for d in self.gcode:
            index+=1
            if current_thumb is None:
                if d.startswith("; thumbnail"):
                    if d.startswith("; thumbnail begin") or d.startswith("; thumbnail_PNG begin"):
                        self.image_format="PNG"
                    elif d.startswith("; thumbnail_JPG begin"):
                        self.image_format="JPG"
                    elif d.startswith("; thumbnail_QOI begin"):
                        self.image_format="QOI"
                    else:
                        # unsupported preview image format
                        continue
                    current_thumb = {"base64": "", "start_row": index - 1}
                    self.thumbs.append(current_thumb)
                    continue
            if (current_thumb is not None) and (d.startswith("; thumbnail end") or d.startswith("; thumbnail_"+self.image_format+" end")):
                current_thumb["end_row"] = index - 1
                current_thumb=None
                continue
            if current_thumb is not None:
                str=d.strip()[2:]
                current_thumb["base64"]+=str

        for t in self.thumbs:
            image = None
            try:
                bytes = base64.b64decode(t["base64"])
                if (self.image_format == "QOI"):
                    image = self.makeImageForQOI(bytes)
                else:
                    with BytesIO(bytes) as stream:
                        with Image.open(stream) as im:
                            image = im.convert("RGB")
            except:
                continue

            if image and (image.height == image.width):
                if image.height == 200:
                    self.large_preview=image
                elif (image.height == 100) or (image.height == 50):
                    self.small_preview=image

    def dummy_filter(self, idx):
        return True

    def thumb_filter(self, idx):
        for t in self.thumbs:
            if (t["start_row"]<=idx) and (t["end_row"]>=idx):
                return False
        return True

    def getProcessedGcode(self, preview_mode):
        if self.gcode is None:
            return None
        small_size = PreviewModes.get(preview_mode, 0)
        rows=[]
        filter_proc=self.dummy_filter
        if (small_size > 0) and (self.large_preview is not None) and (self.small_preview is not None):
            filter_proc=self.thumb_filter
            self.gen.generate_header(self.small_preview.width, self.small_preview.width, rows)
            self.gen.generate_image_preview(self.small_preview, rows)
            self.gen.generate_image_preview(self.large_preview, rows)
        index=0
        for d in self.gcode:
            if filter_proc(index):
                rows.append(d)
            index+=1
        return rows
