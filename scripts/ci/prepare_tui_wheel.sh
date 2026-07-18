#!/usr/bin/env bash
# Prepare platform c4tui-v9 for inclusion in the wheel (force-include in pyproject).
# Usage (CI / release): ./scripts/ci/prepare_tui_wheel.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
V9="$ROOT/src/tui/v9"
BIN="$V9/bin"
mkdir -p "$BIN"

if [[ -n "${C4REQBER_TUI_PREBUILT:-}" && -f "${C4REQBER_TUI_PREBUILT}" ]]; then
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*|Windows_NT) dest="$BIN/c4tui-v9.exe" ;;
    *) dest="$BIN/c4tui-v9" ;;
  esac
  cp -f "$C4REQBER_TUI_PREBUILT" "$dest"
  chmod +x "$dest" || true
  echo "Prepared TUI binary from C4REQBER_TUI_PREBUILT → $dest"
  exit 0
fi

if ! command -v go >/dev/null 2>&1; then
  echo "go not found — wheel will rely on runtime download (tui_binary.ensure_tui_binary)"
  exit 0
fi

out="$BIN/c4tui-v9"
[[ "$(uname -s)" == MINGW* || "$(uname -s)" == MSYS* ]] && out="$BIN/c4tui-v9.exe"

# Prefer cmd package if present
if [[ -d "$V9/cmd/c4tui-v9" ]]; then
  (cd "$V9" && go build -ldflags="-s -w" -o "$out" ./cmd/c4tui-v9)
else
  (cd "$V9" && go build -ldflags="-s -w" -o "$out" .)
fi
chmod +x "$out" || true
echo "Built TUI for wheel → $out ($(wc -c < "$out") bytes)"
