import base64
from enum import Enum
from ..PyQt_API import (Qt, QtWidgets, Qt, QGuiApplication, QImage, QPixmap, QSize)

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
    def __init__(self, app, preview, preview_gen):
        self.app = app
        self.preview = preview
        self.gcode = None
        self.rows = []
        self.gen = preview_gen
        self.preview = preview
        pass

    def getKeepAspectRatio(self):
        return self.app.config.get("keepPreviewAspectRatio")
    
    def getPreviewMode(self):
        return self.app.config.get("preview")

    def getProcessedGcode(self):
        preview_mode = self.getPreviewMode()
        keep_acpect_ratio = self.getKeepAspectRatio()
        return self.gen.generateAllGcode(self.rows, self.preview, preview_mode, keep_acpect_ratio)

    def makeImageForSHUI(self, data, out_size):
        image = self.gen.restoreShuiPreview(data, out_size)
        return image

    def makeImageForQOI(self, data):
#        format = "QOI"
#        qimg = QImage()
#        qimg.loadFromData(data, format)
        import qoi
        im = qoi.decode(data)
#        format = QImage.Format.Format_ARGB32
        format = QImage.Format.Format_RGBA8888
        qimg = QImage(im, im.shape[0], im.shape[1], format)
        return qimg

    def makeImageForQOI_PIL(self, data):
        from PIL import Image
        import qoi
        im = qoi.decode(data)
        img = Image.fromarray(im)
        qimg = self.convertPILtoQImage(img)
        return qimg

    def convertPILtoQImage(self, img):
#        img = img.convert("RGBA")
        data = img.tobytes("raw","RGBA")
        format = QImage.Format.Format_ARGB32
        qimg = QImage(data, img.size[0], img.size[1], format)
        return qimg

    def parseGcode(self, extract=True):
        self.image_format=None
        self.rows=[]

        # clear initial preview
        self.preview.setImage(None)
        preview_mode = self.getPreviewMode()
        img_size=PreviewModes.get(preview_mode, 0)
        preserve=(img_size <= 0)

        thumbs=[]
        current_thumb=None
        image_format=None
        shui_thumb_size=0
        shui_thumb_line=0

        # parse gcode lines and extract thumpbnails
        index=0
        for d in self.gcode:
#            raise Exception("loop: index=" + str(index) + " len=" + str(len(self.gcode)) + " str=" + d)
            index+=1
            if current_thumb is None:
                if (d.startswith("; thumbnail") and not d.startswith("; thumbnails")) or d.startswith(";SHUI PREVIEW"):
                    if d.startswith("; thumbnail begin") or d.startswith("; thumbnail_PNG begin"):
                        image_format="PNG"
                    elif d.startswith("; thumbnail_JPG begin"):
                        image_format="JPG"
                    elif d.startswith("; thumbnail_QOI begin"):
                        image_format="QOI"
                    elif d.startswith(";SHUI PREVIEW 100x100"):
                        image_format="SHUI-100"
                        shui_thumb_size=100+200
                        shui_thumb_line=0
                    elif d.startswith(";SHUI PREVIEW 50x50"):
                        image_format="SHUI-50"
                        shui_thumb_size=50+200
                        shui_thumb_line=0
                    else:
                        # unsupported preview image format
                        print("Unsupported preview image format: " + d)
                        continue
                    current_thumb = {"format": image_format, "base64": "", "bytes": bytearray(), "start_row": index - 1}
                    thumbs.append(current_thumb)
                    continue
            if (current_thumb is not None) and (d.startswith("; thumbnail end") or d.startswith("; thumbnail_"+image_format+" end")):
                current_thumb["end_row"] = index - 1
                current_thumb=None
                continue
            if (current_thumb is not None) and (shui_thumb_size > 0) and (shui_thumb_line >= shui_thumb_size):
                current_thumb["end_row"] = index - 1
                shui_thumb_size = 0
                shui_thumb_line = 0
                current_thumb=None
            if current_thumb is not None:
                if (shui_thumb_size > 0):
                    s=d.strip()[1:]
                    b=base64.b64decode(s)
                    current_thumb["bytes"]+=b
                    shui_thumb_line += 1
                else:
                    s=d.strip()[2:]
                    current_thumb["base64"]+=s
            # keep all or only non-thumpbnail rows
            if preserve or (current_thumb is None):
                self.rows.append(d)

        # skip handling thumbnails if requested
        if not extract:
            return

        # covert thubnails to image and save largest in preview
        for t in thumbs:
            qimg = None
            try:
                # konvert to PIL Image
                data = t["bytes"]
                format = t["format"]
                if len(t["base64"]) > 0:
                    data = base64.b64decode(t["base64"])
                if (t["format"] == "SHUI-100"):
                    qimg = self.makeImageForSHUI(data, 100)
                elif (t["format"] == "SHUI-50"):
                    qimg = self.makeImageForSHUI(data, 50)
                elif (t["format"] == "QOI"):
                    qimg = self.makeImageForQOI(data)
                else:
                    qimg = QImage()
                    if not qimg.loadFromData(data, format):
                        print("Failed create preview of ", format)
                        qimg = None
            except Exception as e:
                print("Exception in creating preview:", str(e))
#                raise
                continue

            # save largest image in preview
            if qimg is not None:
                pr = self.preview.getImage()
                if (pr is None) or (pr.height() < qimg.height()):
                    self.preview.setImage(qimg, t["format"])
        pass

    def parse(self) -> None: ...

class Preview:
    # QImage image
    image = None
    format = None

    def getAspectRatioMode(self, keep_aspect_ratio=True):
        ratio_mode = Qt.AspectRatioMode.KeepAspectRatio
        if not keep_aspect_ratio:
            ratio_mode = Qt.AspectRatioMode.IgnoreAspectRatio
        return ratio_mode

    def getFormat(self):
        return self.format

    def setImage(self, qimg, format=None):
        self.image = qimg
        self.format = format
    
    def getImage(self):
        return self.image

    def getScaledImage(self, width, height, ratio=Qt.AspectRatioMode.KeepAspectRatio):
        qimg = self.image.scaled(width, height, ratio)
        return qimg

    def getVisualPixmap(self, width, height, keep_aspect_ratio=True):
        pixmap = None
        if self.image:
            ratio_mode = self.getAspectRatioMode(keep_aspect_ratio)
            qimg = self.getScaledImage(width, height, ratio_mode)
            pixmap = QPixmap.fromImage(qimg)
        else:
            pixmap = QPixmap(QSize(width, height))
            pixmap.fill(Qt.GlobalColor.black)
        return pixmap

    def loadFromFile(self, path):
        qimg = QImage()
        if qimg.load(path):
            format = str(qimg.format())
            self.setImage(qimg, format)
        else:
            raise Exception("Cannot read image from file")
        pass

    def loadFromClipboard(self):
        clipboard = QGuiApplication.clipboard()
        mimeData = clipboard.mimeData()
        if mimeData.hasImage():
            # QImage qimg
            qimg = mimeData.imageData()
            if qimg:
                self.setImage(qimg, "cliboard")
        else:
            raise Exception("No image in clipboard")
        pass

class PreviewGenerator:
    large_size = 200
    def generateAllGcode(self, gcode_rows, preview, preview_mode, keep_sapect_ratio):
        rows=[]
        # generate preview if required
        out_size=PreviewModes.get(preview_mode, 0)
        generate=(out_size > 0)
        if generate:
            ratio_mode = preview.getAspectRatioMode(keep_sapect_ratio)
            if preview.getImage() is not None:
                self.generateHeaderPreview(out_size, rows)
                self.generateImagePreview(out_size, preview, ratio_mode, rows)
                self.generateImagePreview(self.large_size, preview, ratio_mode, rows)
                self.generateFooterPreview(out_size, rows)
        # copy filtered gcode
        if gcode_rows is not None:
            for d in gcode_rows:
                rows.append(d)
        return rows

    def generateHeaderPreview(self, out_size, rows):
        rows.append(";SHUI PREVIEW {}x{}\n".format(out_size, out_size))

    def generateFooterPreview(self, out_size, rows):
        rows.append(";End of SHUI PREVIEW\n")

    def generateImagePreview(self, out_size, preview, ratio_mode, rows):
        qimg = preview.getScaledImage(out_size, out_size, ratio_mode)
        img_size = qimg.size()
        # calculate margins to center image inside bounds
        y_size = img_size.height()
        x_size = img_size.width()
        y_shift = (out_size - y_size) // 2
        x_shift = (out_size - x_size) // 2
        if y_shift < 0: y_shift = 0
        if x_shift < 0: x_shift = 0
        # itarate over all pixels inside bounds
        for y in range(out_size):
          row = bytearray()
          for x in range(out_size):
            # use black for pixels outside image
            y_idx = y - y_shift
            x_idx = x - x_shift
            r = 0
            g = 0
            b = 0
            # get real color for pixels inside image
            if (0 <= y_idx < y_size) and (0 <= x_idx < x_size):
                pixel_color = qimg.pixelColor(x_idx, y_idx)
                r = pixel_color.red() >> 3
                g = pixel_color.green() >> 2
                b = pixel_color.blue() >> 3
            # convert to double-byte RGB565
            rgb = (r << 11) | (g << 5) | b
            row.append((rgb >> 8) & 0xFF)
            row.append(rgb & 0xFF)
          row = ";" + base64.b64encode(row).decode('utf-8') + "\n"
          rows.append(row)

    def restoreShuiPreview(self, data, out_size):
        full_size = (out_size*out_size + self.large_size*self.large_size) * 2
        if len(data) < full_size:
            raise Exception("Too few bytes for SHUI preview: " + str(len(data)))
        # drop small head part
        data = data[out_size*out_size*2:]
        buf = bytearray(self.large_size*self.large_size*4)
        # parse big tail part
        for i in range(0, self.large_size):
            for j in range(0, self.large_size):
                idx = (i*self.large_size + j)*2
                rgb = (data[idx] & 0xFF) << 8 | (data[idx+1] & 0xFF)
                r = ((rgb >> 11) & 0b11111) << 3
                g = ((rgb >> 5) & 0b111111) << 2
                b = ((rgb) & 0b11111) << 3
                #data.append(r)
                #data.append(g)
                #data.append(b)
                k=(i*self.large_size + j)*4
                buf[k] = b
                buf[k+1] = g
                buf[k+2] = r
                buf[k+3] = 0xFF
        qimg = QImage(buf, self.large_size, self.large_size, QImage.Format.Format_RGB32)
        return qimg
