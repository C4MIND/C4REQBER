#!/usr/bin/env python3
"""Convert ASCII-art.png to block-character C4R."""

from typing import cast

from PIL import Image


img = Image.open("/Users/figuramax/Downloads/ASCII-art.png").convert("L")
w, h = img.size
print(f"Original: {w}x{h}")

# Crop grid lines — find content bounds by looking for non-black pixels
# Threshold: pixel > 30 (not completely black)
thresh = 30

# Find top/bottom content boundaries
rows = []
for y in range(h):
    row_pixels = [cast(int, img.getpixel((x, y))) for x in range(w)]
    if any(p > thresh for p in row_pixels):
        rows.append(y)
top = min(rows) if rows else 0
bottom = max(rows) if rows else h

# Find left/right content boundaries
cols = []
for x in range(w):
    col_pixels = [cast(int, img.getpixel((x, y))) for y in range(h)]
    if any(p > thresh for p in col_pixels):
        cols.append(x)
left = min(cols) if cols else 0
right = max(cols) if cols else w

print(f"Content bbox: {left},{top} - {right},{bottom}")

# Crop
img = img.crop((left, top, right + 1, bottom + 1))
w, h = img.size
print(f"Cropped: {w}x{h}")

# Target size: ~48 chars wide, ~10-12 rows tall
target_w = 48
target_h = 12
img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

# Convert to ASCII using block chars (darkest to lightest)
chars = "█▓▒░ "  # 5 levels
levels = len(chars)

def pix_to_char(p: int) -> str:
    # p is 0-255, 0=black, 255=white
    # Invert: black background, white text -> we want white=char, black=space
    # But the image has white grid lines and white letters on dark bg
    # Actually the image is black bg with white halftone letters
    idx = int((p / 255) * (levels - 1))
    return chars[idx]

lines: list[str] = []
for y in range(target_h):
    row = ""
    for x in range(target_w):
        p = cast(int, img.getpixel((x, y)))
        row += pix_to_char(p)
    lines.append(row)

# Trim trailing spaces on each line
lines = [r.rstrip() for r in lines]
# Remove empty top/bottom
while lines and lines[0].strip() == "":
    lines.pop(0)
while lines and lines[-1].strip() == "":
    lines.pop()

# Center horizontally
max_len = max(len(r) for r in lines)
for i, r in enumerate(lines):
    pad = (max_len - len(r)) // 2
    lines[i] = " " * pad + r

print(f"\nGenerated {len(lines)} lines, width {max_len}:\n")
for r in lines:
    print(r)

# Write to a file for easy copying
with open("c4r_new.txt", "w") as f:
    f.write("\n".join(lines) + "\n")
