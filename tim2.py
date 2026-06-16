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

    def get_normalized_image(self, is_swizzled: bool = False) -> list[int]:
        image: list[int] = []
        palette = self.__get_normalized_palette()

        match self.header.image_type:
            case TIM2ImageType.TIM2_RGB16:
                # UNTESTED
                for i in range(0, len(self.image_data), 2):
                    rgba = self.image_data[i] | (self.image_data[i + 1] << 8)
                    r = rgba & 0x1F
                    rgba >>= 5
                    g = rgba & 0x1F
                    rgba >>= 5
                    b = rgba & 0x1F
                    rgba >>= 5
                    a = rgba & 1
                    image.extend([r * 8, g * 8, b * 8, a * 128])
            case TIM2ImageType.TIM2_RGB24:
                # UNTESTED
                for i in range(0, len(self.image_data), 3):
                    for j in range(i, i + 3):
                        image.append(self.image_data[j])
                    image.append(128) # Alpha = 0x80
            case TIM2ImageType.TIM2_RGB32:
                # UNTESTED
                image = list(struct.unpack(f"<{len(self.image_data)}B", self.image_data))
            case TIM2ImageType.TIM2_IDTEX4:
                linear_image = list(self.image_data)
                if is_swizzled:
                    linear_image = self.__unswizzle_imagePSMT4()
                for byte in linear_image:
                    indices = [byte & 0xF, byte >> 4]
                    for index in indices:
                        for i in range(4):
                            color = (palette[index] >> (i * 8)) & 0xFF
                            image.append(color)
            case TIM2ImageType.TIM2_IDTEX8:
                linear_image = list(self.image_data)
                if is_swizzled:
                    linear_image = self.__unswizzle_imagePSMT8()
                for index in linear_image:
                    for i in range(4):
                        color = (palette[index] >> (i * 8)) & 0xFF
                        image.append(color)

        # Convert PS2 alpha (0x0-0x80) to 0x0-0xFF
        for i in range(3, len(image), 4):
            a = image[i]
            a = min(a * 2, 0xFF)
            image[i] = a

        return image
    
    def __unswizzle_imagePSMT8(self) -> list[int]:
        image = self.image_data

        # We need to convert the original 8-bit image to a 32-bit image of half size
        # to work upon it (e.g. 8-bit 64x64 -> 32-bit 32x32) because the way pixels are
        # laid out in the 32-bit image are going to be different than they are in the 8-bit image.
        # (e.g. in the 32-bit format, which we're unpacking to 8-bit, (x=16,y=0) would actually be (x=0,y=1)
        # in the 8-bit format as the 16th 32-bit pixel starts with the 64th byte.)
        image32 = list(struct.unpack(f"<{len(self.image_data) // 4}I", self.image_data))
        width = self.width // 2
        height = self.height // 2

        new_image: list[int] = [0] * len(image)

        # In the 32-bit image, for a 8x2 column which looks like this:
        #
        # A B C D E F G H
        # I J K L M N O P
        #
        # the 64-bit 8-bit values are laid out as such, for the first four pixels:
        #    bit0...        ...bit32
        # A: 0  | 36 | 8  | 44
        # B: 1  | 37 | 9  | 45
        # C: 2  | 38 | 10 | 46
        # D: 3  | 39 | 11 | 47
        # And this pattern of 4 sequential indices being in the same byte of a 32-bit value
        # continues for the rest of the pixels. We can use a lookup table here to determine
        # the starting bit // 4 for each of those 4 pixel chunks.
        # The even layout is used for columns 0, 2, ..., while the odd layout is used for
        # colums 1, 3, .... The two layouts are rather similar, but the odd layout is laid
        # out such that we can just flip the lookup value's least significant bit to replicate it.
        # (for example, for an odd column, 8-bit pixels 4, 5, 6, and 7 are located within the first
        # byte of the 32-bit pixels A, B, C, and D).
        even_layout = [
            0, 9, 2, 11,
            1, 8, 3, 10,
            4, 13, 6, 15,
            5, 12, 7, 14,
        ]
        odd_layout = [i ^ 1 for i in even_layout]

        def get_pixel(column: int, i: int) -> int:
            layout = odd_layout if column & 1 else even_layout

            layout_idx = (i % 4) + ((i // 16) * 4)
            offset = (layout[layout_idx] * 4) + ((i % 16) // 4)

            return offset
        
        # NOTE: Columns vary by size per image type (it's 64-bytes of data)
        # but always start at the top left of the image, and then travel downwards.
        # If the top left of an 8-bit 32x16 image is (x=0, y=0), then the first column
        # is at (0,0), then (0,4), then (0,8), then (0, 12), then (4, 0), and so on.
        for column in range(len(new_image) // 64):
            # These are the coordinates for the top left of a 8x2 column
            # for the 32-bit representation for the texture
            scx, scy = (column * 2) // height * 8, (column * 2) % height
            # These are the coordinates for the top left of a 16x4 column
            # for the 8-bit representation for the texture
            dcx, dcy = (column * 4) // self.height * 16, (column * 4) % self.height
            for i in range(64):
                # Extract a byte from the 32-bit image which will
                # replace a pixel in the 8-bit image. These bytes
                # are extracted sequentially out of the 32-bit
                # column as the loop iterates.
                x, y = scx + (i // 4) % 8, scy + i // 32
                src_pixel_idx = y * width + x
                src_pixel = image32[src_pixel_idx]
                src_pixel = (src_pixel >> (i % 4) * 8) & 0xFF

                # Determine the position of the 8-bit pixel to replace.
                column_idx = get_pixel(column, i)
                dx, dy = column_idx % 16, column_idx // 16
                dest_pixel = self.__calc_index(dcx + dx, dcy + dy)
                new_image[dest_pixel] = src_pixel

        return new_image
    
    def __unswizzle_imagePSMT4(self) -> list[int]:
        image = self.image_data

        image32 = list(struct.unpack(f"<{len(self.image_data) // 4}I", self.image_data))
        width = self.width // 2
        height = self.height // 4

        new_image: list[int] = [0] * len(image)

        even_layout = [
            0 , 17, 2 , 19, 4 , 21, 6 , 23,
            1 , 16, 3 , 18, 5 , 20, 7 , 22,
            8 , 25, 10, 27, 12, 29, 14, 31,
            9 , 24, 11, 26, 13, 28, 15, 30,
        ]
        odd_layout = [i ^ 1 for i in even_layout]

        def get_pixel(column: int, i: int) -> int:
            layout = odd_layout if column & 1 else even_layout

            layout_idx = (i % 8) + ((i // 32) * 8)
            offset = (layout[layout_idx] * 4) + ((i % 32) // 8)

            return offset
        
        for column in range(len(new_image) // 64):
            scx, scy = (column * 2) // height * 8, (column * 2) % height
            dcx, dcy = (column * 4) // self.height * 32, (column * 4) % self.height
            for i in range(128):
                # Extract a nibble from the 32-bit image which will
                # replace a pixel in the 4-bit image. These bytes
                # are extracted sequentially out of the 32-bit
                # column as the loop iterates.
                x, y = scx + (i // 8) % 8, scy + i // 64
                src_pixel_idx = y * width + x
                src_pixel = image32[src_pixel_idx]
                shift = (i % 8) * 4
                src_pixel = ((src_pixel & (0xF << shift)) >> shift) & 0xF

                # Determine the position of the 4-bit pixel to replace.
                column_idx = get_pixel(column, i)
                dx, dy = column_idx % 32, column_idx // 32
                dest_pixel = self.__calc_index4(dcx + dx, dcy + dy)

                pixel = new_image[dest_pixel]
                if column_idx & 1 == 0:
                    new_image[dest_pixel] = (pixel & 0xF0) | src_pixel
                else:
                    new_image[dest_pixel] = (pixel & 0x0F) | (src_pixel << 4)

        # TODO: 
        # Now, the image is properly deswizzled, BUT, the image as is consists of
        # 32x16 pixel blocks which are ordered incorrectly. 
        # For example, consider we have a 64x64 texture.
        # The blocks should be laid out left to right as such:
        #
        # 0 1
        # 2 3
        # 4 5
        # 6 7
        #
        # However, the blocks are actually laid out as such:
        #
        # 0 4
        # 1 5
        # 2 6
        # 3 7
        #
        # Therefore, we need to transform the image again in order
        # to rotate these blocks around.

        return new_image
    
    def __calc_index(self, x: int, y: int) -> int:
        return y * self.width + x
    
    def __calc_index4(self, x: int, y: int) -> int:
        return y * (self.width // 2) + (x // 2)
    
    def __unswizzle_palette32(self) -> list[int]:
        palette = list(struct.unpack(f"<{len(self.palette_data) // 4}I", self.palette_data))
        return self.__unswizzle_palette(palette)
    
    def __unswizzle_palette16(self) -> list[int]:
        palette = list(struct.unpack(f"<{len(self.palette_data) // 2}H", self.palette_data))
        return self.__unswizzle_palette(palette)
    
    def __unswizzle_palette(self, palette: list[int]) -> list[int]:
        if self.header.image_type is TIM2ImageType.TIM2_IDTEX4:
            # The palette is effectively already linear
            return palette

        new_palette: list[int] = []

        for i in range(len(palette)):
            top = (i & 0x8) == 0
            left = (i & 0x10) == 0

            if top and left:
                new_palette.append(palette[i])
            elif not top and left:
                new_palette.append(palette[i + 8])
            elif top and not left:
                new_palette.append(palette[i - 8])
            else:
                new_palette.append(palette[i])
        
        return new_palette

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
                # UNTESTED
                pass
            case TIM2PaletteType.PAL_RGB16_CSM1:
                # UNTESTED
                # (16-bit palette, swizzled)
                palette = [convert16_to_32(color) for color in self.__unswizzle_palette16()]
            case TIM2PaletteType.PAL_RGB32_CSM1:
                # (32-bit palette, swizzled)
                palette = self.__unswizzle_palette32()
            case TIM2PaletteType.PAL_RGB16_CSM2:
                # UNTESTED
                # (16-bit palette, linear)
                palette = [convert16_to_32(color) for color in struct.unpack(f"<{len(self.palette_data) // 2}H", self.palette_data)]
            case TIM2PaletteType.PAL_RGB32_CSM2:
                # UNTESTED
                # (32-bit palette, linear)
                palette = list(struct.unpack(f"<{len(self.palette_data) // 4}I", self.palette_data))
        
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

