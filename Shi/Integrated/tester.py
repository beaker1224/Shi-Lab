from helpers.mask import thresholding_mask, apply_mask
from helpers.oir2tiff import oir_to_tiff
from helpers.quantitative import mask_prm_srs, compute_turnover
from helpers.redox import process_images
# from helpers.calibration import tiff_to_png_with_bar, calibration_bar
import os, glob
import tifffile as tiff

# try:
#     SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
#     SCRIPT_DIR = os.path.join(SCRIPT_DIR, r"helpers")
# except NameError:                    # e.g. in notebooks
#     SCRIPT_DIR = os.getcwd()
#     print("cannot find royal.lut under heplers folder, please make a copy from FIJI")

# ROYAL_LUT_PATH = os.path.join(SCRIPT_DIR, "royal.txt")


# folders = [r"D:\Chrome\Rapamycin\data\brain\Ctrl1\tiff_files\processed",
#            r"D:\Chrome\Rapamycin\data\brain\Ctrl2\tiff_files\processed",
#            r"D:\Chrome\Rapamycin\data\brain\H1\tiff_files\processed",
#            r"D:\Chrome\Rapamycin\data\brain\L1\tiff_files\processed",
#            r"D:\Chrome\Rapamycin\data\brain\L2\tiff_files\processed",
#            r"D:\Chrome\Rapamycin\data\brain\L3\tiff_files\processed",
#            ]
# for f in folders:
#     compute_turnover(f)
# folders = [r"D:\Chrome\Rapamycin\data\gut\Ctrl3\tiff_files",
#            r"D:\Chrome\Rapamycin\data\gut\Ctrl2\tiff_files",
#            r"D:\Chrome\Rapamycin\data\gut\H2\tiff_files",
#            r"D:\Chrome\Rapamycin\data\gut\L1\tiff_files",
#            r"D:\Chrome\Rapamycin\data\gut\L2\tiff_files",
#            ]
# for f in folders:
#     apply_mask(f)