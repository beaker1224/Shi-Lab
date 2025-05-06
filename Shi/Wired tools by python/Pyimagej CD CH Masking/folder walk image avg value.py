import os
import pandas as pd
from tifffile import imread

# ——— CONFIG ———
# List your 16 “CH‑masked” folders here:
ch_masked_dirs = [
    r"D:\study\Shi_Lab\Data\sebaceous gland\1R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\2R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\3R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\4R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\5R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\6R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\7R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\8R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\9R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\10R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\11R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\12R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\13R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\14R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\15R\CH-masked",
    r"D:\study\Shi_Lab\Data\sebaceous gland\16R\CH-masked",
]

# Where to write the Excel file:
output_xlsx = r"D:\study\Shi_Lab\Data\sebaceous gland\CH_masked_averages.xlsx"
# —————————

records = []

for dir_path in ch_masked_dirs:
    if not os.path.isdir(dir_path):
        print(f"Warning: folder not found, skipping: {dir_path}")
        continue
    print(f"Processing: {dir_path}")
    for fname in os.listdir(dir_path):
        if not fname.lower().endswith(".tif"):
            continue

        abs_path = os.path.join(dir_path, fname)
        # load the image and compute its mean
        img = imread(abs_path)
        mean_val = img.mean()

        records.append({
            "Path":     abs_path,
            "Filename": fname,
            "Mean":     mean_val
        })

# build a DataFrame and save to Excel
df = pd.DataFrame(records, columns=["Path", "Filename", "Mean"])
df.to_excel(output_xlsx, index=False)

print(f"\nWrote {len(df)} entries to {output_xlsx}")
