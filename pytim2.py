from __future__ import annotations

import os
import sys
from pathlib import Path
from PIL import Image

from tim2 import TIM2

# NOTE: Some variables for testing exist here until command line arguments
# are implemented
# Single file
file_path = "20051.TM2"#sys.argv[1]
is_swizzled = True

# Folder
folder_path = "TEX"
swizzled_files = {"1955", "12238"}

if folder_path is not None:
    # Convert all files from within a provided folder and save them in another folder.
    # Get files from provided folder
    if not os.path.isdir(folder_path):
        raise RuntimeError(f"{folder_path} is not a directory.")
    files = os.listdir(folder_path)

    # Create the output directory
    if not os.path.isdir("PNG"):
        os.mkdir("PNG")

    for file in files:
        if Path(file).suffix.lower() != ".tm2":
            continue

        is_swizzled = Path(file).stem in swizzled_files

        tim2_file = open(f"TEX/{file}", "rb")
        tim2 = TIM2.from_file(tim2_file)
        tim2_file.close()
        tim2_image = tim2.images[0]
        image_data = tim2_image.get_normalized_image(is_swizzled)

        image = Image.frombytes("RGBA", (tim2_image.width, tim2_image.height), bytes(image_data))
        image.save(f"PNG/{Path(file).stem}.png")

    sys.exit(0)
else:
    # Only convert one file and save it back to the working directory.
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
    sys.exit(0)
