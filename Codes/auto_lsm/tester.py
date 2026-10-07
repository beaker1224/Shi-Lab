import pyautogui
import json
import time


CONFIG_FILE = "FV_layout.json"

# Checkbox is approximately 10 x 10 pixels.
# Capture a little extra around it in case the saved top-left is off by 1-2 pixels.
CAPTURE_WIDTH = 14
CAPTURE_HEIGHT = 14

# A pixel is considered changed when the total RGB difference
# between unchecked and checked states exceeds this value.
TOLERANCE = 30


def load_from_json(file_name):
    with open(file_name, "r") as file:
        return json.load(file)


def capture_checkbox(position):
    """
    Capture a region around the checkbox starting from the saved top-left position.
    """

    x, y = position

    image = pyautogui.screenshot(
        region=(
            x,
            y,
            CAPTURE_WIDTH,
            CAPTURE_HEIGHT
        )
    )

    return image


def count_changed_pixels(
    unchecked_image,
    checked_image,
    x_offset,
    y_offset,
    width,
    height,
    tolerance=30
):
    """
    Count pixels that differ significantly between unchecked
    and checked checkbox images within a candidate region.
    """

    changed = 0

    for y in range(y_offset, y_offset + height):
        for x in range(x_offset, x_offset + width):

            unchecked = unchecked_image.getpixel((x, y))
            checked = checked_image.getpixel((x, y))

            difference = sum(
                abs(int(a) - int(b))
                for a, b in zip(unchecked, checked)
            )

            if difference > tolerance:
                changed += 1

    return changed


# ---------------------------------------------------------
# Load checkbox positions
# ---------------------------------------------------------

config = load_from_json(CONFIG_FILE)

positions = {}

for channel in range(1, 6):
    positions[channel] = tuple(
        config[f"channel_{channel}_checkbox_position"]
    )


# ---------------------------------------------------------
# Capture unchecked state
# ---------------------------------------------------------

print("\nMake sure CH1-CH5 are ALL UNCHECKED.")
input("Press Enter when ready...")

previous_mouse_position = pyautogui.position()

# Move mouse away so hover rendering disappears.
pyautogui.moveTo(100, 100)
time.sleep(0.5)

unchecked_images = {}

for channel in range(1, 6):
    unchecked_images[channel] = capture_checkbox(
        positions[channel]
    )

print("Unchecked images captured.")


# ---------------------------------------------------------
# Capture checked state
# ---------------------------------------------------------

print("\nNow CHECK CH1-CH5.")
input("Press Enter when all five are checked...")

pyautogui.moveTo(100, 100)
time.sleep(0.5)

checked_images = {}

for channel in range(1, 6):
    checked_images[channel] = capture_checkbox(
        positions[channel]
    )

print("Checked images captured.")

# Restore mouse after screenshots are finished.
pyautogui.moveTo(previous_mouse_position)


# ---------------------------------------------------------
# Automatically search candidate regions
# ---------------------------------------------------------

results = []

# Since checkbox is ~10x10, offsets larger than about 4 pixels
# are unlikely to be useful.
for x_offset in range(0, 5):

    for y_offset in range(0, 5):

        # Test realistic widths/heights.
        for width in range(4, 11):

            for height in range(4, 11):

                # Candidate region must stay inside captured image.
                if x_offset + width > CAPTURE_WIDTH:
                    continue

                if y_offset + height > CAPTURE_HEIGHT:
                    continue

                changed_counts = []

                for channel in range(1, 6):

                    changed = count_changed_pixels(
                        unchecked_images[channel],
                        checked_images[channel],
                        x_offset=x_offset,
                        y_offset=y_offset,
                        width=width,
                        height=height,
                        tolerance=TOLERANCE
                    )

                    changed_counts.append(changed)

                area = width * height

                changed_ratios = [
                    count / area
                    for count in changed_counts
                ]

                # Worst performing channel is most important.
                minimum_changed = min(changed_counts)
                minimum_ratio = min(changed_ratios)

                average_changed = (
                    sum(changed_counts)
                    / len(changed_counts)
                )

                average_ratio = (
                    sum(changed_ratios)
                    / len(changed_ratios)
                )

                results.append({
                    "x_offset": x_offset,
                    "y_offset": y_offset,

                    "width": width,
                    "height": height,

                    "area": area,

                    "counts": changed_counts,

                    "minimum_changed": minimum_changed,
                    "average_changed": average_changed,

                    "minimum_ratio": minimum_ratio,
                    "average_ratio": average_ratio,
                })


# ---------------------------------------------------------
# Rank combinations
# ---------------------------------------------------------

# Priority:
#
# 1. Highest worst-channel changed count
# 2. Highest worst-channel changed ratio
# 3. Highest average changed count
# 4. Larger region if otherwise similar
#
# This helps avoid a situation where CH3 is weak even though
# the other four channels look excellent.

results.sort(
    key=lambda result: (
        result["minimum_changed"],
        result["minimum_ratio"],
        result["average_changed"],
        result["area"]
    ),
    reverse=True
)


# ---------------------------------------------------------
# Display best results
# ---------------------------------------------------------

print("\n")
print("=" * 85)
print("BEST CHECKBOX DETECTION REGIONS")
print("=" * 85)


for rank, result in enumerate(results[:20], start=1):

    print(
        f"\n#{rank}"
        f"\n  offset = "
        f"({result['x_offset']}, {result['y_offset']})"
        f"\n  size   = "
        f"{result['width']} x {result['height']}"
        f"\n  area   = "
        f"{result['area']} pixels"
    )

    print(
        "  changed pixels: "
        + ", ".join(
            f"CH{i + 1}={count}"
            for i, count in enumerate(result["counts"])
        )
    )

    print(
        f"  worst channel changed pixels = "
        f"{result['minimum_changed']}"
    )

    print(
        f"  worst channel changed ratio  = "
        f"{result['minimum_ratio']:.2%}"
    )

    print(
        f"  average changed pixels       = "
        f"{result['average_changed']:.2f}"
    )

    print(
        f"  average changed ratio        = "
        f"{result['average_ratio']:.2%}"
    )


# ---------------------------------------------------------
# Best result
# ---------------------------------------------------------

best = results[0]

print("\n")
print("=" * 85)
print("RECOMMENDED SETTINGS")
print("=" * 85)

print(
    f"""
'checkbox strip width': {best['width']},
'checkbox strip height': {best['height']},
'checkbox strip x offset': {best['x_offset']},
'checkbox strip y offset': {best['y_offset']}
"""
)

print(
    "Changed pixels for best region:"
)

for channel, count in enumerate(
    best["counts"],
    start=1
):
    print(
        f"CH{channel}: "
        f"{count} / {best['area']} pixels changed"
    )


input("\nPress Enter to exit.")