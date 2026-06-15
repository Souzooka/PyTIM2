from __future__ import annotations

import os
import struct
from enum import IntEnum, unique
from typing import BinaryIO

# https://rewiki.miraheze.org/wiki/TM2_TIM2_Image

class TIM2:
    header: TIM2Header
    images: list[TIM2Image]

    @classmethod
    def from_file(cls, f: BinaryIO):
        pos = f.tell()

        tim2 = cls()

        # Parse the header
        f.seek(pos + 0x0)
        tim2.header = TIM2Header.from_file(f)

        # Parse images (there's probably only 1, will have to see if any TIM2 have multiple in the wild)
        f.seek(pos + tim2.header.size)
        tim2.images = []
        for _ in range(tim2.header.number_of_images):
            image = TIM2Image.from_file(f)
            tim2.images.append(image)
            f.seek(image.header.image_size, os.SEEK_CUR)

        f.seek(pos)

        return tim2

class TIM2Header:
    # 0 (4 bytes)
    signature: str
    """Should be "TIM2" or "CLT2" (CLUT2) to indicate this is a valid TIM2 file."""
    # 4 (1 byte)
    version: int
    # 5 (1 byte)
    alignment: int
    # 6 (2 bytes)
    number_of_images: int
    """NOTE: This is presumably always 1"""
    
    size: int
    """Size of header; will be 16 or 128 depending on if alignment is 0 or 1 respectively."""

    @classmethod
    def from_file(cls, f: BinaryIO):
        pos = f.tell()

        header = cls()

        f.seek(pos + 0x0)
        header.signature = struct.unpack("<4s", f.read(4))[0].decode("utf-8")

        match header.signature:
            case "TIM2":
                pass
            case "CLT2":
                raise RuntimeError("CLUT2 files are unsupported.")
            case _:
                raise RuntimeError("File appears not to be a TIM2 file.")

        f.seek(pos + 0x4)
        header.version = struct.unpack("<B", f.read(1))[0]

        f.seek(pos + 0x5)
        header.alignment = struct.unpack("<B", f.read(1))[0]

        match header.alignment:
            case 0:
                header.size = 16
            case 1:
                header.size = 128
            case _:
                raise RuntimeError(f"Unrecognized TIM2 alignment value: {header.alignment}")

        f.seek(pos + 0x6)
        header.number_of_images = struct.unpack("<H", f.read(2))[0]

        if header.number_of_images > 1:
            raise RuntimeError("TIM2 files with more than 1 image are currently not supported.")

        f.seek(pos)
        
        return header

class TIM2ImageHeader:
    # 0 (4 bytes)
    image_size: int
    """Total image size"""
    # 4 (4 bytes)
    palette_size: int
    # 8 (4 bytes)
    image_data_size: int
    # C (2 bytes)
    image_header_size: int
    # E (2 bytes)
    num_palette_colors: int
    # 10 (1 byte)
    # (Probably 0?)
    picture_format: int
    # 11 (1 byte)
    num_mipmaps: int
    """Number of mipmaps (NOTE: This includes the main image, so main image + no other mipmaps is 1)"""
    # 12 (1 byte)
    palette_type: TIM2PaletteType
    # 13 (1 byte)
    image_type: TIM2ImageType
    # 14 (2 bytes)
    image_width: int
    # 16 (2 bytes)
    image_height: int
    # 18 (8 bytes)
    gs_tex0_register_data: int
    # 20 (8 bytes)
    gs_tex1_register_data: int
    # 28 (4 bytes)
    gs_tex_afbapabe_data: int
    # 2C (4 bytes)
    gs_texclut_register_data: int

    @classmethod
    def from_file(cls, f: BinaryIO):
        # TODO
        pos = f.tell()

        header = cls()

        f.seek(pos + 0x0)
        header.image_size = struct.unpack("<I", f.read(4))[0]

        f.seek(pos + 0x4)
        header.palette_size = struct.unpack("<I", f.read(4))[0]

        f.seek(pos + 0x8)
        header.image_data_size = struct.unpack("<I", f.read(4))[0]

        f.seek(pos + 0xC)
        header.image_header_size = struct.unpack("<H", f.read(2))[0]

        f.seek(pos + 0xE)
        header.num_palette_colors = struct.unpack("<H", f.read(2))[0]

        f.seek(pos + 0x10)
        header.picture_format = struct.unpack("<B", f.read(1))[0]

        f.seek(pos + 0x11)
        header.num_mipmaps = struct.unpack("<B", f.read(1))[0]

        f.seek(pos + 0x12)
        palette_type: int = struct.unpack("<B", f.read(1))[0]
        if palette_type not in TIM2PaletteType:
            raise RuntimeError(f"Unknown palette type: {palette_type}")
        header.palette_type = TIM2PaletteType(palette_type)

        f.seek(pos + 0x13)
        image_type: int = struct.unpack("<B", f.read(1))[0]
        if image_type not in TIM2ImageType:
            raise RuntimeError(f"Unknown image type: {image_type}")
        header.image_type = TIM2ImageType(image_type)

        f.seek(pos + 0x14)
        header.image_width = struct.unpack("<H", f.read(2))[0]

        f.seek(pos + 0x16)
        header.image_height = struct.unpack("<H", f.read(2))[0]

        f.seek(pos + 0x18)
        header.gs_tex0_register_data = struct.unpack("<Q", f.read(8))[0]

        f.seek(pos + 0x20)
        header.gs_tex1_register_data = struct.unpack("<Q", f.read(8))[0]

        f.seek(pos + 0x28)
        header.gs_tex_afbapabe_data = struct.unpack("<I", f.read(4))[0]

        f.seek(pos + 0x2C)
        header.gs_texclut_register_data = struct.unpack("<I", f.read(4))[0]

        f.seek(pos)
        
        return header

class TIM2Image:
    header: TIM2ImageHeader
    mipmaps: list[TIM2MipMap]
    image_data: bytes
    palette_data: bytes

    @classmethod
    def from_file(cls, f: BinaryIO):
        # TODO
        pos = f.tell()

        image = cls()
        image.header = TIM2ImageHeader.from_file(f)

        image.mipmaps = []

        f.seek(image.header.image_header_size, os.SEEK_CUR)
        image.image_data = f.read(image.header.image_data_size)
        image.palette_data = f.read(image.header.palette_size)

        image.validate_image_size()
        image.validate_palette_size()

        f.seek(pos)
        
        return image
    
    @property
    def width(self) -> int:
        return self.header.image_width
    
    @property
    def height(self) -> int:
        return self.header.image_height
    
    def validate_image_size(self):
        expected = 0
        actual = self.header.image_data_size
        pixels = self.header.image_width * self.header.image_height

        match self.header.image_type:
            case TIM2ImageType.TIM2_IDTEX4:
                # 2 pixels/byte
                expected = pixels / 2
            case TIM2ImageType.TIM2_IDTEX8:
                # 1 byte/pixel
                expected = pixels
            case TIM2ImageType.TIM2_RGB16:
                # 2 bytes/pixel
                expected = pixels * 2
            case TIM2ImageType.TIM2_RGB24:
                # 3 bytes/pixel
                expected = pixels * 3
            case TIM2ImageType.TIM2_RGB32:
                # 4 bytes/pixel
                expected = pixels * 4

        assert actual == expected, f"Image size mismatch (expected bytes={expected}, actual bytes={actual})"

    def validate_palette_size(self):
        expected = 0
        actual = self.header.palette_size
        colors = self.header.num_palette_colors

        if self.header.image_type not in (TIM2ImageType.TIM2_IDTEX4, TIM2ImageType.TIM2_IDTEX8):
            assert self.header.palette_type is TIM2PaletteType.PAL_NONE, "Non-indexed image has palette"
            return
        
        match self.header.palette_type:
            case TIM2PaletteType.PAL_RGB16_CSM1 | TIM2PaletteType.PAL_RGB16_CSM2:
                # 2 bytes/color
                expected = colors * 2
            case TIM2PaletteType.PAL_RGB32_CSM1 | TIM2PaletteType.PAL_RGB32_CSM2:
                # 4 bytes/color
                expected = colors * 4
            case _:
                pass

        assert actual == expected, f"Palette size mismatch (expected bytes={expected}, actual bytes={actual})"

    def get_normalized_image(self) -> list[int]:
        image: list[int] = []
        palette = self.__get_normalized_palette()

        match self.header.image_type:
            case TIM2ImageType.TIM2_RGB16:
                raise NotImplementedError()
            case TIM2ImageType.TIM2_RGB24:
                raise NotImplementedError()
            case TIM2ImageType.TIM2_RGB32:
                image = list(struct.unpack(f"<{len(self.image_data)}B", self.image_data))
            case TIM2ImageType.TIM2_IDTEX4:
                raise NotImplementedError()
            case TIM2ImageType.TIM2_IDTEX8:
                for index in self.image_data:
                    for i in range(4):
                        color = (palette[index] >> (i * 8)) & 0xFF
                        image.append(color)
        
        return image

    def __get_normalized_palette(self) -> list[int]:
        """
        Returns a 32-bit color palette for this image. If the image has no palette, this returns an empty sequence of bytes.
        """
        palette: list[int] = []

        def convert16_to_32(color: int) -> int:
            r = color & 0x1F
            color >>= 5
            g = color & 0x1F
            color >>= 5
            b = color & 0x1F
            color >>= 5
            a = color & 1
            
            color = \
                ((a * 128) << 24) | \
                ((b * 8) << 16) | \
                ((g * 8) << 8) | \
                ((r * 8))
            
            return color
        
        match self.header.palette_type:
            case TIM2PaletteType.PAL_NONE:
                pass
            case TIM2PaletteType.PAL_RGB16_CSM1:
                # (16-bit palette, swizzled)
                raise NotImplementedError()
            case TIM2PaletteType.PAL_RGB32_CSM1:
                # (32-bit palette, swizzled)
                #raise NotImplementedError()
                # TEST pending implementation
                palette = list(struct.unpack(f"<{len(self.palette_data) // 4}I", self.palette_data))
            case TIM2PaletteType.PAL_RGB16_CSM2:
                # (16-bit palette, linear)
                palette = [convert16_to_32(color) for color in struct.unpack(f"<{len(self.palette_data) // 2}H", self.palette_data)]
            case TIM2PaletteType.PAL_RGB32_CSM2:
                # (32-bit palette, linear)
                palette = list(struct.unpack(f"<{len(self.palette_data) // 4}I", self.palette_data))

        # Convert PS2 alpha (0x0-0x80) to 0x0-0xFF
        for i in range(len(palette)):
            a = palette[i] >> 24
            a = min(a * 2, 0xFF)
            palette[i] |= a << 24
        
        return palette

@unique
class TIM2ImageType(IntEnum):
    TIM2_RGB16 = 1 # (16bbp image, RGBA5551)
    TIM2_RGB24 = 2 # (24bpp image, RGBX8888)
    TIM2_RGB32 = 3 # (32bbp image, RGBA8888)
    TIM2_IDTEX4 = 4 # (4-bit indexed image, PAL4)
    TIM2_IDTEX8 = 5 # (8-bit indexed image, PAL8)

class TIM2Palette:
    @classmethod
    def from_file(cls, f: BinaryIO):
        # TODO
        pos = f.tell()

        palette = cls()

        f.seek(pos)
        
        return palette

@unique
class TIM2PaletteType(IntEnum):
    PAL_NONE = 0 # (no palette)
    PAL_RGB16_CSM1 = 1 # (16-bit palette, swizzled)
    PAL_RGB32_CSM1 = 3 # (32-bit palette, swizzled)
    PAL_RGB16_CSM2 = 129 # (16-bit palette, linear)
    PAL_RGB32_CSM2 = 131 # (32-bit palette, linear)

class TIM2MipMapHeader:
    @classmethod
    def from_file(cls, f: BinaryIO):
        # TODO
        pos = f.tell()

        header = cls()

        f.seek(pos)
        
        return header

class TIM2MipMap:
    header: TIM2MipMapHeader

    @classmethod
    def from_file(cls, f: BinaryIO):
        # TODO
        pos = f.tell()

        mipmap = cls()

        f.seek(pos)
        
        return mipmap

