import subprocess
import os
import sys
from helpers.oir2tiff import oir_to_tiff

print("Welcome to Shuo's code for Image analysis!\n" \
"I am here to help you to do some basic image analysis from " \
"either .oir images or .tif images")

print("Please choose from the following options\n" \
"Usually, once you get all your oir images, just run everything from top to bottom")

print("feature list:\n" \
"1. Convert all the oir images into tiff images\n" \
"2. Get a mask for each set of image\n" \
"3. Get a redox ratio for each set of redox image\n" \
"4. Get CD/CH ratios\n" \
"5. \n" \
"6. \n")

# construct the input feature choose system
while True:
    try:
        feature_choice = int(input("Press 'enter' after you input a number\n"))
        break  # got a valid integer
    except ValueError:
        print("Enter a valid integer, please!!!")


# construct feature 1. convert destination oir files into tif files
os.system('cls')
print("Now we are trying to convert oir files to tif files\n" \
"Please provide absolute folder paths for all the oir files you want to process")


