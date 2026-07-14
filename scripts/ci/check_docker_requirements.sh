#!/bin/sh
# Fail CI if committed requirements-docker.txt drifts from filter_requirements.sh output.
set -eu
ROOT="${CI_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$ROOT"
sh scripts/ci/filter_requirements.sh requirements.txt /tmp/requirements-docker.expected.txt
# Strip header comments from committed file for comparison
grep -Ev '^\s*#' requirements-docker.txt | grep -v '^[[:space:]]*$' > /tmp/requirements-docker.committed.txt
grep -Ev '^\s*#' /tmp/requirements-docker.expected.txt | grep -v '^[[:space:]]*$' > /tmp/requirements-docker.expected.clean.txt
if ! diff -u /tmp/requirements-docker.expected.clean.txt /tmp/requirements-docker.committed.txt; then
  echo "ERROR: requirements-docker.txt is out of sync. Run:" >&2
  echo "  sh scripts/ci/filter_requirements.sh requirements.txt requirements-docker.txt" >&2
  exit 1
fi
echo "requirements-docker.txt OK"
