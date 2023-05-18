from .Core import GCodeSource, PreviewGenerator

class PrusaGCodeParser(GCodeSource):
    def __init__(self, app, preview, fileName):
        super().__init__(app, preview, PreviewGenerator())
        self.fileName=fileName

    def parse(self):
        # load oroginal gcode
        with open(self.fileName, "r", encoding="utf-8") as g_file:
            self.gcode=g_file.readlines()
        self.parseGcode()
