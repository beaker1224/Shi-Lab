import tifffile as tiff
import numpy as np
import napari
from skimage.filters import threshold_otsu  # optional

# Load image
img = tiff.imread('image.tif')  # works with 2D or 3D stacks

# Start GUI
viewer = napari.Viewer()
viewer.add_image(img, name='image', contrast_limits=[np.min(img), np.max(img)])

# Auto-threshold example (replace with your preferred threshold)
th = threshold_otsu(img) if img.dtype != bool else 0.5
mask_init = (img > th).astype(np.uint8)

# Add a paintable mask layer (0 background, 1 foreground)
mask_layer = viewer.add_labels(mask_init, name='mask')  # use brush/eraser to edit

napari.run()  # interactively edit the mask; close the window when done

# After the window closes, save the edited mask as 0/1 TIFF
final_mask = mask_layer.data.astype(np.uint8)  # ensure dtype uint8 with values 0/1
tiff.imwrite('mask.tif', final_mask)
