import struct

class Header:
    def __init__(self, input):
        self.magic = None #char magic[4]; // magic
        self.width = None #uint32_t width in pixels(BE)
        self.height = None #uint32_t height in pixels(BE)
        self.channels = None #channels; // 3 = RGB, 4 = RGBA
        self.colorspace = None #uint8_t colorspace; // 0 = sRGB with linear alpha // 1 = all channels linear
        self.magic, self.width, self.height, self.channels, self.colorspace = struct.unpack(">4sIIcc", input[0:14])
        self.magic = self.magic.decode()
        if self.magic!="qoif":
            raise Exception("Is not qoi stream")

        self.size = 14
        pass

class QOIReader:
    def __init__(self, input):
        self.input = input
        self.header = Header(input)
        self.palette = [(0, 0, 0, 255) for i in range(64)]
        self.cursor = self.header.size
        self.readed = 0
        self.prev = (0, 0, 0, 255)
        self.wanted = self.header.width * self.header.height
        self.pixel_writer = None

    def set_color(self, color, save_pallete=True):
        self.pixel_writer(color)

        if save_pallete:
            def hash(color):
                r, g, b, a = color
                return (r * 3 + g * 5 + b * 7 + a * 11) & 0b111111
            self.palette[hash(color)] = color
        self.readed = self.readed + 1
        self.prev = color
        pass

    def rgb(self):
        self.set_color(
            (
                self.input[self.cursor],
                self.input[self.cursor + 1],
                self.input[self.cursor + 2],
                255
            )
        )
        self.cursor = self.cursor + 3
        pass

    def rgba(self):
        self.set_color(
            (
                self.input[self.cursor],
                self.input[self.cursor + 1],
                self.input[self.cursor + 2],
                self.input[self.cursor + 3]
            )
        )
        self.cursor = self.cursor + 4
        pass

    def index(self, tag):
        color = self.palette[tag & 0b111111]
        self.set_color(color, False)
        pass

    def diff(self, tag):
        dr = ((tag & 0b00110000) >> 4) - 2
        dg = ((tag & 0b00001100) >> 2) - 2
        db = ((tag & 0b00000011) >> 0) - 2
        (r, g, b, a) = self.prev
        self.set_color((r + dr, g + dg, b + db, a))
        pass

    def luma(self, tag):
        dg = (tag & 0b00111111) - 32
        drg = (self.input[self.cursor] & 0b11110000) >> 4
        dbg = (self.input[self.cursor] & 0b00001111) >> 0
        (r, g, b, a) = self.prev
        self.set_color((r + dg - 8 + drg, g + dg, b + dg - 8 + dbg, a))
        self.cursor = self.cursor + 1
        pass

    def run(self, tag):
        for i in range((tag & 0b00111111) + 1):
            self.set_color(self.prev, False)
        pass

    def read_chunk(self):
        tag = self.input[self.cursor]
        self.cursor = self.cursor + 1
        if tag==0 and (self.input[self.cursor:self.cursor+7]==b'\0\0\0\0\0\0\1'):
            return False
        if tag == 0b11111110:
            self.rgb()
        elif tag == 0b11111111:
            self.rgba()
        else:
            tag_mark = tag & 0b11000000
            if tag_mark == 0b00000000:
                self.index(tag)
            elif tag_mark == 0b01000000:
                self.diff(tag)
            elif tag_mark == 0b10000000:
                self.luma(tag)
            elif tag_mark == 0b11000000:
                self.run(tag)
        return True

    def do_read(self):
        while self.readed < self.wanted and self.read_chunk():
            pass
        pass

    def image_writer(self, color):
        self.img.putpixel(
            (self.readed % self.header.width, int(self.readed / self.header.width)),
            color
        )

    def array_writer(self, color):
        self.img[self.readed] = color

    def asImage(self):
        from PIL import Image

        self.img = Image.new(
            mode = "RGB" if self.header.channels == 3 else "RGBA",
            size = (self.header.width, self.header.height)
        )

        self.pixel_writer = self.image_writer
        self.do_read()

        return self.img

    def asArray(self):
        self.img = [None for i in range(self.header.width * self.header.height)]
        self.pixel_writer = self.array_writer
        self.do_read()
        return self.img

