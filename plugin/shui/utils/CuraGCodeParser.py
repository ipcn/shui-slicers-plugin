from .Core import GCodeSource, PreviewGenerator

class CuraGCodeParser(GCodeSource):
    small_size = 50
    large_size = 200
    large_preview = None
    has_preview = False
    
    def __init__(self):
        super().__init__()
        self.gcode = None
        self.gen = PreviewGenerator()

    def parse(self):
        from UM.Application import Application
        app_instance=Application.getInstance()
        gcode_dict = getattr(app_instance.getController().getScene(), "gcode_dict", None)
        self.gcode = gcode_dict.get(app_instance.getMultiBuildPlateModel().activeBuildPlate, None)
        from .Core import PreviewGenerator
        self.has_preview = self.gen.has_preview(self.gcode)
        from cura.Snapshot import Snapshot
        self.large_preview = Snapshot.snapshot(width = self.large_size, height = self.large_size)

    def getLargePreview(self):
        if self.large_preview == None:
            return None
        from ..PyQt_API import QPixmap
        return QPixmap.fromImage(self.large_preview)

    def getProcessedGcode(self):
        if self.has_preview or (self.large_preview is None) or (self.gcode is None):
            return self.gcode
        else:
            rows = []
            self.gen.generate_header(self.small_size, self.small_size, rows)
            self.gen.generate_qimage_preview(self.large_preview, self.small_size, rows)
            self.gen.generate_qimage_preview(self.large_preview, self.large_size, rows)
            for d in self.gcode:
                rows.append(d)
            return rows
