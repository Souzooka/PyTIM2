from tim2 import TIM2

import sys

file_path = "1821.TM2"#sys.argv[1]
tim2_file = None
try:
    tim2_file = open(file_path, "rb")
except OSError:
    print(f"ERROR: Could not open \"{file_path}\" as file!")
    sys.exit(1)

tim2 = TIM2.from_file(tim2_file)

tim2_file.close()
pass
