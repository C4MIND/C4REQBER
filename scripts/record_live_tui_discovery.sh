#!/usr/bin/env bash
# Record a REAL c4reqber discovery in TUI — terminal capture ONLY.
# NEVER uses screencapture, avfoundation, or desktop recording.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/load_kilo_env.sh"

export PYTHONPATH=src
export C4_NO_SPLASH=1
export C4_DEMO_AUTH=1
export C4_API_URL="${C4_API_URL:-http://127.0.0.1:8000}"
export C4_LOCAL_LLM_FIRST=1
export LM_STUDIO_MODEL=qwen2.5-7b-instruct

# Bootstrap LM Studio (headless)
LMS="$HOME/.lmstudio/bin/lms"
if [[ -x "$LMS" ]]; then
  if ! curl -sf "${LM_STUDIO_URL:-http://localhost:1234}/v1/models" >/dev/null 2>&1; then
    "$LMS" server start >/dev/null 2>&1 || true
    sleep 2
  fi
  if ! "$LMS" ps 2>/dev/null | rg -q "Loaded"; then
    FIRST_MODEL=$("$LMS" ls 2>/dev/null | awk 'NF && $1 !~ /^(You|LLM|─)/ {print $1; exit}')
    if [[ -n "${FIRST_MODEL:-}" ]]; then
      "$LMS" load "$FIRST_MODEL" -y >/dev/null 2>&1 || true
      export LM_STUDIO_MODEL="$FIRST_MODEL"
    fi
  fi
fi
export C4_DREAM_IDLE=0
export C4_LANG=en
export C4_WIDTH=120
export C4_HEIGHT=40

# Isolated HOME — skip wizard, force EN, never touch user's Telegram/desktop state
REC_HOME=$(mktemp -d)
export HOME="$REC_HOME"
export C4REQBER_CONFIG="$REC_HOME/.c4reqber"
mkdir -p "$C4REQBER_CONFIG"
cp -f "$ROOT/config/mission_free_models.json" "$C4REQBER_CONFIG/models.json" 2>/dev/null || true
cat >"$C4REQBER_CONFIG/tui-v9-state.json" <<'JSON'
{
  "langs_seen": ["en"],
  "achievements": [],
  "discovery_count": 0,
  "llm_tier": "C2",
  "color_profile": "default",
  "lang": "en",
  "first_run": false,
  "updated_at": "2026-07-14T00:00:00Z"
}
JSON

TUI_BIN="$ROOT/src/tui/v9/bin/c4tui-v9"
DOCS="$ROOT/docs/screenshots"
DEMO="$ROOT/docs/demo"
PY="$ROOT/scripts/txt_terminal_to_png.py"
SESSION="c4reqber-live-rec"
TOPIC="${1:-How can marine cloud brightening reduce regional warming while preserving rainfall?}"
MAX_SECONDS="${MAX_SECONDS:-180}"
INTERVAL="${INTERVAL:-2}"

if [[ ! -x "$TUI_BIN" ]]; then
  echo "TUI binary missing: $TUI_BIN" >&2
  exit 1
fi

mkdir -p "$DOCS" "$DEMO" "$ROOT/landing/assets/demo" "$ROOT/social-marketing"

echo "==> Waiting for backend $C4_API_URL"
for _ in $(seq 1 30); do
  if curl -sf "$C4_API_URL/api/v1/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
if ! curl -sf "$C4_API_URL/api/v1/health" >/dev/null 2>&1; then
  echo "Backend not reachable. Start: PYTHONPATH=src uvicorn src.api.server:app --host 127.0.0.1 --port 8000" >&2
  exit 1
fi

FRAMES="$ROOT/docs/demo/.live-rec-frames"
rm -rf "$FRAMES"
mkdir -p "$FRAMES"
trap 'tmux kill-session -t "$SESSION" 2>/dev/null || true; rm -rf "$REC_HOME"' EXIT

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -x 120 -y 40

LAUNCH="cd '$ROOT' && export HOME='$REC_HOME' C4REQBER_CONFIG='$REC_HOME/.c4reqber' PYTHONPATH=src C4_NO_SPLASH=1 C4_DEMO_AUTH=1 C4_LANG=en C4_DREAM_IDLE=0 C4_API_URL='$C4_API_URL' C4_WIDTH=120 C4_HEIGHT=40 && '$TUI_BIN'"
tmux send-keys -t "$SESSION" "$LAUNCH" C-m
sleep 5

# Close any overlay — never send ? (toggles help ON)
tmux send-keys -t "$SESSION" Escape
sleep 1

# DISCOVER mode (default) — full one-click HIL pipeline with live SSE cards
# FLASH mode — faster real discovery, readable EN demo (~30-90s)
tmux send-keys -t "$SESSION" Tab
sleep 0.5

tmux send-keys -t "$SESSION" -l "$TOPIC"
sleep 0.5
tmux send-keys -t "$SESSION" C-m

echo "==> Recording live TUI discovery: $TOPIC"
echo "    (terminal-only tmux capture, max ${MAX_SECONDS}s)"

capture_frame() {
  local idx="$1"
  local f="$FRAMES/frame_$(printf '%05d' "$idx").txt"
  tmux capture-pane -t "$SESSION" -p -J -S -300 >"$f"
  printf '%s\n' "$f"
}

frame_idx=0
done_at=""
start_ts=$(date +%s)

while true; do
  now=$(date +%s)
  elapsed=$((now - start_ts))
  if (( elapsed >= MAX_SECONDS )); then
    echo "==> Max time reached (${MAX_SECONDS}s)"
    break
  fi

  f=$(capture_frame "$frame_idx")
  frame_idx=$((frame_idx + 1))

  if (( frame_idx % 15 == 0 )); then
    echo "    ... ${elapsed}s elapsed, ${frame_idx} frames"
  fi

  # Discovery complete heuristics — require phase markers, not help overlay
  if (( elapsed > 25 )); then
    if rg -q "G: Quality|Hypothesis|hypothesis|progress 100|Flash complete|papers|B: Search.*done|🏆" "$f" 2>/dev/null \
      && ! rg -q "keyboard shortcuts|Press \\? to close|DREAM MODE|待机" "$f" 2>/dev/null; then
      if [[ -z "$done_at" ]]; then
        done_at=$elapsed
        echo "==> Discovery appears complete (~${elapsed}s), capturing overlays..."
        sleep 3
        f=$(capture_frame "$frame_idx")
        frame_idx=$((frame_idx + 1))

        # Capabilities overlay (best-effort)
        if tmux has-session -t "$SESSION" 2>/dev/null; then
          tmux send-keys -t "$SESSION" C-S-c
          sleep 2
          cp "$(capture_frame "$frame_idx")" "$DOCS/04_tui_v9_capabilities_overlay.txt" || true
          frame_idx=$((frame_idx + 1))
          tmux send-keys -t "$SESSION" Escape
          sleep 1
          tmux send-keys -t "$SESSION" :
          sleep 1
          cp "$(capture_frame "$frame_idx")" "$DOCS/06_tui_v9_command_palette.txt" || true
          frame_idx=$((frame_idx + 1))
          tmux send-keys -t "$SESSION" Escape
          sleep 1
          tmux send-keys -t "$SESSION" C-S-d
          sleep 1
          cp "$(capture_frame "$frame_idx")" "$DOCS/10_tui_v9_debug_overlay.txt" || true
          frame_idx=$((frame_idx + 1))
          tmux send-keys -t "$SESSION" Escape
          sleep 1
        fi

        for _ in 1 2 3; do
          sleep 2
          capture_frame "$frame_idx" >/dev/null
          frame_idx=$((frame_idx + 1))
        done
        break
      fi
    fi
  fi

  sleep "$INTERVAL"
done

# Final frame for feed / hypothesis screenshots
last="$FRAMES/frame_$(printf '%05d' $((frame_idx - 1))).txt"
cp "$last" "$DOCS/09_tui_v9_multi_paper_feed.txt"
# Best-effort hypothesis card — pick frame with most "Hypothesis" hits
best="$last"
best_score=0
for f in "$FRAMES"/*.txt; do
  score=$(rg -c "Hypothesis|hypothesis|▣" "$f" 2>/dev/null || echo 0)
  if (( score > best_score )); then
    best_score=$score
    best="$f"
  fi
done
cp "$best" "$DOCS/02_tui_v9_hypothesis_card.txt"
# Sim card — frame mentioning sim/engine
for f in "$FRAMES"/*.txt; do
  if rg -q "Simulation|sim_|OpenMM|engine" "$f" 2>/dev/null; then
    cp "$f" "$DOCS/03_tui_v9_simulation_card.txt"
    break
  fi
done
[[ -f "$DOCS/03_tui_v9_simulation_card.txt" ]] || cp "$best" "$DOCS/03_tui_v9_simulation_card.txt"

tmux send-keys -t "$SESSION" C-c 2>/dev/null || true
sleep 1

# Keep frames for rebuild; remove cache after successful encode

echo "==> Render PNG screenshots"
for pair in \
  02_tui_v9_hypothesis_card \
  03_tui_v9_simulation_card \
  04_tui_v9_capabilities_overlay \
  06_tui_v9_command_palette \
  09_tui_v9_multi_paper_feed \
  10_tui_v9_debug_overlay; do
  if [[ -f "$DOCS/${pair}.txt" ]]; then
    python3 "$PY" "$DOCS/${pair}.txt" "$DOCS/${pair}.png"
  fi
done

echo "==> Build MP4 + GIF from ${frame_idx} terminal frames (no desktop capture)"
WORK=$(mktemp -d)
LIST="$WORK/list.txt"
: >"$LIST"
FPS=2
# Subsample to ~30s at 2fps => 60 frames max
step=$(( frame_idx / 60 + 1 ))
idx=0
for f in "$FRAMES"/frame_*.txt; do
  if (( idx % step != 0 )); then
    idx=$((idx + 1))
    continue
  fi
  png="$WORK/$(printf '%04d.png' "$idx")"
  python3 "$PY" "$f" "$png" >/dev/null
  echo "file '$png'" >>"$LIST"
  echo "duration 0.5" >>"$LIST"
  idx=$((idx + 1))
done
# hold last frame
last_png=$(ls "$WORK"/*.png 2>/dev/null | tail -1)
if [[ -n "$last_png" ]]; then
  echo "file '$last_png'" >>"$LIST"
fi

OUT_MP4="$DEMO/c4reqber_mission_demo_30s.mp4"
OUT_GIF="$DEMO/c4reqber_tui_demo.gif"
ffmpeg -y -f concat -safe 0 -i "$LIST" -vf "fps=$FPS,format=yuv420p" -c:v libx264 -pix_fmt yuv420p "$OUT_MP4" 2>/dev/null
ffmpeg -y -i "$OUT_MP4" -filter_complex "[0:v] fps=10,scale=800:-1:flags=lanczos,split [a][b];[a] palettegen [p];[b] paletteuse [p]" "$OUT_GIF" 2>/dev/null

cp "$OUT_MP4" "$ROOT/landing/assets/demo/c4reqber_mission_demo_30s.mp4"
cp "$OUT_GIF" "$ROOT/social-marketing/c4reqber_tui_demo.gif"

rm -rf "$FRAMES"
rm -rf "$WORK"
echo "==> Done — live TUI discovery recording"
ls -lh "$OUT_MP4" "$OUT_GIF" "$DOCS"/*.png 2>/dev/null | tail -20
