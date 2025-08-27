# ***Pipeline***
```
This is the description of the pipeline for Shi Lab data process
should be integrating the following:
1. Python
2. Matlab
3. FIJI-ImageJ (If possible by subprocess by python) (or maybe create my own)
```
What needs to be done
(Very important: I am assuming the naming of the image follows some sort of patterns, personally, I use ROI-Wavelength-Power-something else)
### for cells
1. Have individual wavelengths (i.e. redox + CH + CD + background with individual wavelengths)
```
a. Python: convert all the .oir file into .tif file for the individual ones, to .tif stack for the sweep ones
b. FIJI: masking through thresholding from CH regions, primary choice is 791.3
c. FIJI: Detect CD, if has, choose if to delete the background
d. Python: Mask all the images by subtraction, save all those into tiff
e. Python: Apply LUT to all the images, let user adjust the contrast, save all those into PNG
f. 
```
2. Have hyperspectra
```

````
3.
### for tissue
