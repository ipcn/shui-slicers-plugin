from .Core import GCodeSource, PreviewGenerator

class CuraGCodeParser(GCodeSource):
    def __init__(self, app, preview):
        super().__init__(app, preview, PreviewGenerator())

    def parse(self):
        # get original gcode
        from UM.Application import Application
        app_instance=Application.getInstance()
        gcode_dict = getattr(app_instance.getController().getScene(), "gcode_dict", None)
        gcode = gcode_dict.get(app_instance.getMultiBuildPlateModel().activeBuildPlate, None)
        self.gcode=[]
        for d in gcode:
            lines = d.split("\n")
            for d in lines:
                self.gcode.append(d + "\n")
        # parse gcode
        self.parseGcode(False)
        # get scene snapshot and store in preview
        large_size = self.gen.large_size
        from cura.Snapshot import Snapshot
        # QImage qimg
        qimg = Snapshot.snapshot(width = large_size, height = large_size)
        if qimg is not None:
            self.preview.setImage(qimg)
        pass
