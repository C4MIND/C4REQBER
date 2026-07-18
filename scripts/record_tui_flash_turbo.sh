#!/usr/bin/env bash
# Record REAL c4reqber TUI demo: FLASH + TURBO.
# Captures the live terminal continuously so the discovery actually plays out,
# renders at 720p, and produces an MP4 + GIF.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/mission_env.sh"

export C4_NO_SPLASH=1
export C4_DEMO_AUTH=1
export C4_WIDTH=110
export C4_HEIGHT=52

# NOTE: the TUI now routes "?" (and all plain keys) into the focused input,
# so a trailing "?" is fine and reads as a proper question.
FLASH_TOPIC="${FLASH_TOPIC:-Can iron-fertilized marine cloud brightening cool coastal heatwaves without suppressing monsoon rainfall?}"
TURBO_TOPIC="${TURBO_TOPIC:-Is sleep an active glymphatic maintenance phase, not passive rest?}"
FLASH_MAX="${FLASH_MAX:-240}"
TURBO_MAX="${TURBO_MAX:-600}"
INTERVAL="${INTERVAL:-2}"
FONT_SIZE="${FONT_SIZE:-18}"
FRAME_DUR="${FRAME_DUR:-0.2}"

TUI_BIN="$ROOT/src/tui/v9/bin/c4tui-v9"
DOCS="$ROOT/docs/screenshots"
DEMO="$ROOT/docs/demo"
PY="$ROOT/scripts/txt_terminal_to_png.py"
SESSION="c4reqber-demo-rec"

if [[ ! -x "$TUI_BIN" ]]; then
  echo "TUI binary missing: $TUI_BIN" >&2
  exit 1
fi

mkdir -p "$DOCS" "$DEMO" "$ROOT/landing/assets/demo" "$ROOT/social-marketing"

if [[ -z "${SKIP_BACKEND_RESET:-}" ]]; then
echo "==> Resetting backend on $C4_API_URL (fresh keys from ~/.kilo/.env)"
# Kill any pre-existing backend so we never reuse a stale, keyless process.
# Kill by process name AND by port. NOTE: on macOS `fuser` does not support
# `-k port/tcp`, so we use lsof to find and kill whatever holds :8000; a stale
# backend that survives pkill would keep :8000 and make the TUI poll time out.
pkill -9 -f "uvicorn src.api.server:app" 2>/dev/null || true
# macOS `lsof` lives in /usr/sbin, which mission_env may trim from PATH.
# Resolve it explicitly and guard every call so `set -e` can't abort the script
# if it is missing (we fall back to the pkill above in that case).
LSOF=$(command -v lsof 2>/dev/null || true)
if [ -z "$LSOF" ] && [ -x /usr/sbin/lsof ]; then LSOF=/usr/sbin/lsof; fi
if [ -n "$LSOF" ]; then
  PIDS=$("$LSOF" -tiTCP:8000 -sTCP:LISTEN 2>/dev/null) || true
  if [ -n "$PIDS" ]; then
    # shellcheck disable=SC2086
    kill -9 $PIDS 2>/dev/null || true
  fi
  # Wait until nothing is listening on :8000 before we bind a fresh backend.
  for _ in $(seq 1 40); do
    "$LSOF" -tiTCP:8000 -sTCP:LISTEN >/dev/null 2>&1 || break
    sleep 0.5
  done
fi
sleep 1
echo "    Starting API server (keys loaded via mission_env -> load_kilo_env)..."
PYTHONPATH=src nohup python3 -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000 \
  > /tmp/c4reqber_api_rec.log 2>&1 &
API_PID=$!
disown "$API_PID" 2>/dev/null || true
for _ in $(seq 1 90); do
  curl -sf "$C4_API_URL/api/v1/health" >/dev/null 2>&1 && break
  sleep 1
done
curl -sf "$C4_API_URL/api/v1/health" >/dev/null || {
  echo "Backend not reachable on $C4_API_URL (see /tmp/c4reqber_api_rec.log)" >&2
  exit 1
}
echo "    Backend OK"
# Sanity: a fresh backend prints a Uvicorn startup banner. If the log has no
# startup banner at all, something is wrong (but we don't key on the date —
# the backend logs in UTC, so a local "July-14" timestamp is just the current
# run). The port-kill above already guarantees a fresh process on :8000.
if ! grep -qE 'Uvicorn running on|Application startup complete' /tmp/c4reqber_api_rec.log 2>/dev/null; then
  echo "WARN: backend started but no Uvicorn startup banner in log (see /tmp/c4reqber_api_rec.log)" >&2
fi
fi

REC_HOME=$(mktemp -d)
export HOME="$REC_HOME"
export C4REQBER_CONFIG="$REC_HOME/.c4reqber"
mkdir -p "$C4REQBER_CONFIG"
cp -f "$ROOT/config/mission_free_models.json" "$C4REQBER_CONFIG/models.json"
cat >"$C4REQBER_CONFIG/tui-v9-state.json" <<'JSON'
{"langs_seen":["en"],"achievements":[],"discovery_count":0,"llm_tier":"C2","color_profile":"default","lang":"en","first_run":false,"updated_at":"2026-07-14T00:00:00Z"}
JSON

FRAMES="$ROOT/docs/demo/.live-rec-frames"
rm -rf "$FRAMES"
mkdir -p "$FRAMES"
FRAME_N="$FRAMES/.n"
echo 0 >"$FRAME_N"
trap 'tmux kill-session -t "$SESSION" 2>/dev/null || true; rm -rf "$REC_HOME"' EXIT

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -x 110 -y 52

LAUNCH="cd '$ROOT' && source '$ROOT/scripts/mission_env.sh' && export HOME='$REC_HOME' C4REQBER_CONFIG='$REC_HOME/.c4reqber' C4_NO_SPLASH=1 C4_DEMO_AUTH=1 C4_LANG=en C4_DREAM_IDLE=0 C4_API_URL='$C4_API_URL' C4_WIDTH=110 C4_HEIGHT=52 && '$TUI_BIN'"
tmux send-keys -t "$SESSION" "$LAUNCH" C-m
sleep 5
tmux send-keys -t "$SESSION" Escape
sleep 1

# Frame counter is persisted in a file: capture_frame is invoked inside
# $(...) subshells, so a shell variable would never survive between calls.
capture_frame() {
  local n f
  n=$(cat "$FRAME_N")
  f="$FRAMES/frame_$(printf '%05d' "$n").txt"
  tmux capture-pane -t "$SESSION" -p -J -S -300 >"$f"
  echo $((n + 1)) >"$FRAME_N"
  printf '%s\n' "$f"
}

frame_count() {
  local c
  c=$(cat "$FRAME_N" 2>/dev/null)
  c=${c//[^0-9]/}
  echo "${c:-0}"
}

reject_frame() {
  local f="$1"
  rg -q "Poll error|DREAM MODE|待机|keyboard shortcuts|Press \\? to close" "$f" 2>/dev/null
}

wait_for_pattern() {
  local label="$1" max_sec="$2" pattern="$3"
  local start_ts elapsed f
  start_ts=$(date +%s)
  echo "==> Recording $label (max ${max_sec}s)"
  while true; do
    elapsed=$(( $(date +%s) - start_ts ))
    if (( elapsed >= max_sec )); then
      echo "    TIMEOUT $label at ${elapsed}s"
      return 1
    fi
    f=$(capture_frame)
    if (( elapsed > 15 )) && rg -q "$pattern" "$f" 2>/dev/null && ! reject_frame "$f"; then
      echo "    DONE $label (~${elapsed}s)"
      # keep capturing the completed result (dissertation + papers) so the
      # video ends on the finished output, not mid-progress.
      for _ in $(seq 1 20); do sleep 1; capture_frame >/dev/null; done
      return 0
    fi
    sleep "$INTERVAL"
  done
}

# Pre-roll: capture the live TUI before any discovery starts.
for _ in 1 2 3; do capture_frame >/dev/null; done

clear_overlay() {
  # "?" toggles the help overlay; make sure it is never open when we type.
  tmux send-keys -t "$SESSION" Escape
  sleep 0.6
}

# Insert a topic reliably, one character at a time. `tmux paste-buffer`
# occasionally drops characters when the burst arrives mid-render, and a
# single `send-keys -l` of the whole string is too fast. Per-character typing
# at a steady pace is clean; the TUI now routes focused-input keys to the text
# field (keymap focus guard), so letters like c/f/g/i/o are no longer swallowed.
type_topic() {
  local s="$1" i ch
  for (( i = 0; i < ${#s}; i++ )); do
    ch="${s:$i:1}"
    tmux send-keys -t "$SESSION" -l "$ch"
    sleep 0.05
  done
}

# --- FLASH (Tab x1 from DISCOVER) ---
clear_overlay
tmux send-keys -t "$SESSION" Tab
sleep 1.5
clear_overlay
type_topic "$FLASH_TOPIC"
sleep 0.8
tmux send-keys -t "$SESSION" C-m
# FLASH completion is signaled by the result card: "Hypothesis" (success) or
# "Flash error" (failure). The old "First Discovery" badge is never emitted for
# FLASH runs (session counter stays at 0), so it would never match and the
# recording would idle for the full FLASH_MAX. Detect the result card instead.
wait_for_pattern "FLASH" "$FLASH_MAX" "Hypothesis|Flash error" || true

# --- TURBO ---
# After FLASH completes the TUI drops back to DISCOVER mode, so a single Tab
# only reaches FLASH. Cycle modes and confirm we are actually in TURBO (the
# header shows `[TURBO]`) before typing the topic.
for _ in $(seq 1 6); do
  clear_overlay
  tmux send-keys -t "$SESSION" Tab
  sleep 1.2
  f=$(capture_frame)
  if rg -q '\[TURBO\]' "$f" 2>/dev/null; then break; fi
done
clear_overlay
type_topic "$TURBO_TOPIC"
sleep 0.8
tmux send-keys -t "$SESSION" C-m
wait_for_pattern "TURBO" "$TURBO_MAX" "Discovery complete|G: Quality control progress 100%" || true

# Overlays after success
if tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux send-keys -t "$SESSION" C-S-c
  sleep 2
  cp "$(capture_frame)" "$DOCS/04_tui_v9_capabilities_overlay.txt" || true
  tmux send-keys -t "$SESSION" Escape
  sleep 1
fi

# Pick best frames
best=""
best_score=0
cnt=$(frame_count)
if [ "${cnt:-0}" -gt 0 ]; then
  for f in "$FRAMES"/frame_*.txt; do
    [[ -f "$f" ]] || continue
    score=$(rg -c "Dissertation|Hypothesis|Abstract|G: Quality|hypothesis" "$f" 2>/dev/null || echo 0)
    score=${score//[^0-9]/}
    if [ "${score:-0}" -gt "${best_score:-0}" ]; then best_score=$score; best="$f"; fi
  done
fi
if [[ -z "$best" ]] && [ "${cnt:-0}" -gt 0 ]; then
  best="$FRAMES/frame_$(printf '%05d' $((cnt - 1))).txt"
fi
if [[ -n "$best" && -f "$best" ]]; then
  cp "$best" "$DOCS/02_tui_v9_hypothesis_card.txt"
  cp "$best" "$DOCS/09_tui_v9_multi_paper_feed.txt"
fi
[[ -f "$DOCS/04_tui_v9_capabilities_overlay.txt" ]] || { [[ -n "$best" && -f "$best" ]] && cp "$best" "$DOCS/04_tui_v9_capabilities_overlay.txt" || true; }

tmux send-keys -t "$SESSION" C-c 2>/dev/null || true

echo "==> Render PNGs"
for pair in 02_tui_v9_hypothesis_card 04_tui_v9_capabilities_overlay 09_tui_v9_multi_paper_feed; do
  [[ -f "$DOCS/${pair}.txt" ]] && python3 "$PY" "$DOCS/${pair}.txt" "$DOCS/${pair}.png" "$FONT_SIZE"
done

cnt=$(frame_count)
echo "==> Build MP4 + GIF (${cnt} frames)"
WORK=$(mktemp -d)
LIST="$WORK/list.txt"
: >"$LIST"
# Keep the video at a watchable length: sample frames to ~150 and cap duration.
step=1
if [ "${cnt:-0}" -gt 180 ]; then step=$(( (cnt + 179) / 180 )); fi
idx=0
for f in "$FRAMES"/frame_*.txt; do
  if [ $((idx % step)) -ne 0 ]; then idx=$((idx + 1)); continue; fi
  png="$WORK/$(printf '%04d.png' "$idx")"
  python3 "$PY" "$f" "$png" "$FONT_SIZE" >/dev/null
  echo "file '$png'" >>"$LIST"
  echo "duration $FRAME_DUR" >>"$LIST"
  idx=$((idx + 1))
done
last_png=$(ls "$WORK"/*.png 2>/dev/null | tail -1)
[[ -n "$last_png" ]] && echo "file '$last_png'" >>"$LIST"

OUT_MP4="$DEMO/c4reqber_mission_demo_30s.mp4"
OUT_GIF="$DEMO/c4reqber_tui_demo.gif"
# Normalize every frame to a fixed 1280x720 canvas (captured frames vary in
# height); otherwise the concat demuxer fails on dimension mismatch.
VF="fps=10,scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p"
ffmpeg -y -f concat -safe 0 -i "$LIST" -vf "$VF" -c:v libx264 -pix_fmt yuv420p "$OUT_MP4"
ffmpeg -y -i "$OUT_MP4" -filter_complex "[0:v] fps=12,scale=1280:-1:flags=lanczos,split [a][b];[a] palettegen [p];[b][p] paletteuse" "$OUT_GIF"
cp "$OUT_MP4" "$ROOT/landing/assets/demo/c4reqber_mission_demo_30s.mp4"
cp "$OUT_GIF" "$ROOT/social-marketing/c4reqber_tui_demo.gif"
rm -rf "$FRAMES" "$WORK"

echo "==> Done"
ls -lh "$OUT_MP4" "$OUT_GIF" "$DOCS"/*.png 2>/dev/null
