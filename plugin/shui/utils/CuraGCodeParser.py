from .Core import GCodeSource, PreviewGenerator, PreviewModes

class CuraGCodeParser(GCodeSource):
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

    def getProcessedGcode(self, preview_mode):
        small_size = PreviewModes.get(preview_mode, 0)
        if not self.has_preview and (small_size > 0) \
                and (self.large_preview is not None) and (self.gcode is not None):
            rows = []
            self.gen.generate_header(small_size, small_size, rows)
            self.gen.generate_qimage_preview(self.large_preview, small_size, rows)
            self.gen.generate_qimage_preview(self.large_preview, self.large_size, rows)
            for d in self.gcode:
                rows.append(d)
            return rows
        return self.gcode
