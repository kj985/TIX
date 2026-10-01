#!/bin/bash
# One-step launcher for the gig tool.
#
#   ./start.sh                   start the dashboard (default)
#   ./start.sh import            import gigs from Bandsintown
#   ./start.sh import --sample   import the sample gigs
#   ./start.sh clear-sample      delete the sample gigs
#
# The first run takes a minute while it installs what it needs.
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed. Follow step 1 in README.md, then try again."
  exit 1
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "This tool needs Python 3.11 or newer, but 'python3' is $(python3 --version 2>&1)."
  echo "Install the latest Python from https://www.python.org/downloads/ (README step 1),"
  echo "then close and reopen Terminal and try again."
  exit 1
fi

if [ ! -d .venv ]; then
  echo "First run: setting up (this only happens once)..."
  python3 -m venv .venv
fi
.venv/bin/pip install --quiet --disable-pip-version-check -r requirements.txt

if [ $# -eq 0 ]; then
  set -- run
fi
exec .venv/bin/python -m gigtool "$@"
