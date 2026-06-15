from __future__ import annotations

import sys
from PIL import Image

from tim2 import TIM2

file_path = "10003.TM2"#sys.argv[1]
is_swizzled = True
tim2_file = None
try:
    tim2_file = open(file_path, "rb")
except OSError:
    print(f"ERROR: Could not open \"{file_path}\" as file!")
    sys.exit(1)

tim2 = TIM2.from_file(tim2_file)

tim2_file.close()

tim2_image = tim2.images[0]
image_data = tim2_image.get_normalized_image(is_swizzled)

image = Image.frombytes("RGBA", (tim2_image.width, tim2_image.height), bytes(image_data))
image.save("output.png")
