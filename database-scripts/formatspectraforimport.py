# from experiment import *
import hashlib
import sys
import re  

# Use with : find . -name "*csv" -exec python3 formatspectroforimport.py {} \; > importall.csv
if len(sys.argv) > 1:
    filepath = sys.argv[1]
else:
    filepath = sys.stdin

# data = DataFile(filepath=filepath, delimiter=',', hasHeader=False, skipLines=10)

text_file = open(filepath, "br")
hash = hashlib.md5(text_file.read()).hexdigest()
text_file.close()

# Using SQL commands is 1000x slower than using a CSV
# No spaces after comma!
# print("wavelength,intensity,column,md5")

text_file = open(filepath, "r")

lines = text_file.read().splitlines()

for line in lines:
    match = re.match(r'^\s*(\d+\.?\d+)\s+(-?\d*\.?\d*)', line)
    if match is not None:
        intensity = match.group(2)
        wavelength = match.group(1)
        print(f'{wavelength},{intensity},{hash}')
    else:
        pass
        # print("Line does not match: {0}".format(line))
