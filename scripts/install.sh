#!/bin/sh
set -eu

DOPAMINE_AGENT="all"
DOPAMINE_SCOPE="user"
DOPAMINE_PROJECT_DIR="$(pwd)"
DOPAMINE_SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DOPAMINE_REPO_DIR=$(CDPATH= cd -- "$DOPAMINE_SCRIPT_DIR/.." && pwd)
DOPAMINE_SOURCE="$DOPAMINE_REPO_DIR/skills/dopamine"

usage() {
  printf '%s\n' \
    'Usage: ./scripts/install.sh [--agent codex|claude|all] [--scope user|project] [--project PATH]' \
    '' \
    'Examples:' \
    '  ./scripts/install.sh --agent all --scope user' \
    '  ./scripts/install.sh --agent codex --scope project --project /path/to/repo'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --agent)
      [ "$#" -ge 2 ] || { printf '%s\n' 'Missing value for --agent' >&2; exit 2; }
      DOPAMINE_AGENT=$2
      shift 2
      ;;
    --scope)
      [ "$#" -ge 2 ] || { printf '%s\n' 'Missing value for --scope' >&2; exit 2; }
      DOPAMINE_SCOPE=$2
      shift 2
      ;;
    --project)
      [ "$#" -ge 2 ] || { printf '%s\n' 'Missing value for --project' >&2; exit 2; }
      DOPAMINE_PROJECT_DIR=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$DOPAMINE_AGENT" in
  codex|claude|all) ;;
  *) printf 'Invalid agent: %s\n' "$DOPAMINE_AGENT" >&2; exit 2 ;;
esac

case "$DOPAMINE_SCOPE" in
  user|project) ;;
  *) printf 'Invalid scope: %s\n' "$DOPAMINE_SCOPE" >&2; exit 2 ;;
esac

[ -f "$DOPAMINE_SOURCE/SKILL.md" ] || {
  printf 'Skill source is missing: %s\n' "$DOPAMINE_SOURCE/SKILL.md" >&2
  exit 1
}

if [ "$DOPAMINE_SCOPE" = "project" ]; then
  [ -d "$DOPAMINE_PROJECT_DIR" ] || {
    printf 'Project directory does not exist: %s\n' "$DOPAMINE_PROJECT_DIR" >&2
    exit 1
  }
  DOPAMINE_PROJECT_DIR=$(CDPATH= cd -- "$DOPAMINE_PROJECT_DIR" && pwd)
  [ "$DOPAMINE_PROJECT_DIR" != "/" ] || {
    printf '%s\n' 'Refusing to install project skills at the filesystem root.' >&2
    exit 1
  }
fi

codex_target() {
  if [ "$DOPAMINE_SCOPE" = "project" ]; then
    printf '%s\n' "$DOPAMINE_PROJECT_DIR/.agents/skills/dopamine"
  else
    printf '%s\n' "$HOME/.agents/skills/dopamine"
  fi
}

claude_target() {
  if [ "$DOPAMINE_SCOPE" = "project" ]; then
    printf '%s\n' "$DOPAMINE_PROJECT_DIR/.claude/skills/dopamine"
  else
    printf '%s\n' "$HOME/.claude/skills/dopamine"
  fi
}

preflight() {
  DOPAMINE_TARGET=$1
  if [ -e "$DOPAMINE_TARGET" ] || [ -L "$DOPAMINE_TARGET" ]; then
    printf 'Refusing to overwrite existing installation: %s\n' "$DOPAMINE_TARGET" >&2
    printf '%s\n' 'Move or remove it explicitly, then run the installer again.' >&2
    exit 1
  fi
}

install_one() {
  DOPAMINE_LABEL=$1
  DOPAMINE_TARGET=$2
  DOPAMINE_PARENT=$(dirname -- "$DOPAMINE_TARGET")
  mkdir -p -- "$DOPAMINE_PARENT"
  cp -R -- "$DOPAMINE_SOURCE" "$DOPAMINE_TARGET"
  printf 'Installed Dopamine for %s: %s\n' "$DOPAMINE_LABEL" "$DOPAMINE_TARGET"
}

if [ "$DOPAMINE_AGENT" = "codex" ] || [ "$DOPAMINE_AGENT" = "all" ]; then
  DOPAMINE_CODEX_TARGET=$(codex_target)
  preflight "$DOPAMINE_CODEX_TARGET"
fi
if [ "$DOPAMINE_AGENT" = "claude" ] || [ "$DOPAMINE_AGENT" = "all" ]; then
  DOPAMINE_CLAUDE_TARGET=$(claude_target)
  preflight "$DOPAMINE_CLAUDE_TARGET"
fi

if [ "$DOPAMINE_AGENT" = "codex" ] || [ "$DOPAMINE_AGENT" = "all" ]; then
  install_one Codex "$DOPAMINE_CODEX_TARGET"
fi
if [ "$DOPAMINE_AGENT" = "claude" ] || [ "$DOPAMINE_AGENT" = "all" ]; then
  install_one 'Claude Code' "$DOPAMINE_CLAUDE_TARGET"
fi

printf '%s\n' 'Invoke it with $dopamine in Codex or /dopamine in Claude Code.'
