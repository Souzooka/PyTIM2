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

        header.image_size = 0

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

        f.seek(pos)
        
        return image

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

