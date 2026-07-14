#!/usr/bin/env bash
# Build mission demo video from TUI screenshots (slideshow + titles).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/docs/demo/c4reqber_mission_demo_90s.mp4"
SHOTS="$ROOT/docs/screenshots"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

FPS=30
DUR=8  # seconds per slide

make_slide() {
  local idx="$1" title="$2" png="$3"
  local out="$WORK/$(printf '%02d' "$idx").png"
  python3 - "$title" "$png" "$out" <<'PY'
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

title, png_path, out_path = sys.argv[1:4]
base = Image.open(png_path).convert("RGB")
# Fit into 1920x1080 canvas with title bar
canvas = Image.new("RGB", (1920, 1080), (13, 17, 23))
scale = min(1880 / base.width, 980 / base.height, 1.0)
nw, nh = int(base.width * scale), int(base.height * scale)
resized = base.resize((nw, nh), Image.Resampling.LANCZOS)
x = (1920 - nw) // 2
y = 80 + (980 - nh) // 2
canvas.paste(resized, (x, y))
draw = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 36)
except OSError:
    font = ImageFont.load_default()
draw.text((40, 24), title, fill=(0, 220, 220), font=font)
draw.text((40, 1040), "c4reqber v9 · humanity-saving discovery mission · GitLab feat/production-upgrade", fill=(120, 140, 160), font=font)
canvas.save(out_path)
PY
}

make_slide 1 "TUI v9 — Hypothesis card" "$SHOTS/02_tui_v9_hypothesis_card.png"
make_slide 2 "TUI v9 — Simulation surface" "$SHOTS/03_tui_v9_simulation_card.png"
make_slide 3 "Capabilities overlay (32 engines + 27 verifiers)" "$SHOTS/04_tui_v9_capabilities_overlay.png"
make_slide 4 "Command palette" "$SHOTS/06_tui_v9_command_palette.png"
make_slide 5 "Multi-paper discovery feed" "$SHOTS/09_tui_v9_multi_paper_feed.png"
make_slide 6 "blast flash — marine cloud brightening" "$SHOTS/07_blast_flash_demo.png"

# ffmpeg concat demuxer with duration
LIST="$WORK/list.txt"
: > "$LIST"
for f in "$WORK"/*.png; do
  echo "file '$f'" >> "$LIST"
  echo "duration $DUR" >> "$LIST"
done
echo "file '$WORK/06.png'" >> "$LIST"

ffmpeg -y -f concat -safe 0 -i "$LIST" \
  -vf "fps=$FPS,format=yuv420p" \
  -c:v libx264 -pix_fmt yuv420p \
  "$OUT" 2>/dev/null

echo "Wrote $OUT ($(du -h "$OUT" | cut -f1))"
