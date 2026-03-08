#!/bin/bash
# Frugent v1 — Setup Script
# Installs CLI, skill files, tracker, and templates globally.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRUGENT_DIR="$HOME/.frugent"
CLAUDE_DIR="$HOME/.claude"
GEMINI_DIR="$HOME/.gemini"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No color

info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!!]${NC} $1"; }
error() { echo -e "${RED}[ERR]${NC} $1"; exit 1; }

echo ""
echo "  Frugent v1 — Setup"
echo "  ==================="
echo ""

# --- Check Python 3.6+ ---
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

    if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 6 ]; }; then
        error "Python 3.6+ required (found $PY_VERSION)"
    fi
    info "Python $PY_VERSION found"
else
    error "Python 3 not found. Install Python 3.6+ and try again."
fi

# --- Helper: copy with backup ---
safe_copy() {
    local src="$1"
    local dest="$2"
    local label="$3"

    if [ -f "$dest" ]; then
        # Check if content is identical
        if cmp -s "$src" "$dest"; then
            info "$label already up to date"
            return
        fi

        # Back up existing file
        local backup="${dest}.backup.$(date +%Y%m%d%H%M%S)"
        cp "$dest" "$backup"
        warn "$label exists — backed up to $(basename "$backup")"
    fi

    cp "$src" "$dest"
    info "$label installed"
}

# --- Install ~/.frugent/ ---
mkdir -p "$FRUGENT_DIR/templates"

# Save repo path for `frugent update`
echo "$SCRIPT_DIR" > "$FRUGENT_DIR/.repo_path"
info "Repo path saved for updates"

safe_copy "$SCRIPT_DIR/frugent.py" "$FRUGENT_DIR/frugent.py" "frugent.py"
chmod +x "$FRUGENT_DIR/frugent.py"

# Keep tracker.py as alias for agents that call it directly
if [ -f "$SCRIPT_DIR/tracker/tracker.py" ]; then
    safe_copy "$SCRIPT_DIR/tracker/tracker.py" "$FRUGENT_DIR/tracker.py" "tracker.py (agent compat)"
    chmod +x "$FRUGENT_DIR/tracker.py"
fi

for template in "$SCRIPT_DIR"/templates/*; do
    if [ -f "$template" ]; then
        tname=$(basename "$template")
        safe_copy "$template" "$FRUGENT_DIR/templates/$tname" "template: $tname"
    fi
done

# --- Install skill files ---
mkdir -p "$CLAUDE_DIR"
mkdir -p "$GEMINI_DIR"

safe_copy "$SCRIPT_DIR/skills/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md" "CLAUDE.md skill"
safe_copy "$SCRIPT_DIR/skills/GEMINI.md" "$GEMINI_DIR/GEMINI.md" "GEMINI.md skill"

# --- Configure Gemini telemetry ---
GEMINI_SETTINGS="$GEMINI_DIR/settings.json"
TELEMETRY_FILE="$FRUGENT_DIR/gemini-telemetry.jsonl"

if [ -f "$GEMINI_SETTINGS" ]; then
    # Check if telemetry is already configured
    if python3 -c "
import json, sys
with open('$GEMINI_SETTINGS') as f:
    s = json.load(f)
t = s.get('telemetry', {})
if t.get('enabled') and t.get('outfile') == '$TELEMETRY_FILE':
    sys.exit(0)
sys.exit(1)
" 2>/dev/null; then
        info "Gemini telemetry already configured"
    else
        # Merge telemetry config into existing settings
        python3 -c "
import json
with open('$GEMINI_SETTINGS') as f:
    s = json.load(f)
s['telemetry'] = {
    'enabled': True,
    'target': 'local',
    'outfile': '$TELEMETRY_FILE',
    'logPrompts': False
}
with open('$GEMINI_SETTINGS', 'w') as f:
    json.dump(s, f, indent=2)
"
        info "Gemini telemetry enabled → $TELEMETRY_FILE"
    fi
else
    # Create settings.json with telemetry config
    python3 -c "
import json
s = {
    'telemetry': {
        'enabled': True,
        'target': 'local',
        'outfile': '$TELEMETRY_FILE',
        'logPrompts': False
    }
}
with open('$GEMINI_SETTINGS', 'w') as f:
    json.dump(s, f, indent=2)
"
    info "Gemini settings created with telemetry → $TELEMETRY_FILE"
fi

# --- Install frugent to PATH ---
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

SYMLINK="$LOCAL_BIN/frugent"
if [ -L "$SYMLINK" ] || [ -f "$SYMLINK" ]; then
    rm "$SYMLINK"
fi
ln -s "$FRUGENT_DIR/frugent.py" "$SYMLINK"
info "frugent symlinked to $SYMLINK"

# Check if ~/.local/bin is on PATH
if ! echo "$PATH" | grep -q "$LOCAL_BIN"; then
    warn "$LOCAL_BIN is not on your PATH"
    echo "      Add this to your shell profile (~/.bashrc or ~/.zshrc):"
    echo "      export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# --- Done ---
echo ""
echo "  Setup complete!"
echo ""
echo "  Installed:"
echo "    ~/.frugent/frugent.py        — CLI launcher + tracker"
echo "    ~/.frugent/tracker.py        — tracker (agent compat)"
echo "    ~/.frugent/templates/        — document templates ($(ls "$FRUGENT_DIR/templates/" | wc -l) files)"
echo "    ~/.claude/CLAUDE.md          — planner skill"
echo "    ~/.gemini/GEMINI.md          — executor skill"
echo "    ~/.local/bin/frugent         — symlink (on PATH)"
echo ""
echo "  Quick start:"
echo "    cd your-project"
echo "    frugent"
echo ""
echo "  Check quota:"
echo "    frugent status"
echo ""
