#!/usr/bin/env bash
# preflight.sh — run before every `git push` to catch bugs locally.
#
# This script runs the same checks that production CI would run, but
# locally and in <30 seconds. If anything fails, exit non-zero so the
# push hook (or manual `&&`) can block the push.
#
# Checks:
#   1. go build ./...         — compile errors
#   2. go vet ./...           — suspicious constructs
#   3. go test -race -count=3 — race conditions + 3 stability runs
#   4. (optional) staticcheck — third-party linter if installed
#
# Usage:
#   ./scripts/preflight.sh            # run all checks
#   ./scripts/preflight.sh --no-race  # skip -race (faster, less safe)
#   ./scripts/preflight.sh --help     # show usage
#
# Exit codes:
#   0 — all checks pass
#   1 — one or more checks failed
#   2 — prerequisite missing (go not found, etc.)
set -euo pipefail

# ---- argument parsing ----
USE_RACE=1
SHOW_HELP=0
for arg in "$@"; do
  case "$arg" in
    --no-race)  USE_RACE=0 ;;
    --help|-h)  SHOW_HELP=1 ;;
    *)          echo "Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

if [ "$SHOW_HELP" -eq 1 ]; then
  sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

# ---- locate repo root ----
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$REPO_ROOT"

# ---- prerequisites ----
if ! command -v go >/dev/null 2>&1; then
  echo "ERROR: go binary not found in PATH" >&2
  exit 2
fi
GO_VERSION="$(go version)"
echo "Using $GO_VERSION"
echo "Repo root: $REPO_ROOT"
echo

# ---- 1. Build ----
echo "═══ 1/4 go build ./... (all Go modules) ═══"
BUILD_OK=1
for mod in $(find . -name "go.mod" -not -path "./vendor/*" -not -path "./.git/*" | sort); do
  mod_dir="$( dirname "$mod" )"
  echo "  → $mod_dir"
  if ! ( cd "$mod_dir" && go build ./... ); then
    echo "✗ BUILD FAILED in $mod_dir — fix compile errors before pushing" >&2
    BUILD_OK=0
  fi
done
if [ "$BUILD_OK" -eq 0 ]; then
  exit 1
fi
echo "✓ build OK"
echo

# ---- 2. Vet ----
echo "═══ 2/4 go vet ./... (all Go modules) ═══"
VET_OK=1
for mod in $(find . -name "go.mod" -not -path "./vendor/*" -not -path "./.git/*" | sort); do
  mod_dir="$( dirname "$mod" )"
  echo "  → $mod_dir"
  if ! ( cd "$mod_dir" && go vet ./... ); then
    echo "✗ VET FAILED in $mod_dir" >&2
    VET_OK=0
  fi
done
if [ "$VET_OK" -eq 0 ]; then
  exit 1
fi
echo "✓ vet OK"
echo

# ---- 3. Test (-race -count=3) ----
TEST_ARGS="-count=3"
if [ "$USE_RACE" -eq 1 ]; then
  TEST_ARGS="-race -count=3"
fi
echo "═══ 3/4 go test $TEST_ARGS ./... (all Go modules) ═══"
TEST_OK=1
for mod in $(find . -name "go.mod" -not -path "./vendor/*" -not -path "./.git/*" | sort); do
  mod_dir="$( dirname "$mod" )"
  echo "  → $mod_dir"
  if ! ( cd "$mod_dir" && go test $TEST_ARGS ./... ); then
    echo "✗ TESTS FAILED in $mod_dir" >&2
    TEST_OK=0
  fi
done
if [ "$TEST_OK" -eq 0 ]; then
  exit 1
fi
echo "✓ tests OK ($([ "$USE_RACE" -eq 1 ] && echo "race detector clean, " )3 stable runs)"
echo

# ---- 4. Staticcheck (optional) ----
echo "═══ 4/4 staticcheck (optional) ═══"
if command -v staticcheck >/dev/null 2>&1; then
  SC_OK=1
  for mod in $(find . -name "go.mod" -not -path "./vendor/*" -not -path "./.git/*" | sort); do
    mod_dir="$( dirname "$mod" )"
    echo "  → $mod_dir"
    if ! ( cd "$mod_dir" && staticcheck ./... ); then
      SC_OK=0
    fi
  done
  if [ "$SC_OK" -eq 0 ]; then
    echo "✗ STATICCHECK FAILED" >&2
    exit 1
  fi
  echo "✓ staticcheck OK"
else
  echo "— staticcheck not installed, skipping (install: go install honnef.co/go/tools/cmd/staticcheck@latest)"
fi
echo

# ---- summary ----
echo "════════════════════════════════════"
echo "✓ PREFLIGHT PASSED — safe to push"
echo "════════════════════════════════════"
