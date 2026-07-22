#!/usr/bin/env bash
# Prepare platform c4tui-v9 for inclusion in the wheel (force-include in pyproject).
# Usage (CI / release): ./scripts/ci/prepare_tui_wheel.sh
# Set C4REQBER_TUI_WHEEL_STRICT=1 on release publish jobs to fail if no binary.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
V9="$ROOT/src/tui/v9"
BIN="$V9/bin"
mkdir -p "$BIN"
STRICT="${C4REQBER_TUI_WHEEL_STRICT:-0}"

_have_binary() {
  [[ -f "$BIN/c4tui-v9" || -f "$BIN/c4tui-v9.exe" ]]
}

_fail_or_soft() {
  local msg="$1"
  if [[ "$STRICT" == "1" ]]; then
    echo "ERROR: $msg (C4REQBER_TUI_WHEEL_STRICT=1)" >&2
    exit 1
  fi
  echo "$msg — wheel will rely on runtime download (tui_binary.ensure_tui_binary)"
  exit 0
}

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
  _fail_or_soft "go not found"
fi

out="$BIN/c4tui-v9"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*|Windows_NT) out="$BIN/c4tui-v9.exe" ;;
esac

# Prefer cmd package if present
if [[ -d "$V9/cmd/c4tui-v9" ]]; then
  (cd "$V9" && go build -ldflags="-s -w" -o "$out" ./cmd/c4tui-v9)
else
  (cd "$V9" && go build -ldflags="-s -w" -o "$out" .)
fi
chmod +x "$out" || true

if ! _have_binary; then
  _fail_or_soft "TUI binary missing after build"
fi

echo "Built TUI for wheel → $out ($(wc -c < "$out") bytes)"
