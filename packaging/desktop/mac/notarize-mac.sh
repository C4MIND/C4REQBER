#!/usr/bin/env bash
# Apple notarization pipeline for C4REQBER.app
# Requires: Developer ID Application cert, notarytool credentials.
#
# Env (human-provided):
#   APPLE_ID          — Apple ID email
#   APPLE_APP_PASSWORD — app-specific password
#   TEAM_ID           — 10-char Team ID
#   SIGNING_IDENTITY  — "Developer ID Application: Your Name (TEAMID)"
#
# Usage:
#   ./notarize-mac.sh dist/C4REQBER.app
set -euo pipefail

APP_PATH="${1:-dist/C4REQBER.app}"
ZIP_PATH="${APP_PATH%.app}.zip"

: "${APPLE_ID:?Set APPLE_ID}"
: "${APPLE_APP_PASSWORD:?Set APPLE_APP_PASSWORD}"
: "${TEAM_ID:?Set TEAM_ID}"
: "${SIGNING_IDENTITY:?Set SIGNING_IDENTITY}"

echo "==> Codesign ${APP_PATH}"
codesign --deep --force --options runtime --sign "${SIGNING_IDENTITY}" "${APP_PATH}"
codesign --verify --verbose "${APP_PATH}"

echo "==> Zip for notarization"
ditto -c -k --keepParent "${APP_PATH}" "${ZIP_PATH}"

echo "==> Submit to Apple notaryservice"
xcrun notarytool submit "${ZIP_PATH}" \
  --apple-id "${APPLE_ID}" \
  --password "${APPLE_APP_PASSWORD}" \
  --team-id "${TEAM_ID}" \
  --wait

echo "==> Staple ticket"
xcrun stapler staple "${APP_PATH}"

echo "==> Done: ${APP_PATH} is notarized and stapled"
spctl --assess --verbose "${APP_PATH}"