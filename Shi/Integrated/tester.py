from helpers.mask import thresholding_mask, apply_mask
from helpers.oir2tiff import oir_to_tiff
from helpers.quantitative import mask_prm_srs, compute_turnover
from helpers.redox import process_images
from pathlib import Path
# from helpers.calibration import tiff_to_png_with_bar, calibration_bar
import os, glob
import tifffile as tiff
import requests

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


# folders = [r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\with Methanol Wash\BCR-ABL\high\tiff_files",
#            r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\with Methanol Wash\DMSO\high\tiff_files",
#            r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\with Methanol Wash\LYni\high\tiff_files",
#            r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\without Methanol Wash\BCR-ACL\High\tiff_files",
#            r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\without Methanol Wash\BCR-ACL\Low\tiff_files",
#            r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\without Methanol Wash\DMSO\high\tiff_files",
#            r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\without Methanol Wash\DMSO\low\tiff_files",
#            r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\without Methanol Wash\LYni\high\tiff_files",
#            r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\without Methanol Wash\LYni\low\tiff_files"]
# for f in folders:
#     apply_mask(f)

folders = [r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\without Methanol Wash\LYni\high\1-CH_lipid subtypes\1-CH",
           r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\without Methanol Wash\LYni\low\2-CH_lipid subtypes\2-CH",
           r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\without Methanol Wash\LYni\low\3-CH_lipid subtypes\3-CH",
           r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\without Methanol Wash\DMSO\high\2-CH_lipid subtypes\2-CH",
           r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\without Methanol Wash\DMSO\high\4-CH_lipid subtypes\4-CH",
           r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\without Methanol Wash\DMSO\low\2-CH_lipid subtype\2-CH",
           r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\without Methanol Wash\BCR-ACL\High\1-CH_lipid subtypes\1-CH",
           r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\without Methanol Wash\BCR-ACL\Low\2-CH_lipid subtypes\2-CH",
           r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\with Methanol Wash\BCR-ABL\high\2-CH_lipid subtype",
           r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\with Methanol Wash\BCR-ABL\high\3-CH_lipid subtype\3-CH",
           r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\with Methanol Wash\DMSO\high\1-CH_lipid subtype\1-CH",
           r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\with Methanol Wash\LYni\high\1-CH_lipid subtype\1-CH"
           ]

for f in folders:
    mask_prm_srs(Path(f))

def notify_done_ntfy(title = "Task Complete", message = "Your task has finished running."):
    """Send a notification using ntfy.sh service."""
    url = "https://ntfy.sh/K-means-with-love-from-beaker"
    response = requests.post(
        url, 
        data=message.encode('utf-8'), 
        headers={"Title": title, 
                 "Priority": "5"},
                 timeout=20)
    response.raise_for_status()    