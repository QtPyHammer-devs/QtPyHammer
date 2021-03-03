# https://developer.valvesoftware.com/wiki/Valve_Texture_Format
import struct


colour_format = {
    0: "RGBA_8888",
    1: "ABGR_8888",
    2: "RGB_888",
    3: "BGR_888",
    4: "RGB_565",
    5: "I_8",
    6: "IA_88",
    7: "P_8",  # 8-bit paletted colour
    8: "A_8",
    9: "RGB_888_BLUESCREEN",
    10: "BGR_888_BLUESCREEN",
    11: "ARGB_8888",
    12: "BGRA_8888",
    13: "DXT1",
    14: "DXT3",
    15: "DXT5",
    16: "BGRX_8888",
    17: "BGRX_5551",
    18: "BGRA_4444",
    19: "DXT1_ONE_BIT_ALPHA",
    20: "BGRA_5551",
    21: "UV_88",
    22: "UVWQ_8888",
    23: "RGBA_16161616F",
    24: "RGBA_16161616",
    25: "UVLX_8888"}

colour_format_bpp = {0: 32, 1: 32,
                     2: 24, 3: 24, 4: 16,
                     5: 8, 6: 16, 7: 8, 8: 8,
                     9: 24, 10: 24,
                     11: 32, 12: 32,
                     13: 8, 14: 16, 15: 16,  # DXTs
                     16: 32, 17: 16, 18: 16,
                     19: 8, 20: 16, 21: 16, 22: 32,
                     23: 64, 24: 64, 25: 32}

flags = {
    0x00000001: "point_sample",  # GL_NEAREST, pixelate
    0x00000002: "trilinear",
    0x00000004: "clamp_s",
    0x00000008: "clamp_t",
    0x00000010: "anisotropic",
    0x00000020: "hint_dxt5",  # for seamless skybox edges
    0x00000040: "pwl_corrected",
    0x00000080: "normal",
    0x00000100: "no_mip",
    0x00000200: "no_lod",
    0x00000400: "all_MIPs",
    0x00000800: "procedural",
    0x00001000: "one_bit_alpha",
    0x00002000: "eight_bit_alpha",
    0x00004000: "env_map",
    0x00008000: "render_target",
    0x00010000: "depth_render_target",
    0x00020000: "no_debug_override",
    0x00040000: "single_copy",
    0x00080000: "pre_srgb",
    0x00800000: "no_depth_buffer",
    0x02000000: "clamp_u",
    0x04000000: "vertex_texture",
    0x08000000: "ssbump",
    0x20000000: "border"}


def rgb_565_to_888(colour):
    # colour is a 16-bit integer
    R = colour >> 11
    G = (colour >> 5) % 64
    B = colour % 32
    return bytes((R << 3, G << 2, B << 3))


def rgb_888_to_565(colour):
    # colour is a 16-bit integer
    R, G, B = colour
    R = R >> 3
    G = G >> 2
    B = B >> 3
    return ((R << 11) + (G << 5) + B).to_bytes(2, "little")


def decode_dxt1(bytestream, width, height):
    """returns a RGB_888 bytestring of length 12 * width, height"""
    if width % 4 != 0 or height % 4 != 0:  # input doesn't split into 4x4 tiles
        raise RuntimeError(f"Cannot decode into {width}x{height} size image")
    if len(bytestream) < width * height:  # not enough data to decode it all
        missing = (width * height) - len(bytestream)
        raise RuntimeError(f"Input is {missing} bytes short")
    out = [b""] * height
    start = 0
    for y in range(0, height, 4):
        for _ in range(0, width, 4):
            # RGB_565 palette (2x 16-bit colours)
            palette = bytestream[start:start + 4]
            c0, c1 = [rgb_565_to_888(c) for c in struct.unpack("2H", palette)]
            if c0 > c1:
                c2 = bytes([a * 2 // 3 + b // 3 for a, b in zip(c0, c1)])
                c3 = bytes([a // 3 + b * 2 // 3 for a, b in zip(c0, c1)])
            else:  # c0 <= c1
                c2 = bytes([a // 2 + b // 2 for a, b in zip(c0, c1)])
                c3 = b"\x00\x00\x00"
            c = (c0, c1, c2, c3)
            # 4x4px indexed tile
            tile = bytestream[start + 4:start + 8]
            for row_index, byte in enumerate(tile):  # 1 row of 2bpp colour indices
                A = byte % 4
                B = (byte >> 2) % 4
                C = (byte >> 4) % 4
                D = byte >> 6
                pixels = b"".join([c[i] for i in (A, B, C, D)])
                out[y + row_index] = b"".join((out[y + row_index], pixels))
                # ^ stitch into one byestring
            start += 8
    out = b"".join(out)
    return out


def decode_dxt5(dxt5_data: bytes) -> bytes:
    # https://en.wikipedia.org/wiki/S3_Texture_Compression#DXT4_and_DXT5
    # TODO: decode more than one tile and stitch tiles together
    # a0, a1: int  # 8bit alpha pallet pixel
    # alpha_lut: bytes  # 3-bit 4x4 lookup table (6 bytes)
    # c0, c1: int  # 565RGB pallet pixel
    # colour_lut: bytes  # 2-bit 4x4 lookup table (4 bytes)

    alpha, colour = struct.unpack("2B6s2H4s", dxt5_data)
    a0, a1, alpha_lut = alpha
    c0, c1, colour_lut = colour
    # calculate a2 - a7 (alpha palette)
    if a0 > a1:
        a2, a3, a4, a5, a6, a7 = [((6 - i) * a0 + (1 + i) * a1) // 7 for i in range(6)]
    else:
        a2, a3, a4, a5 = [((4 - i) * a0 + (1 + i) * a1) // 5 for i in range(4)]
        a6 = 0
        a7 = 255
    alpha_palette = [a0, a1, a2, a3, a4, a5, a6, a7]
    # calculate c2 & c3 (colour palette)
    c0, c1 = map(lambda c: [(c >> 11) << 3, ((c >> 5) % 64) << 2, (c % 32) << 3], [c0, c1])
    # ^ 565RGB to 888RGB
    if c0 > c1:
        c2 = [a * 2 // 3 + b // 3 for a, b in zip(c0, c1)]
        c3 = [a // 3 + b * 2 // 3 for a, b in zip(c0, c1)]
    else:  # c0 <= c1
        c2 = [a // 2 + b // 2 for a, b in zip(c0, c1)]
        c3 = [0, 0, 0]
    colour_palette = [c0, c1, c2, c3]
    # lookup tables --> pixels
    alpha_lut = int.from_bytes(alpha_lut, "big")
    colour_lut = int.from_bytes(colour_lut, "big")
    pixels = []
    for i in range(16):
        colour = colour_palette[colour_lut % 4]
        alpha = alpha_palette[alpha_lut % 8]
        pixels.append(bytes([*colour, alpha]))
        colour_lut = colour_lut >> 2
        alpha_lut = alpha_lut >> 3
    return b"".join(reversed(pixels))


class Vtf:
    """Read-only importer for Valve Texture File Format"""
    def __init__(self, filename):
        self.file = open(filename, "rb")

        def unpack(f):
            """always returns a tuple, sometimes of len(1)"""
            return struct.unpack(f, self.file.read(struct.calcsize(f)))

        assert unpack("4s")[0] == b"VTF\x00"
        major_version, minor_version = unpack("2I")
        assert major_version == 7
        if minor_version > 2:
            raise NotImplementedError(f"Can't decode v7.{minor_version} VTF")
        self.version = (major_version, minor_version)
        self.header_size = unpack("I")[0]
        self.width, self.height = unpack("2H")
        self.flags = unpack("I")[0]
        self.flag_names = {flags[f] for f in flags if self.flags & f}
        self.frame_count, self.first_frame = unpack("2H4x")
        self.reflectivity = unpack("3f4x")
        self.bumpmap_scale, self.format = unpack("fI")
        # format name = colour_format[high_res_format]
        self.mipmap_count = unpack("B")[0]
        thumbnail_format, self.thumbnail_width, self.thumbnail_height = unpack("I2B")
        assert thumbnail_format == 13  # DXT1
        if minor_version >= 2:  # v7.2+
            self.depth = unpack("H")[0]  # Z-slices
        if minor_version >= 3:  # v7.3+
            ...  # NotImplemented
            # until you hit the header size:
            # resource entries [unpack("3sBI")]
            # -- 3s = tag; e.g. b"\x01\x00\x00" or b"CRC"
            # ----- known tags:
            #    --  b"\x01\x00\x00" Thumbnail
            # -- B = flags; 0x2 = no data chunk (then offset = data?)
            # -- I = offset; file.seek(offset); file.read(?) for data

    def __del__(self):
        self.file.close()

    @property
    def thumbnail(self):
        """returns the decoded thumbnail"""
        self.file.seek(self.header_size)  # maybe elsewhere if v7.3+
        width, height = self.thumbnail_width, self.thumbnail_height
        thumb = self.file.read(width * height)
        return decode_dxt1(thumb, width, height)

    def load_thumbnail(self):
        width, height = self.thumbnail_width, self.thumbnail_height
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, self.thumbnail)
        # ^ target, mipmap, gpu_format, width, height, border, data_format
        # -- data_size, data
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    def mipmap(self, index):
        if index < 0:
            raise RuntimeError("Invalid mipmap index")
        no_mips = bool(self.flags & 0x100)
        if no_mips and index > 0:
            raise RuntimeError("File only has one mipmap")
        if index > self.mipmap_count - 1:
            raise RuntimeError(f"Mipmap {index} not in file")
        bytes_per_pixel = colour_format_bpp[self.format] // 8

        def size(w, h):
            return w * h * bytes_per_pixel

        offset = 0
        for i in range(self.mipmap_count - 1 - index):
            mipmap_width = self.width >> i
            mipmap_height = self.height >> i
            print(f"skipping {mipmap_width}x{mipmap_height}")
            offset += size(mipmap_width, mipmap_height)
        thumbnail_size = self.thumbnail_width * self.thumbnail_height
        thumbnail_end = 80 + thumbnail_size
        self.file.seek(thumbnail_end + offset)
        mipmap_width = self.width >> index
        mipmap_height = self.height >> index
        data = self.file.read(size(mipmap_width, mipmap_height))
        return mipmap_width, mipmap_height, data

    def load_mipmaps(self):
        # https://github.com/LogicAndTrick/sledge-formats/blob/master/Sledge.Formats.Texture/Vtf/VtfFile.cs#L130
        # NOTE: not all VTFs have frames, faces or z_slices
        # seek to start
        size_of_thumbnail = self.thumbnail_width * self.thumbnail_height
        end_of_thumbnail = 80 + size_of_thumbnail
        self.file.seek(end_of_thumbnail)
        # for each...
        # mipmaps: smallest to largest
        # -- frames: first to last
        # ---- faces: first to last (???)
        # ------ slices: min to max (range(depth))
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, self.mipmap_count - 1)
        for i in range(self.mipmap_count - 1, 0, -1):  # SMALLEST TO LARGEST
            # ^ stops at 256x256px, not 512x512?
            width = self.width >> i
            height = self.height >> i
            if width < 4:
                data = self.file.read(16)
                pixels = decode_dxt1(data, 4, 4)  # RGB_888
                # pixel = bytes([int(255 * x) for x in self.reflectivity])
                # pixels = pixel * width * height
            else:
                data = self.file.read(width * height)
                pixels = decode_dxt1(data, width, height)  # RGB_888
            if i == 0:
                print(pixels)
            glTexImage2D(GL_TEXTURE_2D, i, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, pixels)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            # ^ forces texture to use base mipmap
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_BASE_LEVEL, 3)
            # ^ sets base mipmap (default == 0)
        print(bool(glGetTexParameteriv(GL_TEXTURE_2D, GL_TEXTURE_RESIDENT)))
        # ^ is texture mipmap complete?
        # https://www.khronos.org/opengl/wiki/Texture#Texture_completeness
        end = self.file.tell()
        self.file.read()
        true_end = self.file.tell()
        print(true_end - end, "bytes left")


if __name__ == "__main__":
    import sys

    from OpenGL.GL import *
    from OpenGL.GL.shaders import compileShader, compileProgram
    from PyQt5 import QtCore, QtWidgets

    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)
    sys.excepthook = except_hook  # Python Qt Debug

    app = QtWidgets.QApplication([])

    materials = "../../test_materials"
    test_vtf = Vtf(f"{materials}/test.vtf")
    # test_vtf = vtf(f"{materials}/customdev/dev_measuregeneric01green.vtf")
    # test_vtf = vtf(f"{materials}/test_materials/customdev/dev_measurewall01green.vtf")

    class viewport(QtWidgets.QOpenGLWidget):
        def __init__(self):
            super(viewport, self).__init__(parent=None)
            self.mipmap = test_vtf.mipmap_count - 1

        def keyPressEvent(self, event):
            key = event.key()
            if key == QtCore.Qt.Key_Left:
                self.mipmap = max(self.mipmap - 1, 0)
            elif key == QtCore.Qt.Key_Right:
                self.mipmap = min(self.mipmap + 1, test_vtf.mipmap_count - 1)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_BASE_LEVEL, self.mipmap)
            # no visible changes occur /;

        def initializeGL(self):
            glClearColor(.25, .25, .25, 1.0)
            # test_vtf.load_thumbnail() # <-- TESTED
            # test_vtf.load_mipmaps()
            # width, height, data = test_vtf.mipmap(8)
            thumb_size = test_vtf.thumbnail_width * test_vtf.thumbnail_height
            thumb_end = 80 + thumb_size
            test_vtf.file.seek(thumb_end)
            width, height = 8, 5  # why does this look close to right?
            data = test_vtf.file.read()
            print(colour_format[test_vtf.format], f"{width}x{height}")
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB,
                         GL_UNSIGNED_BYTE, data)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

            vertex_source = """#version 450 core
layout(location = 0) in vec3 vertexPosition;
out vec3 position;
void main() {
    position = vertexPosition;
    gl_Position = vec4(vertexPosition, 1); }"""
            fragment_source = """#version 300 es
layout(location = 0) out mediump vec4 outColour;
in mediump vec3 position;
uniform sampler2D albedo;
void main() {
    outColour = texture(albedo, vec2(position.x, -position.y)); }"""
            vertex = compileShader(vertex_source, GL_VERTEX_SHADER)
            fragment = compileShader(fragment_source, GL_FRAGMENT_SHADER)
            shader = compileProgram(vertex, fragment)
            glLinkProgram(shader)
            glUseProgram(shader)

        def paintGL(self):
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glBegin(GL_QUADS)
            glVertex(0, 1)
            glVertex(1, 1)
            glVertex(1, 0)
            glVertex(0, 0)
            glEnd()

    window = viewport()
    window.setGeometry(128, 64, 576, 576)
    window.show()
    app.exec_()
