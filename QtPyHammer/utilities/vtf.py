# https://developer.valvesoftware.com/wiki/Valve_Texture_Format
import struct


colour_format = {
    0: "RGBA_8888",
    1: "ABGR_8888",
    2: "RGB_888",
    3: "BGR_888",
    4: "RGB_565",
    5: "I8",
    6: "IA88",
    7: "P8", # 8-bit paletted colour
    8: "A8",
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


# flags
flags = {
    0x00000001: "point_sample", # GL_NEAREST, pixelate
    0x00000002: "trilinear",
    0x00000004: "clamp_s",
    0x00000008: "clamp_t",
    0x00000010: "anisotropic",
    0x00000020: "hint_dxt5", # for seamless skybox edges
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

def DXT1_decode(bytestream, width, height):
    out = [[b""] * width] * height # 1 x RGB_888 bytestring per pixel
    # ^ TEST NEW OUTPUT WITH OPENGL
    start = 0
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            # RGB_565 palette (2x 16-bit colours)
            palette = bytestream[start : start + 4]
            c0, c1 = [rgb_565_to_888(c) for c in struct.unpack("2H", palette)]
            if c0 > c1:
                c2 = bytes([a * 2 // 3 + b // 3 for a, b in zip(c0, c1)])
                c3 = bytes([a // 3 + b * 2 // 3 for a, b in zip(c0, c1)])
            else: # c0 <= c1
                c2 = bytes([a // 2 + b // 2 for a, b in zip(c0, c1)])
                c3 = b"\x00\x00\x00"
            c = (c0, c1, c2, c3)
            # 4x4px indexed tile
            tile = bytestream[start + 4 : start + 8]
            for row_index, byte in enumerate(tile): # 1 row of 2bpp colour indices
                A = byte % 4
                B = (byte >> 2) % 4
                C = (byte >> 4) % 4
                D = byte >> 6
                pixels = [c[i] for i in (A, B, C, D)]
                out = out[y + row_index][x : x + 4] = pixels
                # ^ stitch into one byestring
            start += 8
    return out

class vtf:
    """Read-only importer for Valve Texture File Format"""
    def __init__(self, filename):
        self.file = open(filename, "rb")
        unpack = lambda f: struct.unpack(f, self.file.read(struct.calcsize(f)))
        assert unpack("4s") == b"VTF\x00"
        major_version, minor_version = unpack("2I")
        assert major_version == 7
        if minor_version > 2:
            raise NotImplementedError(f"Can't decode v7.{minor_version} VTF")
        self.version = (major_version, minor_version)
        self.header_size = unpack("I")
        self.width, self.height = unpack("2H")
        self.flags = unpack("I")
        self.flag_names = {flags[f] for f in self.flags if self.flags & f}
        self.frame_count, self.first_frame = unpack("2H4x")
        self.reflectivity = unpack("3f4x")
        self.bumpmap_scale, high_res_format = unpack("fI")
        self.format = colour_format[high_res_format]
        self.mipmap_count = unpack("B")[0]
        thumbnail_format, self.thumbnail_width, self.thumbnail_height = unpack("I2B")
        assert thumbnail_format == DXT1
        if minor_version >= 2: # v7.2+
            depth = unpack("H") # Z-slices
        if minor_version >= 3: # v7.3+
            ... # NotImplemented
            # until you hit the header size:
            # resource entries [unpack("3sBI")]
            # -- 3s = tag; e.g. b"\x01\x00\x00" or b"CRC"
            # ----- known tags:
            #    --  b"\x01\x00\x00" Thumbnail
            # -- B = flags; 0x2 = no data chunk (then offset = data?)
            # -- I = offset; file.seek(offset); file.read(?) for data

    def __del__(self):
        self.file.close()
        super(v7_2, self).__del__()

    @property
    def thumbnail(self):
        """returns the decoded thumbnail"""
        self.file.seek(self.header_size) # maybe elsewhere if v7.3+
        width, height = self.thumbnail_width, self.thumbnail_height
        thumb = self.file.read(width * height // 2)
        return DXT1_decode(thumb, width, height, 16)

    def mipmap(index, frame=0, face=0, z_slice=0):
        # NOTE: not all VTFs have frames, faces or z_slices
        size_of_thumbnail = self.thumbnail_width * self.thumbnail_height, 16 // 2
        end_of_thumbnail = 80 + size_of_thumbnail
        file.seek(end_of_thumbnail)
        # add a value based on encoding, format & mipmapsize / count
        # each mipmap is half in either dimension
        # note mipmap_count, frame_count, depth & cubemap flags
        raise NotImplementedError()
        # for each...
        # mipmaps: smallest to largest
        #-- frames: first to last
        #---- faces: first to last (???)
        #------ slices: min to max (range(depth))


if __name__ == "__main__":
    import sys

    from OpenGL.GL import *
    from OpenGL.GL.shaders import compileShader, compileProgram
    from PyQt5 import QtWidgets


    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)
    sys.excepthook = except_hook # Python Qt Debug

    app = QtWidgets.QApplication([])
    class viewport(QtWidgets.QOpenGLWidget):
        def __init__(self):
            super(viewport, self).__init__(parent=None)
        
        def initializeGL(self):
            data = b"\xFF\x00\xFF\x00\x00\x00" * 2
            data += bytes(reversed(data)) # invert every second row
            data *= 2
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 4, 4, 0, GL_RGB,
                         GL_UNSIGNED_BYTE, data)
            # ^ target, mipmap, gpu_format, width, height, border, data_format
            # -- data_size, data
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            vertex_source = """#version 450 core
layout(location = 0) in vec3 vertexPosition;
out vec3 position;
void main() {
    position = vertexPosition;
    gl_Position = vec4(vertexPosition, 1); }"""
            vertex = compileShader(vertex_source, GL_VERTEX_SHADER)
            fragment_source = """#version 450 core
layout(location = 0) out vec4 outColour;
in vec3 position;
uniform sampler2D albedo;
void main() {
    outColour = texture(albedo, position.xy); }"""
            fragment = compileShader(fragment_source, GL_FRAGMENT_SHADER)
            shader = compileProgram(vertex, fragment)
            glLinkProgram(shader)
            glUseProgram(shader)
            
        def paintGL(self):
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glBegin(GL_QUADS)
            glVertex(-1, 1)
            glVertex(1, 1)
            glVertex(1, -1)
            glVertex(-1, -1)
            glEnd()
    window = viewport()
    window.setGeometry(128, 64, 576, 576)
    window.show()
    app.exec_()
