#!/usr/bin/env bash
# Create .venv, install anything missing, and start the local dashboard.
# Run from anywhere: ./setup.sh
# A script cannot leave its caller's shell activated. After Solara stops,
# the script prints the command that activates .venv in a new terminal.

set -euo pipefail

cd "$(dirname "$0")"

echo "Schelling Operational Status"
echo "Setting up a local dashboard."
echo

pick_python() {
    local cmd
    for cmd in python3.12 python3; do
        if command -v "$cmd" >/dev/null 2>&1 \
            && "$cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)'; then
            echo "$cmd"
            return 0
        fi
    done
    return 1
}

if ! PYTHON="$(pick_python)"; then
    echo "This model needs Python 3.12 or newer."
    echo "Install it, then run ./setup.sh again."
    exit 1
fi

echo "Using $($PYTHON --version)."

if [[ ! -d .venv ]]; then
    echo "Creating a virtual environment in .venv ..."
    "$PYTHON" -m venv .venv
else
    echo "Virtual environment already exists at .venv."
fi

# shellcheck disable=SC1091
source .venv/bin/activate

deps_current() {
    python - <<'PY'
import importlib.metadata as md
import re
import sys
from pathlib import Path

def version_tuple(text):
    parts = []
    for piece in re.split(r"[._+-]", text):
        if piece.isdigit():
            parts.append(int(piece))
        else:
            break
    return tuple(parts)

try:
    import matplotlib
    import networkx
    import solara
except ImportError:
    sys.exit(1)

for raw in Path("requirements.txt").read_text().splitlines():
    line = raw.split("#", 1)[0].strip()
    if not line:
        continue
    match = re.fullmatch(
        r"([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*(==|>=|<=|>|<)\s*([A-Za-z0-9*_.+-]+)",
        line,
    )
    if match is None:
        sys.exit(1)
    name, op, wanted = match.groups()
    try:
        installed = md.version(name)
    except md.PackageNotFoundError:
        sys.exit(1)
    got = version_tuple(installed)
    need = version_tuple(wanted)
    if op == "==" and got != need:
        sys.exit(1)
    if op == ">=" and got < need:
        sys.exit(1)
    if op == ">" and got <= need:
        sys.exit(1)
    if op == "<=" and got > need:
        sys.exit(1)
    if op == "<" and got >= need:
        sys.exit(1)
PY
}

echo "Checking dependencies from requirements.txt ..."
if deps_current; then
    echo "Dependencies are already installed."
else
    echo "Installing dependencies from requirements.txt ..."
    python -m pip install -r requirements.txt
fi

echo
echo "Starting the dashboard. Open the local URL Solara prints below."
echo "Stop the dashboard with Ctrl+C."
echo "A new terminal does not keep this environment. Activate it with:"
echo "  source .venv/bin/activate"
echo

trap 'echo; echo "Dashboard stopped."; echo "To use this environment later, run: source .venv/bin/activate"; exit 0' INT TERM

solara run app.py
status=$?
echo
echo "Dashboard stopped."
echo "To use this environment later, run: source .venv/bin/activate"
exit "$status"
