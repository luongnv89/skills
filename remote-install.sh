#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# skills Remote Installer
# Install agent skills from anywhere with a single command:
#   curl -sSL https://raw.githubusercontent.com/luongnv89/skills/main/remote-install.sh | bash
# Or with wget:
#   wget -qO- https://raw.githubusercontent.com/luongnv89/skills/main/remote-install.sh | bash
#
# Non-interactive mode (skip menus):
#   curl -sSL ... | bash -s -- --skills "code-review,auto-push" --tools "Claude Code" --scope global
#   curl -sSL ... | bash -s -- --all --tools "Claude Code,Cursor" --scope project
# ============================================================================

REPO_OWNER="luongnv89"
REPO_NAME="skills"
DEFAULT_BRANCH="main"
TARBALL_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/${DEFAULT_BRANCH}.tar.gz"

# ─── ANSI colors (with dumb-terminal fallback) ─────────────────────────────
if [[ "${TERM:-dumb}" != "dumb" ]] && command -v tput &>/dev/null && tput colors &>/dev/null; then
  BOLD=$(tput bold)    DIM=$(tput dim)      RESET=$(tput sgr0)
  GREEN=$(tput setaf 2) CYAN=$(tput setaf 6) YELLOW=$(tput setaf 3) RED=$(tput setaf 1)
else
  BOLD="" DIM="" RESET="" GREEN="" CYAN="" YELLOW="" RED=""
fi

# ─── Restore terminal on unexpected exit ────────────────────────────────────
cleanup() {
  stty echo icanon 2>/dev/null || true
  tput cnorm 2>/dev/null || true
  # Remove temp directory if it exists
  if [[ -n "${TMPDIR_CREATED:-}" && -d "${TMPDIR_CREATED}" ]]; then
    rm -rf "${TMPDIR_CREATED}"
  fi
}
trap cleanup EXIT

# ─── Globals ────────────────────────────────────────────────────────────────
SKILLS_SRC_DIR=""       # path to extracted skills/ folder
OS=""
SKILLS=()               # discovered skill folder names
SKILL_DESCS=()          # one-line descriptions (from frontmatter)
SKILL_SEL=()            # 1/0 toggle per skill
TOOLS=("Claude Code" "Cursor" "Windsurf" "GitHub Copilot" "OpenAI Codex" "OpenCode" "Google Antigravity")
TOOL_SEL=()             # 1/0 toggle per tool
INSTALL_SCOPE=""        # "global" or "project"
INSTALLED=()            # log: "skill|tool|path"
INSTALL_ALL_TOOLS=0     # 1 if "Install All" was toggled for tools
TMPDIR_CREATED=""

# ─── CLI argument parsing (for non-interactive mode) ────────────────────────
ARG_SKILLS=""           # comma-separated skill names, or empty
ARG_ALL_SKILLS=0        # 1 if --all was passed
ARG_TOOLS=""            # comma-separated tool names, or empty
ARG_SCOPE=""            # global|project, or empty
NON_INTERACTIVE=0

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --skills)
        ARG_SKILLS="$2"
        NON_INTERACTIVE=1
        shift 2
        ;;
      --all)
        ARG_ALL_SKILLS=1
        NON_INTERACTIVE=1
        shift
        ;;
      --tools)
        ARG_TOOLS="$2"
        NON_INTERACTIVE=1
        shift 2
        ;;
      --scope)
        ARG_SCOPE="$2"
        NON_INTERACTIVE=1
        shift 2
        ;;
      --help|-h)
        show_help
        exit 0
        ;;
      --list)
        LIST_ONLY=1
        shift
        ;;
      *)
        echo "${RED}Unknown option: $1${RESET}" >&2
        echo "Use --help for usage information." >&2
        exit 1
        ;;
    esac
  done
}

show_help() {
  cat <<'HELPEOF'
skills Remote Installer

Usage:
  curl -sSL https://raw.githubusercontent.com/luongnv89/skills/main/remote-install.sh | bash
  curl -sSL ... | bash -s -- [OPTIONS]

Options:
  --skills <list>   Comma-separated skill names to install (e.g. "code-review,auto-push")
  --all             Install all available skills
  --tools <list>    Comma-separated tool names, or "all" for all tools
                    (e.g. "Claude Code,Cursor" or "all")
                    Available: Claude Code, Cursor, Windsurf, GitHub Copilot,
                               OpenAI Codex, OpenCode, Google Antigravity
                    When "all": skills stored in .agents/skills/, Claude Code gets symlinks
  --scope <scope>   Installation scope: "global" or "project"
  --list            List available skills and exit
  --help, -h        Show this help message

Interactive mode (default):
  If no --skills/--all and --tools flags are given, the installer launches an
  interactive TUI where you can select skills, tools, and scope.

Examples:
  # Interactive mode
  curl -sSL https://raw.githubusercontent.com/luongnv89/skills/main/remote-install.sh | bash

  # Install specific skills for Claude Code globally
  curl -sSL ... | bash -s -- --skills "code-review,auto-push" --tools "Claude Code" --scope global

  # Install all skills for multiple tools in current project
  curl -sSL ... | bash -s -- --all --tools "Claude Code,Cursor" --scope project

  # Install all skills for all tools globally (shared install with symlinks)
  curl -sSL ... | bash -s -- --all --tools all --scope global

  # List available skills
  curl -sSL ... | bash -s -- --list
HELPEOF
}

# ─── OS detection ───────────────────────────────────────────────────────────
detect_os() {
  case "$(uname -s)" in
    Darwin*)  OS="macOS" ;;
    Linux*)
      if grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
        OS="WSL"
      else
        OS="Linux"
      fi ;;
    CYGWIN*|MINGW*|MSYS*) OS="Windows" ;;
    *) OS="Unknown" ;;
  esac
}

# ─── Download and extract skills ───────────────────────────────────────────
download_skills() {
  TMPDIR_CREATED="$(mktemp -d)"
  local tarball="${TMPDIR_CREATED}/skills.tar.gz"

  echo "  ${DIM}Downloading skills from GitHub...${RESET}"

  if command -v curl &>/dev/null; then
    curl -sSL "$TARBALL_URL" -o "$tarball"
  elif command -v wget &>/dev/null; then
    wget -qO "$tarball" "$TARBALL_URL"
  else
    echo "${RED}Error: Neither curl nor wget found. Please install one of them.${RESET}" >&2
    exit 1
  fi

  echo "  ${DIM}Extracting...${RESET}"
  tar -xzf "$tarball" -C "$TMPDIR_CREATED"

  # The tarball extracts to <repo>-<branch>/ (e.g. skills-main/)
  SKILLS_SRC_DIR="${TMPDIR_CREATED}/${REPO_NAME}-${DEFAULT_BRANCH}/skills"

  if [[ ! -d "$SKILLS_SRC_DIR" ]]; then
    echo "${RED}Error: Could not find skills directory in downloaded archive.${RESET}" >&2
    exit 1
  fi

  echo "  ${GREEN}✔${RESET} Skills downloaded successfully"
  echo ""
}

# ─── Discover skills (folders containing SKILL.md) ─────────────────────────
discover_skills() {
  local dir desc
  for dir in "$SKILLS_SRC_DIR"/*/; do
    [[ -f "$dir/SKILL.md" ]] || continue
    local name
    name="$(basename "$dir")"
    # Extract description from YAML frontmatter
    desc=$(awk '/^---$/{n++; next} n==1 && /^description:/{sub(/^description: *"?/, ""); sub(/"$/, ""); print; exit}' "$dir/SKILL.md")
    # Truncate long descriptions for display
    if [[ ${#desc} -gt 70 ]]; then
      desc="${desc:0:67}..."
    fi
    SKILLS+=("$name")
    SKILL_DESCS+=("$desc")
    SKILL_SEL+=(0)
  done

  if [[ ${#SKILLS[@]} -eq 0 ]]; then
    echo "${RED}No skills found in the downloaded archive.${RESET}"
    exit 1
  fi
}

# ─── List available skills ─────────────────────────────────────────────────
list_skills() {
  echo ""
  echo "${BOLD}${CYAN}Available skills (${#SKILLS[@]}):${RESET}"
  echo ""
  local i
  for (( i = 0; i < ${#SKILLS[@]}; i++ )); do
    printf "  ${GREEN}•${RESET} ${BOLD}%-30s${RESET} %s\n" "${SKILLS[$i]}" "${SKILL_DESCS[$i]}"
  done
  echo ""
}

# ─── Interactive checkbox list (Bash 3.2 compatible) ────────────────────────
checkbox_select() {
  local title="$1"
  local items_name=$2
  local descs_name=$3
  local sel_name=$4

  eval "local count=\${#${items_name}[@]}"
  local cursor=0

  tput civis 2>/dev/null || true
  stty -echo -icanon min 1 time 0 2>/dev/null || true

  while true; do
    printf "\033[2J\033[H"
    echo "${BOLD}${CYAN}$title${RESET}"
    echo "${DIM}  ↑/↓ Navigate   Space Toggle   Enter Confirm${RESET}"
    echo ""

    local i
    for (( i = 0; i < count; i++ )); do
      local marker="  "
      eval "local sel_val=\${${sel_name}[$i]}"
      eval "local item_val=\"\${${items_name}[$i]}\""
      eval "local desc_val=\"\${${descs_name}[$i]:-}\""
      [[ "$sel_val" -eq 1 ]] && marker="${GREEN}✔${RESET} "
      if [[ $i -eq $cursor ]]; then
        printf " ${BOLD}▸ %s %-25s${RESET} ${DIM}%s${RESET}\n" "$marker" "$item_val" "$desc_val"
      else
        printf "   %s %-25s ${DIM}%s${RESET}\n" "$marker" "$item_val" "$desc_val"
      fi
    done

    local key
    key=$(dd bs=1 count=1 2>/dev/null) || true
    if [[ "$key" == $'\x1b' ]]; then
      local seq
      seq=$(dd bs=1 count=2 2>/dev/null) || true
      case "$seq" in
        '[A') [[ $cursor -gt 0 ]] && (( cursor-- )) || true ;;
        '[B') [[ $cursor -lt $((count - 1)) ]] && (( cursor++ )) || true ;;
      esac
    elif [[ "$key" == " " ]]; then
      eval "local cur_val=\${${sel_name}[$cursor]}"
      if [[ "$cur_val" -eq 0 ]]; then
        eval "${sel_name}[$cursor]=1"
      else
        eval "${sel_name}[$cursor]=0"
      fi
    elif [[ "$key" == "" ]]; then
      break
    fi
  done

  stty echo icanon 2>/dev/null || true
  tput cnorm 2>/dev/null || true
}

# ─── Interactive single-choice selector ──────────────────────────────────────
radio_select() {
  local title="$1"
  local items_name=$2
  local descs_name=$3
  local result_name=$4

  eval "local count=\${#${items_name}[@]}"
  local cursor=0

  tput civis 2>/dev/null || true
  stty -echo -icanon min 1 time 0 2>/dev/null || true

  while true; do
    printf "\033[2J\033[H"
    echo "${BOLD}${CYAN}$title${RESET}"
    echo "${DIM}  ↑/↓ Navigate   Enter Select${RESET}"
    echo ""

    local i
    for (( i = 0; i < count; i++ )); do
      eval "local item_val=\"\${${items_name}[$i]}\""
      eval "local desc_val=\"\${${descs_name}[$i]:-}\""
      local marker="  "
      [[ $i -eq $cursor ]] && marker="${GREEN}●${RESET} "
      if [[ $i -eq $cursor ]]; then
        printf " ${BOLD}▸ %s %-25s${RESET} ${DIM}%s${RESET}\n" "$marker" "$item_val" "$desc_val"
      else
        printf "   %s %-25s ${DIM}%s${RESET}\n" "$marker" "$item_val" "$desc_val"
      fi
    done

    local key
    key=$(dd bs=1 count=1 2>/dev/null) || true
    if [[ "$key" == $'\x1b' ]]; then
      local seq
      seq=$(dd bs=1 count=2 2>/dev/null) || true
      case "$seq" in
        '[A') [[ $cursor -gt 0 ]] && (( cursor-- )) || true ;;
        '[B') [[ $cursor -lt $((count - 1)) ]] && (( cursor++ )) || true ;;
      esac
    elif [[ "$key" == "" ]]; then
      break
    fi
  done

  stty echo icanon 2>/dev/null || true
  tput cnorm 2>/dev/null || true

  eval "${result_name}=${cursor}"
}

# ─── Strip YAML frontmatter from SKILL.md ──────────────────────────────────
strip_frontmatter() {
  local file="$1"
  awk 'BEGIN{n=0} /^---$/{n++; next} n>=2{print}' "$file"
}

# ─── Install one skill for one tool ────────────────────────────────────────
install_skill_for_tool() {
  local skill="$1" tool="$2"
  local src="$SKILLS_SRC_DIR/$skill"
  local skill_dir dest_file

  case "$tool" in
    "Claude Code")
      if [[ "$INSTALL_SCOPE" == "global" ]]; then
        skill_dir="$HOME/.claude/skills/$skill"
      else
        skill_dir=".claude/skills/$skill"
      fi
      mkdir -p "$skill_dir"
      cp -r "$src"/* "$skill_dir"/
      INSTALLED+=("${skill}|${tool}|${skill_dir}/")
      ;;

    "Cursor")
      if [[ "$INSTALL_SCOPE" == "global" ]]; then
        skill_dir="$HOME/.agents/skills/$skill"
      else
        skill_dir=".agents/skills/$skill"
      fi
      mkdir -p "$skill_dir"
      cp -r "$src"/* "$skill_dir"/
      mkdir -p .cursor/rules
      dest_file=".cursor/rules/${skill}.mdc"
      strip_frontmatter "$src/SKILL.md" > "$dest_file"
      INSTALLED+=("${skill}|${tool}|${skill_dir}/ + ${dest_file}")
      ;;

    "Windsurf")
      if [[ "$INSTALL_SCOPE" == "global" ]]; then
        skill_dir="$HOME/.agents/skills/$skill"
      else
        skill_dir=".agents/skills/$skill"
      fi
      mkdir -p "$skill_dir"
      cp -r "$src"/* "$skill_dir"/
      mkdir -p .windsurf/rules
      dest_file=".windsurf/rules/${skill}.md"
      strip_frontmatter "$src/SKILL.md" > "$dest_file"
      INSTALLED+=("${skill}|${tool}|${skill_dir}/ + ${dest_file}")
      ;;

    "GitHub Copilot")
      if [[ "$INSTALL_SCOPE" == "global" ]]; then
        skill_dir="$HOME/.agents/skills/$skill"
      else
        skill_dir=".agents/skills/$skill"
      fi
      mkdir -p "$skill_dir"
      cp -r "$src"/* "$skill_dir"/
      mkdir -p .github/instructions
      dest_file=".github/instructions/${skill}.instructions.md"
      strip_frontmatter "$src/SKILL.md" > "$dest_file"
      INSTALLED+=("${skill}|${tool}|${skill_dir}/ + ${dest_file}")
      ;;

    "OpenAI Codex")
      if [[ "$INSTALL_SCOPE" == "global" ]]; then
        skill_dir="$HOME/.agents/skills/$skill"
        mkdir -p "$skill_dir"
        cp -r "$src"/* "$skill_dir"/
        mkdir -p "$HOME/.codex"
        dest_file="$HOME/.codex/AGENTS.md"
      else
        skill_dir=".agents/skills/$skill"
        mkdir -p "$skill_dir"
        cp -r "$src"/* "$skill_dir"/
        dest_file="AGENTS.md"
      fi
      {
        echo ""
        echo "<!-- skills: $skill -->"
        strip_frontmatter "$src/SKILL.md"
        echo "<!-- /skills: $skill -->"
      } >> "$dest_file"
      INSTALLED+=("${skill}|${tool}|${skill_dir}/ + ${dest_file}")
      ;;

    "OpenCode")
      if [[ "$INSTALL_SCOPE" == "global" ]]; then
        skill_dir="$HOME/.agents/skills/$skill"
      else
        skill_dir=".agents/skills/$skill"
      fi
      mkdir -p "$skill_dir"
      cp -r "$src"/* "$skill_dir"/
      INSTALLED+=("${skill}|${tool}|${skill_dir}/")
      ;;

    "Google Antigravity")
      if [[ "$INSTALL_SCOPE" == "global" ]]; then
        skill_dir="$HOME/.agents/skills/$skill"
      else
        skill_dir=".agents/skills/$skill"
      fi
      mkdir -p "$skill_dir"
      cp -r "$src"/* "$skill_dir"/
      INSTALLED+=("${skill}|${tool}|${skill_dir}/")
      ;;
  esac
}

# ─── Install one skill for ALL tools (shared .agents/skills + symlink) ────
install_skill_all_tools() {
  local skill="$1"
  local src="$SKILLS_SRC_DIR/$skill"
  local shared_dir dest_file

  # Step 1: Copy skill files to the shared canonical location (.agents/skills/)
  if [[ "$INSTALL_SCOPE" == "global" ]]; then
    shared_dir="$HOME/.agents/skills/$skill"
  else
    shared_dir=".agents/skills/$skill"
  fi
  mkdir -p "$shared_dir"
  cp -r "$src"/* "$shared_dir"/

  # Step 2: Create symlink for Claude Code
  local claude_dir
  if [[ "$INSTALL_SCOPE" == "global" ]]; then
    claude_dir="$HOME/.claude/skills/$skill"
    mkdir -p "$(dirname "$claude_dir")"
    rm -rf "$claude_dir"
    ln -s "$shared_dir" "$claude_dir"
  else
    claude_dir=".claude/skills/$skill"
    mkdir -p "$(dirname "$claude_dir")"
    rm -rf "$claude_dir"
    ln -s "../../.agents/skills/$skill" "$claude_dir"
  fi
  INSTALLED+=("${skill}|Claude Code|${claude_dir}/ → ${shared_dir}/ (symlink)")

  # Step 3: Cursor rule file
  mkdir -p .cursor/rules
  dest_file=".cursor/rules/${skill}.mdc"
  strip_frontmatter "$src/SKILL.md" > "$dest_file"
  INSTALLED+=("${skill}|Cursor|${shared_dir}/ + ${dest_file}")

  # Step 4: Windsurf rule file
  mkdir -p .windsurf/rules
  dest_file=".windsurf/rules/${skill}.md"
  strip_frontmatter "$src/SKILL.md" > "$dest_file"
  INSTALLED+=("${skill}|Windsurf|${shared_dir}/ + ${dest_file}")

  # Step 5: GitHub Copilot instructions file
  mkdir -p .github/instructions
  dest_file=".github/instructions/${skill}.instructions.md"
  strip_frontmatter "$src/SKILL.md" > "$dest_file"
  INSTALLED+=("${skill}|GitHub Copilot|${shared_dir}/ + ${dest_file}")

  # Step 6: OpenAI Codex AGENTS.md entry
  if [[ "$INSTALL_SCOPE" == "global" ]]; then
    mkdir -p "$HOME/.codex"
    dest_file="$HOME/.codex/AGENTS.md"
  else
    dest_file="AGENTS.md"
  fi
  {
    echo ""
    echo "<!-- skills: $skill -->"
    strip_frontmatter "$src/SKILL.md"
    echo "<!-- /skills: $skill -->"
  } >> "$dest_file"
  INSTALLED+=("${skill}|OpenAI Codex|${shared_dir}/ + ${dest_file}")

  # Step 7: OpenCode (uses .agents/skills/ directly)
  INSTALLED+=("${skill}|OpenCode|${shared_dir}/")

  # Step 8: Google Antigravity (uses .agents/skills/ directly)
  INSTALLED+=("${skill}|Google Antigravity|${shared_dir}/")
}

# ─── Print summary table ───────────────────────────────────────────────────
print_summary() {
  if [[ ${#INSTALLED[@]} -eq 0 ]]; then
    echo "${YELLOW}Nothing was installed.${RESET}"
    return
  fi

  echo ""
  echo "${BOLD}${GREEN}Installation Summary${RESET}"
  echo ""
  printf "  ${BOLD}%-25s %-20s %s${RESET}\n" "Skill" "Tool" "Path"
  printf "  %-25s %-20s %s\n" "─────────────────────────" "────────────────────" "──────────────────────────────"

  local entry
  for entry in "${INSTALLED[@]}"; do
    IFS='|' read -r s t p <<< "$entry"
    printf "  %-25s %-20s %s\n" "$s" "$t" "$p"
  done
  echo ""
}

# ─── Non-interactive skill/tool resolution ─────────────────────────────────
resolve_non_interactive() {
  # Resolve skills
  if [[ $ARG_ALL_SKILLS -eq 1 ]]; then
    for (( i = 0; i < ${#SKILLS[@]}; i++ )); do
      SKILL_SEL[$i]=1
    done
  elif [[ -n "$ARG_SKILLS" ]]; then
    IFS=',' read -ra REQUESTED_SKILLS <<< "$ARG_SKILLS"
    for req in "${REQUESTED_SKILLS[@]}"; do
      req="$(echo "$req" | xargs)"  # trim whitespace
      local found=0
      for (( i = 0; i < ${#SKILLS[@]}; i++ )); do
        if [[ "${SKILLS[$i]}" == "$req" ]]; then
          SKILL_SEL[$i]=1
          found=1
          break
        fi
      done
      if [[ $found -eq 0 ]]; then
        echo "${YELLOW}Warning: Skill '$req' not found, skipping.${RESET}"
      fi
    done
  else
    echo "${RED}Error: In non-interactive mode, specify --skills or --all.${RESET}" >&2
    exit 1
  fi

  # Resolve tools
  if [[ -z "$ARG_TOOLS" ]]; then
    echo "${RED}Error: In non-interactive mode, specify --tools.${RESET}" >&2
    exit 1
  fi
  if [[ "$ARG_TOOLS" == "all" ]]; then
    INSTALL_ALL_TOOLS=1
    for (( j = 0; j < ${#TOOLS[@]}; j++ )); do
      TOOL_SEL[$j]=1
    done
  else
    IFS=',' read -ra REQUESTED_TOOLS <<< "$ARG_TOOLS"
    for req in "${REQUESTED_TOOLS[@]}"; do
      req="$(echo "$req" | xargs)"  # trim whitespace
      local found=0
      for (( j = 0; j < ${#TOOLS[@]}; j++ )); do
        if [[ "${TOOLS[$j]}" == "$req" ]]; then
          TOOL_SEL[$j]=1
          found=1
          break
        fi
      done
      if [[ $found -eq 0 ]]; then
        echo "${YELLOW}Warning: Tool '$req' not recognized, skipping.${RESET}"
      fi
    done
  fi

  # Resolve scope
  if [[ -z "$ARG_SCOPE" ]]; then
    INSTALL_SCOPE="global"
    echo "${DIM}  No --scope specified, defaulting to 'global'.${RESET}"
  elif [[ "$ARG_SCOPE" == "global" || "$ARG_SCOPE" == "project" ]]; then
    INSTALL_SCOPE="$ARG_SCOPE"
  else
    echo "${RED}Error: --scope must be 'global' or 'project', got '$ARG_SCOPE'.${RESET}" >&2
    exit 1
  fi

  # Validate at least one skill and tool selected
  local any_skill=0 any_tool=0
  for s in "${SKILL_SEL[@]}"; do [[ $s -eq 1 ]] && any_skill=1 && break; done
  for t in "${TOOL_SEL[@]}"; do [[ $t -eq 1 ]] && any_tool=1 && break; done

  if [[ $any_skill -eq 0 ]]; then
    echo "${RED}Error: No valid skills selected.${RESET}" >&2
    exit 1
  fi
  if [[ $any_tool -eq 0 ]]; then
    echo "${RED}Error: No valid tools selected.${RESET}" >&2
    exit 1
  fi
}

# ─── Main ───────────────────────────────────────────────────────────────────
main() {
  local LIST_ONLY=0
  parse_args "$@"

  detect_os

  echo ""
  echo "${BOLD}${CYAN}"
  echo "  ┌─────────────────────────────────────┐"
  echo "  │      skills remote installer         │"
  echo "  └─────────────────────────────────────┘${RESET}"
  echo ""
  echo "  OS detected: ${BOLD}${OS}${RESET}"
  echo ""

  # Download and extract skills from GitHub
  download_skills

  # Discover available skills
  discover_skills

  # Handle --list
  if [[ $LIST_ONLY -eq 1 ]]; then
    list_skills
    exit 0
  fi

  # Initialise tool selection array
  for (( i = 0; i < ${#TOOLS[@]}; i++ )); do
    TOOL_SEL+=(0)
  done

  if [[ $NON_INTERACTIVE -eq 1 ]]; then
    # ── Non-interactive mode ──
    resolve_non_interactive

    echo "${BOLD}${CYAN}Installing (${INSTALL_SCOPE})...${RESET}"
    echo ""

    local i j
    for (( i = 0; i < ${#SKILLS[@]}; i++ )); do
      [[ ${SKILL_SEL[$i]} -eq 0 ]] && continue
      if [[ $INSTALL_ALL_TOOLS -eq 1 ]]; then
        echo "  ${GREEN}✔${RESET} ${BOLD}${SKILLS[$i]}${RESET} → All tools (shared + symlinks)"
        install_skill_all_tools "${SKILLS[$i]}"
      else
        for (( j = 0; j < ${#TOOLS[@]}; j++ )); do
          [[ ${TOOL_SEL[$j]} -eq 0 ]] && continue
          echo "  ${GREEN}✔${RESET} ${BOLD}${SKILLS[$i]}${RESET} → ${TOOLS[$j]}"
          install_skill_for_tool "${SKILLS[$i]}" "${TOOLS[$j]}"
        done
      fi
    done

    print_summary
    echo "${GREEN}Done!${RESET}"

  else
    # ── Interactive mode ──

    # Tool descriptions for display
    local TOOL_DESCS=()
    TOOL_DESCS+=("~/.claude/skills/")
    TOOL_DESCS+=("~/.agents/skills/ + .cursor/rules/")
    TOOL_DESCS+=("~/.agents/skills/ + .windsurf/rules/")
    TOOL_DESCS+=("~/.agents/skills/ + .github/instructions/")
    TOOL_DESCS+=("~/.agents/skills/ + ~/.codex/AGENTS.md")
    TOOL_DESCS+=("~/.agents/skills/")
    TOOL_DESCS+=("~/.agents/skills/")

    # ── Step 1: Select skills ──
    local ALL_SKILLS=("Install All" "${SKILLS[@]}")
    local ALL_SKILL_DESCS=("Select/deselect all skills at once" "${SKILL_DESCS[@]}")
    local ALL_SKILL_SEL=(0)
    for (( i = 0; i < ${#SKILLS[@]}; i++ )); do
      ALL_SKILL_SEL+=(0)
    done

    checkbox_select "Select skills to install:" ALL_SKILLS ALL_SKILL_DESCS ALL_SKILL_SEL

    # If "Install All" was toggled on, select every skill
    if [[ ${ALL_SKILL_SEL[0]} -eq 1 ]]; then
      for (( i = 0; i < ${#SKILLS[@]}; i++ )); do
        SKILL_SEL[$i]=1
      done
    else
      for (( i = 0; i < ${#SKILLS[@]}; i++ )); do
        SKILL_SEL[$i]=${ALL_SKILL_SEL[$((i + 1))]}
      done
    fi

    local any_skill=0
    for s in "${SKILL_SEL[@]}"; do [[ $s -eq 1 ]] && any_skill=1 && break; done
    if [[ $any_skill -eq 0 ]]; then
      printf "\033[2J\033[H"
      echo "${YELLOW}No skills selected — exiting.${RESET}"
      exit 0
    fi

    # ── Step 2: Select tools ──
    # Prepend "Install All" option for tools
    local ALL_TOOLS=("Install All" "${TOOLS[@]}")
    local ALL_TOOL_DESCS=("Select all tools (shared .agents/skills/ + symlinks)" "${TOOL_DESCS[@]}")
    local ALL_TOOL_SEL=(0)
    for (( i = 0; i < ${#TOOLS[@]}; i++ )); do
      ALL_TOOL_SEL+=(0)
    done

    checkbox_select "Select target tools:" ALL_TOOLS ALL_TOOL_DESCS ALL_TOOL_SEL

    # If "Install All" was toggled on, select every tool and set flag
    if [[ ${ALL_TOOL_SEL[0]} -eq 1 ]]; then
      INSTALL_ALL_TOOLS=1
      for (( i = 0; i < ${#TOOLS[@]}; i++ )); do
        TOOL_SEL[$i]=1
      done
    else
      # Copy individual selections back (skip index 0 which is "Install All")
      for (( i = 0; i < ${#TOOLS[@]}; i++ )); do
        TOOL_SEL[$i]=${ALL_TOOL_SEL[$((i + 1))]}
      done
    fi

    local any_tool=0
    for t in "${TOOL_SEL[@]}"; do [[ $t -eq 1 ]] && any_tool=1 && break; done
    if [[ $any_tool -eq 0 ]]; then
      printf "\033[2J\033[H"
      echo "${YELLOW}No tools selected — exiting.${RESET}"
      exit 0
    fi

    # ── Step 3: Select installation scope ──
    local SCOPE_ITEMS=("Global" "Project")
    local SCOPE_DESCS=("Install to ~/  (available in all projects)" "Install to ./  (current project only)")
    local SCOPE_CHOICE=0

    radio_select "Install scope:" SCOPE_ITEMS SCOPE_DESCS SCOPE_CHOICE

    if [[ $SCOPE_CHOICE -eq 0 ]]; then
      INSTALL_SCOPE="global"
    else
      INSTALL_SCOPE="project"
    fi

    # ── Step 4: Install ──
    printf "\033[2J\033[H"
    echo "${BOLD}${CYAN}Installing (${INSTALL_SCOPE})...${RESET}"
    echo ""

    local i j
    for (( i = 0; i < ${#SKILLS[@]}; i++ )); do
      [[ ${SKILL_SEL[$i]} -eq 0 ]] && continue
      if [[ $INSTALL_ALL_TOOLS -eq 1 ]]; then
        echo "  ${GREEN}✔${RESET} ${BOLD}${SKILLS[$i]}${RESET} → All tools (shared + symlinks)"
        install_skill_all_tools "${SKILLS[$i]}"
      else
        for (( j = 0; j < ${#TOOLS[@]}; j++ )); do
          [[ ${TOOL_SEL[$j]} -eq 0 ]] && continue
          echo "  ${GREEN}✔${RESET} ${BOLD}${SKILLS[$i]}${RESET} → ${TOOLS[$j]}"
          install_skill_for_tool "${SKILLS[$i]}" "${TOOLS[$j]}"
        done
      fi
    done

    # ── Step 5: Summary ──
    print_summary
    echo "${GREEN}Done!${RESET}"
  fi
}

main "$@"
