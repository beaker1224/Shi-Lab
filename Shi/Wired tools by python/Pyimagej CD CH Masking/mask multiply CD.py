import os
from tifffile import imread, imwrite

# ——— CONFIG ———
# this script will intake the folders contains CH tif files like
# 1-791.3nm-200m2-zoom6.0.tif
# and the corresponding tif mask like
# 1-mask.tif
# and save them into a subfolder under the main folder
dir_paths = [
    r"D:\study\Shi_Lab\Data\sebaceous gland\1R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\2R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\3R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\4R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\5R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\6R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\7R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\8R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\9R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\10R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\11R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\12R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\13R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\14R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\15R",
    r"D:\study\Shi_Lab\Data\sebaceous gland\16R",
    # … add as many as you need …
]# —————————

for dir_path in dir_paths:
    save_path = os.path.join(dir_path, "CD-masked")
    os.makedirs(save_path, exist_ok=True)

    print(f"saved to {save_path}")

    for fname in os.listdir(dir_path):
        # find each mask
        if not fname.endswith("-mask.tif"):
            continue

        roi = fname.replace("-mask.tif", "")               # e.g. "1"
        mask = imread(os.path.join(dir_path, fname))
        # mask_binary = (mask > 0)                           # treat non-zero as 1

        # now find all Result-of files for this ROI
        for res in os.listdir(dir_path):
            if not (res.startswith(f"Result of {roi}-") and res.endswith(".tif")):
                continue

            # load the result image
            img = imread(os.path.join(dir_path, res))

            # multiply
            # masked = img * mask_binary
            masked = img * mask
            
            # extract wavelength from filename:
            #   "Result of 1-841.8nm-600mW-zoom6.0.tif" → "1-841.8nm"
            core = res.replace("Result of ", "").rsplit("-", 2)[0]

            # build output name
            out_name = f"{core}-masked.tif"                  # e.g. "1-841.8nm-masked.tif"
            out_path = os.path.join(save_path, out_name)

            # save with the same dtype
            imwrite(out_path, masked.astype(img.dtype))

            print(f"Saved {out_name}")
