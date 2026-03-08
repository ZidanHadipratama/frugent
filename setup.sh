#!/bin/bash
# Frugent v2 — Setup Script
# Installs slash commands, skill files, tracker, and templates globally.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRUGENT_DIR="$HOME/.frugent"
CLAUDE_DIR="$HOME/.claude"
GEMINI_DIR="$HOME/.gemini"
CODEX_DIR="$HOME/.codex"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
DIM='\033[2m'
NC='\033[0m'

info()  { echo -e "  ${GREEN}✓${NC} $1"; }
warn()  { echo -e "  ${YELLOW}!${NC} $1"; }
error() { echo -e "  ${RED}✗${NC} $1"; exit 1; }

echo ""
echo "  Frugent v2 — Setup"
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
    info "Python $PY_VERSION"
else
    error "Python 3 not found. Install Python 3.6+ and try again."
fi

# --- Helper: copy with backup ---
safe_copy() {
    local src="$1"
    local dest="$2"
    local label="$3"

    if [ -f "$dest" ]; then
        if cmp -s "$src" "$dest"; then
            info "$label (up to date)"
            return
        fi
        local backup="${dest}.backup.$(date +%Y%m%d%H%M%S)"
        cp "$dest" "$backup"
        warn "$label (backed up existing → $(basename "$backup"))"
    fi

    cp "$src" "$dest"
    info "$label"
}

# --- Save repo path for `frugent update` ---
mkdir -p "$FRUGENT_DIR"
echo "$SCRIPT_DIR" > "$FRUGENT_DIR/.repo_path"

# --- Install tracker + templates ---
mkdir -p "$FRUGENT_DIR/templates"

safe_copy "$SCRIPT_DIR/tracker/tracker.py" "$FRUGENT_DIR/tracker.py" "tracker.py"
chmod +x "$FRUGENT_DIR/tracker.py"

for template in "$SCRIPT_DIR"/templates/*; do
    if [ -f "$template" ]; then
        tname=$(basename "$template")
        safe_copy "$template" "$FRUGENT_DIR/templates/$tname" "template: $tname"
    fi
done

# --- Install skill files ---
mkdir -p "$CLAUDE_DIR"
mkdir -p "$GEMINI_DIR"
mkdir -p "$CODEX_DIR"

safe_copy "$SCRIPT_DIR/skills/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md" "CLAUDE.md skill"
safe_copy "$SCRIPT_DIR/skills/GEMINI.md" "$GEMINI_DIR/GEMINI.md" "GEMINI.md skill"
safe_copy "$SCRIPT_DIR/skills/CODEX.md" "$CODEX_DIR/CODEX.md" "CODEX.md skill"

# --- Install slash commands ---
echo ""
echo "  Installing commands..."

mkdir -p "$CLAUDE_DIR/commands"
mkdir -p "$GEMINI_DIR/commands"
mkdir -p "$CODEX_DIR/commands"

for cmd_file in "$SCRIPT_DIR"/commands/frugent-*.md; do
    if [ -f "$cmd_file" ]; then
        cmd_name=$(basename "$cmd_file")
        safe_copy "$cmd_file" "$CLAUDE_DIR/commands/$cmd_name" "claude: /$cmd_name"
        safe_copy "$cmd_file" "$GEMINI_DIR/commands/$cmd_name" "gemini: /$cmd_name"
        safe_copy "$cmd_file" "$CODEX_DIR/commands/$cmd_name" "codex: /$cmd_name"
    fi
done

# --- Configure Gemini telemetry ---
GEMINI_SETTINGS="$GEMINI_DIR/settings.json"
TELEMETRY_FILE="$FRUGENT_DIR/gemini-telemetry.jsonl"

if [ -f "$GEMINI_SETTINGS" ]; then
    if python3 -c "
import json, sys
with open('$GEMINI_SETTINGS') as f:
    s = json.load(f)
t = s.get('telemetry', {})
if t.get('enabled') and t.get('outfile') == '$TELEMETRY_FILE':
    sys.exit(0)
sys.exit(1)
" 2>/dev/null; then
        info "Gemini telemetry (already configured)"
    else
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
        info "Gemini telemetry → $TELEMETRY_FILE"
    fi
else
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
    info "Gemini telemetry → $TELEMETRY_FILE"
fi

# --- Install frugent update CLI ---
safe_copy "$SCRIPT_DIR/frugent.py" "$FRUGENT_DIR/frugent.py" "frugent.py (update CLI)"
chmod +x "$FRUGENT_DIR/frugent.py"

LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

SYMLINK="$LOCAL_BIN/frugent"
if [ -L "$SYMLINK" ] || [ -f "$SYMLINK" ]; then
    rm "$SYMLINK"
fi
ln -s "$FRUGENT_DIR/frugent.py" "$SYMLINK"
info "frugent → $SYMLINK"

if ! echo "$PATH" | grep -q "$LOCAL_BIN"; then
    warn "$LOCAL_BIN is not on your PATH"
    echo "      Add to your shell profile: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# --- Done ---
echo ""
echo "  Setup complete!"
echo ""
echo "  Installed:"
echo "    ~/.frugent/tracker.py           — quota tracker"
echo "    ~/.frugent/templates/           — document templates ($(ls "$FRUGENT_DIR/templates/" | wc -l) files)"
echo "    ~/.local/bin/frugent            — update CLI"
echo "    ~/.claude/CLAUDE.md             — session rules"
echo "    ~/.gemini/GEMINI.md             — session rules"
echo "    ~/.codex/CODEX.md              — session rules"
echo "    ~/.claude/commands/frugent-*    — slash commands"
echo "    ~/.gemini/commands/frugent-*    — slash commands"
echo "    ~/.codex/commands/frugent-*     — slash commands"
echo ""
echo "  Usage:"
echo "    Open any project in claude, gemini, or codex and type:"
echo "      /frugent-init        — set up frugent for the project"
echo "      /frugent-plan        — create the execution plan"
echo "      /frugent-execute     — start working on tasks"
echo "      /frugent-status      — check quota and progress"
echo ""
