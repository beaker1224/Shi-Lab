import pyautogui
import json
import time


CONFIG_FILE = "FV_layout.json"

# Capture a region large enough to contain the entire checkbox.
CAPTURE_WIDTH = 20
CAPTURE_HEIGHT = 20

# Difference threshold for one RGB pixel.
TOLERANCE = 30


def load_from_json(file_name):
    with open(file_name, "r") as file:
        return json.load(file)


def capture_checkbox(position):
    """
    Capture a full checkbox-sized area starting from its saved top-left corner.
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
    Compare a candidate sub-region between unchecked and checked images.
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

# Move mouse away so hover color does not interfere.
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


# ---------------------------------------------------------
# Automatically search different strip sizes and offsets
# ---------------------------------------------------------

results = []

for x_offset in range(0, 9):

    for y_offset in range(0, 9):

        for width in range(4, 20):

            for height in range(2, 20):

                # Make sure the candidate region stays inside
                # our 20 x 20 captured image.
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

                # Percentage of candidate pixels that change.
                changed_ratios = [
                    count / area
                    for count in changed_counts
                ]

                # We care strongly about the WORST channel.
                # If CH3 only shows a tiny difference, this
                # configuration should not rank highly.
                minimum_ratio = min(changed_ratios)
                average_ratio = (
                    sum(changed_ratios)
                    / len(changed_ratios)
                )

                minimum_changed = min(changed_counts)

                results.append({
                    "x_offset": x_offset,
                    "y_offset": y_offset,
                    "width": width,
                    "height": height,
                    "area": area,

                    "counts": changed_counts,

                    "minimum_changed": minimum_changed,
                    "minimum_ratio": minimum_ratio,
                    "average_ratio": average_ratio
                })


# ---------------------------------------------------------
# Rank combinations
# ---------------------------------------------------------

results.sort(
    key=lambda result: (
        result["minimum_ratio"],
        result["average_ratio"],
        result["minimum_changed"]
    ),
    reverse=True
)


# ---------------------------------------------------------
# Display best 20
# ---------------------------------------------------------

print("\n")
print("=" * 80)
print("BEST CHECKBOX DETECTION REGIONS")
print("=" * 80)

for rank, result in enumerate(results[:20], start=1):

    print(
        f"\n#{rank}"
        f"\n  offset = "
        f"({result['x_offset']}, {result['y_offset']})"
        f"\n  size   = "
        f"{result['width']} x {result['height']}"
        f"\n  area   = {result['area']} pixels"
    )

    print(
        "  changed pixels:",
        ", ".join(
            f"CH{i + 1}={count}"
            for i, count in enumerate(result["counts"])
        )
    )

    print(
        f"  worst-channel changed ratio = "
        f"{result['minimum_ratio']:.2%}"
    )

    print(
        f"  average changed ratio       = "
        f"{result['average_ratio']:.2%}"
    )


# ---------------------------------------------------------
# Best result
# ---------------------------------------------------------

best = results[0]

print("\n")
print("=" * 80)
print("RECOMMENDED SETTINGS")
print("=" * 80)

print(
    f"""
'checkbox strip width': {best['width']},
'checkbox strip height': {best['height']},
'checkbox strip x offset': {best['x_offset']},
'checkbox strip y offset': {best['y_offset']}
"""
)

input("\nPress Enter to exit.")