#!/usr/bin/env bash
# Copy the skilltrim agent skill into host skill folders.
# macOS/Linux primary. Does not launch agents or claim a host loaded the skill.
# Syntax-check with: bash -n scripts/install-skill.sh
set -euo pipefail

HOST=all
SCOPE=user

usage() {
  cat <<'EOF'
Usage: bash scripts/install-skill.sh [--host HOST] [--scope SCOPE]

Copy SKILL.md and the files the skill uses into a host folder named skilltrim.
SKILL.md sits directly in that folder (not skilltrim/skilltrim). Copies the
bundled CLI (scripts/skilltrim.py, src/skilltrim), pyproject.toml, README.md,
LICENSE, and the linked reference benchmarks/README.md. Does not copy .git,
.venv, or benchmark corpora.

--host   grok | grok-bot | cursor | openai | antigravity | claude | all
         (default: all)
--scope  user | project
         (default: user)

User scope writes under $HOME. Project scope writes under the current directory.
Grok Bot also prints a paste-in prompt. This script does not prove an agent
discovered or followed the skill.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      [[ $# -ge 2 ]] || { echo "skilltrim: --host requires a value" >&2; exit 2; }
      HOST=$2
      shift 2
      ;;
    --host=*)
      HOST=${1#--host=}
      shift
      ;;
    --scope)
      [[ $# -ge 2 ]] || { echo "skilltrim: --scope requires a value" >&2; exit 2; }
      SCOPE=$2
      shift 2
      ;;
    --scope=*)
      SCOPE=${1#--scope=}
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "skilltrim: unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

case "$HOST" in
  grok|grok-bot|cursor|openai|antigravity|claude|all) ;;
  *)
    echo "skilltrim: unknown host '$HOST'" >&2
    exit 2
    ;;
esac

case "$SCOPE" in
  user|project) ;;
  *)
    echo "skilltrim: unknown scope '$SCOPE'" >&2
    exit 2
    ;;
esac

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)

require_metadata() {
  local skill=$1
  local name desc
  # No pipeline: pipefail plus head/sed SIGPIPE would abort on bash -e.
  name=$(awk '
    /^---[[:space:]]*$/ { c++; next }
    c == 1 && /^name:/ {
      sub(/^name:[[:space:]]*/, "")
      sub(/\r$/, "")
      sub(/[[:space:]]+$/, "")
      print
      exit
    }
  ' "$skill")
  desc=$(awk '
    /^---[[:space:]]*$/ { c++; next }
    c == 1 && /^description:/ {
      sub(/^description:[[:space:]]*/, "")
      sub(/\r$/, "")
      sub(/[[:space:]]+$/, "")
      print
      exit
    }
  ' "$skill")
  if [[ "$name" != "skilltrim" ]]; then
    echo "skilltrim: SKILL.md name must match folder skilltrim (found '${name:-<missing>}')" >&2
    exit 2
  fi
  if [[ -z "$desc" ]]; then
    echo "skilltrim: description is required in SKILL.md frontmatter" >&2
    exit 2
  fi
}

require_metadata "$ROOT/SKILL.md"

assert_installed() {
  local dest=$1
  [[ -f "$dest/SKILL.md" ]] || { echo "skilltrim: missing SKILL.md in $dest" >&2; exit 1; }
  [[ ! -e "$dest/skilltrim" ]] || { echo "skilltrim: double-nested skill folder: $dest/skilltrim" >&2; exit 1; }
  [[ ! -e "$dest/.git" && ! -e "$dest/.venv" ]] || { echo "skilltrim: copied .git or .venv into $dest" >&2; exit 1; }
  [[ ! -e "$dest/benchmarks/fixtures" && ! -e "$dest/benchmarks/real-results.json" && ! -e "$dest/benchmarks/real-example.json" && ! -e "$dest/benchmarks/baseline.json" ]] || {
    echo "skilltrim: copied benchmark corpora into $dest" >&2
    exit 1
  }
  [[ -f "$dest/benchmarks/README.md" ]] || { echo "skilltrim: missing linked reference benchmarks/README.md in $dest" >&2; exit 1; }
  [[ -f "$dest/scripts/skilltrim.py" && -f "$dest/src/skilltrim/cli.py" && -f "$dest/src/skilltrim/__init__.py" && -f "$dest/pyproject.toml" ]] || {
    echo "skilltrim: missing bundled CLI files in $dest" >&2
    exit 1
  }
}

copy_skill() {
  local dest=$1
  case "$dest" in
    */skilltrim) ;;
    *)
      echo "skilltrim: refusing destination that is not a skilltrim folder: $dest" >&2
      exit 2
      ;;
  esac
  if [[ -L "$dest" ]]; then
    rm -f -- "$dest"
  elif [[ -d "$dest" ]]; then
    rm -rf -- "$dest"
  elif [[ -e "$dest" ]]; then
    echo "skilltrim: destination exists and is not a directory: $dest" >&2
    exit 2
  fi
  mkdir -p -- "$dest/benchmarks" "$dest/scripts" "$dest/src/skilltrim"
  cp -- "$ROOT/SKILL.md" "$dest/SKILL.md"
  cp -- "$ROOT/README.md" "$dest/README.md"
  cp -- "$ROOT/LICENSE" "$dest/LICENSE"
  cp -- "$ROOT/pyproject.toml" "$dest/pyproject.toml"
  cp -- "$ROOT/benchmarks/README.md" "$dest/benchmarks/README.md"
  cp -- "$ROOT/scripts/skilltrim.py" "$dest/scripts/skilltrim.py"
  cp -- "$ROOT/src/skilltrim/"*.py "$dest/src/skilltrim/"
  assert_installed "$dest"
  printf 'Installed %s\n' "$dest"
}

dests=()
add_dest() {
  local candidate=$1
  local existing
  if [[ ${#dests[@]} -gt 0 ]]; then
    for existing in "${dests[@]}"; do
      if [[ "$existing" == "$candidate" ]]; then
        return
      fi
    done
  fi
  dests+=("$candidate")
}

if [[ "$SCOPE" == "user" ]]; then
  if [[ -z "${HOME:-}" ]]; then
    echo "skilltrim: HOME is not set" >&2
    exit 2
  fi
  BASE=${HOME%/}
else
  BASE=$(pwd -P)
fi

case "$HOST" in
  grok|grok-bot)
    add_dest "$BASE/.grok/skills/skilltrim"
    ;;
  cursor)
    add_dest "$BASE/.cursor/skills/skilltrim"
    ;;
  openai)
    add_dest "$BASE/.agents/skills/skilltrim"
    ;;
  antigravity)
    if [[ "$SCOPE" == "project" ]]; then
      add_dest "$BASE/.agents/skills/skilltrim"
    else
      add_dest "$BASE/.gemini/config/skills/skilltrim"
      add_dest "$BASE/.gemini/antigravity-cli/skills/skilltrim"
    fi
    ;;
  claude)
    add_dest "$BASE/.claude/skills/skilltrim"
    ;;
  all)
    add_dest "$BASE/.grok/skills/skilltrim"
    add_dest "$BASE/.cursor/skills/skilltrim"
    if [[ "$SCOPE" == "project" ]]; then
      add_dest "$BASE/.agents/skills/skilltrim"
    else
      add_dest "$BASE/.agents/skills/skilltrim"
      add_dest "$BASE/.gemini/config/skills/skilltrim"
      add_dest "$BASE/.gemini/antigravity-cli/skills/skilltrim"
    fi
    add_dest "$BASE/.claude/skills/skilltrim"
    ;;
esac

for dest in "${dests[@]}"; do
  copy_skill "$dest"
done

if [[ "$SCOPE" == "user" ]]; then
  echo "Scope: user. Project paths were not changed. Re-run with --scope project to install .grok, .cursor, .agents, and .claude under the current directory."
else
  echo "Scope: project. Home skill directories were not changed. Antigravity's user paths are ~/.gemini/config/skills/skilltrim and ~/.gemini/antigravity-cli/skills/skilltrim."
fi

case "$HOST" in
  grok|all) echo "Grok: invoke /skilltrim" ;;
esac
case "$HOST" in
  grok-bot|all)
    cat <<'EOF'
Grok Bot paste-in prompt:
Clone https://github.com/JayCommit/skilltrim and copy its agent skill into ~/.grok/skills/skilltrim/ on the bot computer. Copy SKILL.md plus the files that skill uses (bundled scripts/skilltrim.py, src/skilltrim, and linked references such as benchmarks/README.md). Do not copy .git, .venv, or benchmark corpora. Do not nest another skilltrim directory inside the destination; SKILL.md must sit directly at ~/.grok/skills/skilltrim/SKILL.md. Use the same SKILL.md from that repository. Invoke /skilltrim.
EOF
    ;;
esac
case "$HOST" in
  cursor|all) echo "Cursor: folder name matches skill name skilltrim. Invoke /skilltrim" ;;
esac
case "$HOST" in
  openai|all)
    echo "OpenAI / ChatGPT app: zip the skilltrim folder (SKILL.md directly inside it). Plugins → Skills → Add → Upload. Codex: \$skilltrim"
    ;;
esac
case "$HOST" in
  antigravity|all) echo "Antigravity: description is required in SKILL.md. Project path is one level at .agents/skills/skilltrim. Invoke /skilltrim" ;;
esac
case "$HOST" in
  claude|all) echo "Claude: invoke /skilltrim" ;;
esac
