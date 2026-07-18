#!/usr/bin/env bash
# Capture TUI demo assets — TERMINAL ONLY. Never use screencapture / avfoundation.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCS="$ROOT/docs/screenshots"
GOLD="$ROOT/src/tui/v9/tests/golden"
PY="$ROOT/scripts/txt_terminal_to_png.py"
DEMO="$ROOT/docs/demo"

mkdir -p "$DOCS" "$DEMO" "$ROOT/landing/assets/demo"

echo "==> Refresh golden snapshots"
cd "$ROOT/src/tui/v9"
UPDATE=1 go test -run TestGoldenSnapshots -count=1 >/dev/null

echo "==> Copy golden terminal dumps"
cp "$GOLD/T2-mbp16-hypothesis.txt" "$DOCS/02_tui_v9_hypothesis_card.txt"
cp "$GOLD/T2-mbp16-sim.txt" "$DOCS/03_tui_v9_simulation_card.txt"
cp "$GOLD/T2-mbp16-capsim.txt" "$DOCS/04_tui_v9_capabilities_overlay.txt"
cp "$GOLD/T2-mbp16-palette.txt" "$DOCS/06_tui_v9_command_palette.txt"
cp "$GOLD/T2-mbp16-multi-paper.txt" "$DOCS/09_tui_v9_multi_paper_feed.txt"
cp "$GOLD/T2-mbp16-debug.txt" "$DOCS/10_tui_v9_debug_overlay.txt"

echo "==> Render PNG (Menlo terminal, dark theme — no desktop capture)"
for pair in \
  02_tui_v9_hypothesis_card \
  03_tui_v9_simulation_card \
  04_tui_v9_capabilities_overlay \
  06_tui_v9_command_palette \
  09_tui_v9_multi_paper_feed \
  10_tui_v9_debug_overlay; do
  python3 "$PY" "$DOCS/${pair}.txt" "$DOCS/${pair}.png"
done

echo "==> Build 30s slideshow MP4 from TUI PNGs only"
OUT_MP4="$DEMO/c4reqber_mission_demo_30s.mp4"
OUT_GIF="$DEMO/c4reqber_tui_demo.gif"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
FPS=30
DUR=5

make_slide() {
  local idx="$1" title="$2" png="$3"
  local out="$WORK/$(printf '%02d' "$idx").png"
  python3 - "$title" "$png" "$out" <<'PY'
import sys
from PIL import Image, ImageDraw, ImageFont

title, png_path, out_path = sys.argv[1:4]
base = Image.open(png_path).convert("RGB")
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
draw.text((40, 1040), "c4reqber TUI v9 · terminal-only capture · cognitive-functors.gitlab.io/c4reqber", fill=(120, 140, 160), font=font)
canvas.save(out_path)
PY
}

make_slide 1 "TUI v9 — Hypothesis card" "$DOCS/02_tui_v9_hypothesis_card.png"
make_slide 2 "TUI v9 — Simulation surface" "$DOCS/03_tui_v9_simulation_card.png"
make_slide 3 "Capabilities overlay (38 engines + 9 verifiers)" "$DOCS/04_tui_v9_capabilities_overlay.png"
make_slide 4 "Command palette" "$DOCS/06_tui_v9_command_palette.png"
make_slide 5 "Multi-paper discovery feed" "$DOCS/09_tui_v9_multi_paper_feed.png"
make_slide 6 "Debug overlay" "$DOCS/10_tui_v9_debug_overlay.png"

LIST="$WORK/list.txt"
: > "$LIST"
for f in "$WORK"/*.png; do
  echo "file '$f'" >> "$LIST"
  echo "duration $DUR" >> "$LIST"
done
echo "file '$WORK/06.png'" >> "$LIST"

ffmpeg -y -f concat -safe 0 -i "$LIST" -vf "fps=$FPS,format=yuv420p" -c:v libx264 -pix_fmt yuv420p "$OUT_MP4" 2>/dev/null

ffmpeg -y -i "$OUT_MP4" -filter_complex "[0:v] fps=10,scale=800:-1:flags=lanczos,split [a][b];[a] palettegen [p];[b] paletteuse [p]" "$OUT_GIF" 2>/dev/null

cp "$OUT_MP4" "$ROOT/landing/assets/demo/c4reqber_mission_demo_30s.mp4"
mkdir -p "$ROOT/social-marketing"
cp "$OUT_GIF" "$ROOT/social-marketing/c4reqber_tui_demo.gif"

echo "==> Done"
ls -lh "$OUT_MP4" "$OUT_GIF" "$DOCS"/*.png
