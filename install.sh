#!/usr/bin/env bash
set -euo pipefail

echo ""
echo "=================================================="
echo "  MEGASUS Installer"
echo "  Platform: $(uname -s) ($(uname -m))"
echo "=================================================="
echo ""

PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        V=$("$cmd" -c "import sys; print('%d.%d' % (sys.version_info.major, sys.version_info.minor))" 2>/dev/null || echo "0.0")
        MAJOR=$(echo "$V" | cut -d. -f1)
        MINOR=$(echo "$V" | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ] 2>/dev/null; then
            PYTHON="$cmd"; break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.8+ not found."
    echo "  Ubuntu: sudo apt install python3"
    echo "  macOS:  brew install python3"
    echo "  Termux: pkg install python"
    exit 1
fi

echo "Using: $PYTHON"
$PYTHON --version
echo ""
$PYTHON install.py
echo ""
echo "Done! Run: python3 megasus.py"
