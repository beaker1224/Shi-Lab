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
    save_path = os.path.join(dir_path, "CH-masked")
    os.makedirs(save_path, exist_ok=True)

    print(f"saved to {save_path}")
    for fname in os.listdir(dir_path):
        # only look at the mask files
        if not fname.endswith("-mask.tif"):
            continue

        roi = fname.replace("-mask.tif", "")           # e.g. "1"
        mask = imread(os.path.join(dir_path, fname))   

        # now find every .tif that starts with "1-" (but isn't the mask)
        for res in os.listdir(dir_path):
            if not res.endswith(".tif"):
                continue
            if res == fname:
                continue
            if res.startswith("Result of"):
                continue
            if not res.startswith(f"{roi}-"):
                continue
            if res.endswith("masked.tif"):
                continue
            if "794.6nm" in res:
                continue
            # load, mask, and save
            img = imread(os.path.join(dir_path, res))
            masked = img * mask

            # strip the “.tif” suffix for naming
            base = res.rsplit(".tif", 1)[0]             
            out_name = f"{base}-masked.tif"
            out_path = os.path.join(save_path, out_name)

            imwrite(out_path, masked.astype(img.dtype))
            print(f"Saved {out_name}")
