#!/bin/sh
set -eu

DOPAMINE_AGENT="all"
DOPAMINE_SCOPE="user"
DOPAMINE_PROJECT_DIR="$(pwd)"
DOPAMINE_SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DOPAMINE_REPO_DIR=$(CDPATH= cd -- "$DOPAMINE_SCRIPT_DIR/.." && pwd)

usage() {
  printf '%s\n' \
    'Usage: ./scripts/install.sh [--agent NAME] [--scope user|project] [--project PATH]' \
    '' \
    'NAME: codex, claude, opencode, grok, openclaw, cursor, windsurf, cline,' \
    '      copilot, kiro, qoder, portable, or all' \
    '' \
    'The portable target installs AGENTS.md for AGENTS-compatible tools.' \
    'Cursor and Qoder support project scope only; all skips them at user scope.'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --agent) [ "$#" -ge 2 ] || { echo 'Missing value for --agent' >&2; exit 2; }; DOPAMINE_AGENT=$2; shift 2 ;;
    --scope) [ "$#" -ge 2 ] || { echo 'Missing value for --scope' >&2; exit 2; }; DOPAMINE_SCOPE=$2; shift 2 ;;
    --project) [ "$#" -ge 2 ] || { echo 'Missing value for --project' >&2; exit 2; }; DOPAMINE_PROJECT_DIR=$2; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

case "$DOPAMINE_AGENT" in
  codex|claude|opencode|grok|openclaw|cursor|windsurf|cline|copilot|kiro|qoder|portable|all) ;;
  *) printf 'Invalid agent: %s\n' "$DOPAMINE_AGENT" >&2; exit 2 ;;
esac
case "$DOPAMINE_SCOPE" in user|project) ;; *) printf 'Invalid scope: %s\n' "$DOPAMINE_SCOPE" >&2; exit 2 ;; esac

if [ "$DOPAMINE_SCOPE" = "project" ]; then
  [ -d "$DOPAMINE_PROJECT_DIR" ] || { printf 'Project directory does not exist: %s\n' "$DOPAMINE_PROJECT_DIR" >&2; exit 1; }
  DOPAMINE_PROJECT_DIR=$(CDPATH= cd -- "$DOPAMINE_PROJECT_DIR" && pwd)
  [ "$DOPAMINE_PROJECT_DIR" != "/" ] || { echo 'Refusing to install project integrations at the filesystem root.' >&2; exit 1; }
fi

set_mapping() {
  DOPAMINE_NAME=$1
  DOPAMINE_KIND=file
  case "$DOPAMINE_NAME:$DOPAMINE_SCOPE" in
    codex:project) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/skills/dopamine"; DOPAMINE_TARGET="$DOPAMINE_PROJECT_DIR/.agents/skills/dopamine"; DOPAMINE_KIND=directory; DOPAMINE_LABEL=Codex ;;
    codex:user) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/skills/dopamine"; DOPAMINE_TARGET="$HOME/.agents/skills/dopamine"; DOPAMINE_KIND=directory; DOPAMINE_LABEL=Codex ;;
    claude:project) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/skills/dopamine"; DOPAMINE_TARGET="$DOPAMINE_PROJECT_DIR/.claude/skills/dopamine"; DOPAMINE_KIND=directory; DOPAMINE_LABEL='Claude Code' ;;
    claude:user) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/skills/dopamine"; DOPAMINE_TARGET="$HOME/.claude/skills/dopamine"; DOPAMINE_KIND=directory; DOPAMINE_LABEL='Claude Code' ;;
    opencode:project) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/skills/dopamine"; DOPAMINE_TARGET="$DOPAMINE_PROJECT_DIR/.opencode/skills/dopamine"; DOPAMINE_KIND=directory; DOPAMINE_LABEL=OpenCode ;;
    opencode:user) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/skills/dopamine"; DOPAMINE_TARGET="$HOME/.config/opencode/skills/dopamine"; DOPAMINE_KIND=directory; DOPAMINE_LABEL=OpenCode ;;
    grok:project) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/skills/dopamine"; DOPAMINE_TARGET="$DOPAMINE_PROJECT_DIR/.grok/skills/dopamine"; DOPAMINE_KIND=directory; DOPAMINE_LABEL='Grok Build' ;;
    grok:user) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/skills/dopamine"; DOPAMINE_TARGET="$HOME/.grok/skills/dopamine"; DOPAMINE_KIND=directory; DOPAMINE_LABEL='Grok Build' ;;
    openclaw:project) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/skills/dopamine"; DOPAMINE_TARGET="$DOPAMINE_PROJECT_DIR/.openclaw/skills/dopamine"; DOPAMINE_KIND=directory; DOPAMINE_LABEL=OpenClaw ;;
    openclaw:user) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/skills/dopamine"; DOPAMINE_TARGET="$HOME/.openclaw/skills/dopamine"; DOPAMINE_KIND=directory; DOPAMINE_LABEL=OpenClaw ;;
    cursor:project) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/.cursor/rules/dopamine.mdc"; DOPAMINE_TARGET="$DOPAMINE_PROJECT_DIR/.cursor/rules/dopamine.mdc"; DOPAMINE_LABEL=Cursor ;;
    windsurf:project) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/.windsurf/rules/dopamine.md"; DOPAMINE_TARGET="$DOPAMINE_PROJECT_DIR/.windsurf/rules/dopamine.md"; DOPAMINE_LABEL=Windsurf ;;
    windsurf:user) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/AGENTS.md"; DOPAMINE_TARGET="$HOME/.codeium/windsurf/memories/global_rules.md"; DOPAMINE_LABEL=Windsurf ;;
    cline:project) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/.clinerules/dopamine.md"; DOPAMINE_TARGET="$DOPAMINE_PROJECT_DIR/.clinerules/dopamine.md"; DOPAMINE_LABEL=Cline ;;
    cline:user) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/.clinerules/dopamine.md"; DOPAMINE_TARGET="$HOME/Documents/Cline/Rules/dopamine.md"; DOPAMINE_LABEL=Cline ;;
    copilot:project) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/.github/copilot-instructions.md"; DOPAMINE_TARGET="$DOPAMINE_PROJECT_DIR/.github/copilot-instructions.md"; DOPAMINE_LABEL='GitHub Copilot' ;;
    copilot:user) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/.github/copilot-instructions.md"; DOPAMINE_TARGET="$HOME/.copilot/copilot-instructions.md"; DOPAMINE_LABEL='GitHub Copilot CLI' ;;
    kiro:project) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/.kiro/steering/dopamine.md"; DOPAMINE_TARGET="$DOPAMINE_PROJECT_DIR/.kiro/steering/dopamine.md"; DOPAMINE_LABEL=Kiro ;;
    kiro:user) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/.kiro/steering/dopamine.md"; DOPAMINE_TARGET="$HOME/.kiro/steering/dopamine.md"; DOPAMINE_LABEL=Kiro ;;
    qoder:project) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/.qoder/rules/dopamine.md"; DOPAMINE_TARGET="$DOPAMINE_PROJECT_DIR/.qoder/rules/dopamine.md"; DOPAMINE_LABEL=Qoder ;;
    portable:project) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/AGENTS.md"; DOPAMINE_TARGET="$DOPAMINE_PROJECT_DIR/AGENTS.md"; DOPAMINE_LABEL='AGENTS-compatible agents' ;;
    portable:user) DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/AGENTS.md"; DOPAMINE_TARGET="$HOME/.agents/AGENTS.md"; DOPAMINE_LABEL='AGENTS-compatible agents' ;;
    *) printf '%s does not expose a verified %s-scope filesystem target.\n' "$DOPAMINE_NAME" "$DOPAMINE_SCOPE" >&2; exit 2 ;;
  esac
}

preflight() {
  set_mapping "$1"
  [ -e "$DOPAMINE_SOURCE" ] || { printf 'Integration source is missing: %s\n' "$DOPAMINE_SOURCE" >&2; exit 1; }
  if [ -e "$DOPAMINE_TARGET" ] || [ -L "$DOPAMINE_TARGET" ]; then
    printf 'Refusing to overwrite existing installation: %s\n' "$DOPAMINE_TARGET" >&2
    echo 'Move, merge, or remove it explicitly, then run the installer again.' >&2
    exit 1
  fi
}

install_one() {
  set_mapping "$1"
  mkdir -p -- "$(dirname -- "$DOPAMINE_TARGET")"
  if [ "$DOPAMINE_KIND" = directory ]; then cp -R -- "$DOPAMINE_SOURCE" "$DOPAMINE_TARGET"; else cp -- "$DOPAMINE_SOURCE" "$DOPAMINE_TARGET"; fi
  printf 'Installed Dopamine for %s: %s\n' "$DOPAMINE_LABEL" "$DOPAMINE_TARGET"
}

if [ "$DOPAMINE_AGENT" = all ]; then
  if [ "$DOPAMINE_SCOPE" = project ]; then
    DOPAMINE_SELECTION='codex claude opencode grok openclaw cursor windsurf cline copilot kiro qoder'
  else
    DOPAMINE_SELECTION='codex claude opencode grok openclaw windsurf cline copilot kiro'
  fi
else
  DOPAMINE_SELECTION=$DOPAMINE_AGENT
fi

for DOPAMINE_ITEM in $DOPAMINE_SELECTION; do preflight "$DOPAMINE_ITEM"; done
for DOPAMINE_ITEM in $DOPAMINE_SELECTION; do install_one "$DOPAMINE_ITEM"; done

echo 'Installation complete. The selected agents discover Dopamine automatically from their native path.'
