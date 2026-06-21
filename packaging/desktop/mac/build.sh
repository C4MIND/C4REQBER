#!/usr/bin/env bash
# Build C4REQBER.app for macOS (PyInstaller + bundled c4tui-v9).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "${ROOT}"

echo "==> Build Go TUI binaries"
make -C src/tui/v9 release-all

ARCH="$(uname -m)"
case "${ARCH}" in
  arm64) TUI_SRC="src/tui/v9/dist/c4tui-v9-darwin-arm64" ;;
  x86_64) TUI_SRC="src/tui/v9/dist/c4tui-v9-darwin-amd64" ;;
  *) echo "Unsupported arch: ${ARCH}"; exit 1 ;;
esac

echo "==> PyInstaller desktop bundle"
python3 -m pip install --quiet pyinstaller build hatchling
pyinstaller packaging/desktop/c4reqber-desktop.spec --noconfirm

APP="dist/C4REQBER.app"
mkdir -p "${APP}/Contents/Resources"
cp "${TUI_SRC}" "${APP}/Contents/Resources/c4tui-v9"
chmod +x "${APP}/Contents/Resources/c4tui-v9"
cp packaging/desktop/mac/Info.plist "${APP}/Contents/Info.plist"

echo "==> Built ${APP}"
echo "Optional notarization: packaging/desktop/mac/notarize-mac.sh ${APP}"