#!/usr/bin/env bash
set -euo pipefail

# ─── ANSI colors (with dumb-terminal fallback) ─────────────────────────────
if [[ "${TERM:-dumb}" != "dumb" ]] && command -v tput &>/dev/null && tput colors &>/dev/null; then
  BOLD=$(tput bold)    DIM=$(tput dim)      RESET=$(tput sgr0)
  GREEN=$(tput setaf 2) CYAN=$(tput setaf 6) YELLOW=$(tput setaf 3) RED=$(tput setaf 1)
else
  BOLD="" DIM="" RESET="" GREEN="" CYAN="" YELLOW="" RED=""
fi

# ─── Restore terminal on unexpected exit ────────────────────────────────────
cleanup() { stty echo icanon 2>/dev/null || true; tput cnorm 2>/dev/null || true; }
trap cleanup EXIT

# ─── Globals ────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OS=""
SKILLS=()           # discovered skill folder names
SKILL_DESCS=()      # one-line descriptions (from frontmatter)
SKILL_SEL=()        # 1/0 toggle per skill
TOOLS=("Claude Code" "Cursor" "Windsurf" "GitHub Copilot" "OpenAI Codex" "OpenCode" "Google Antigravity")
TOOL_SEL=()         # 1/0 toggle per tool
INSTALL_SCOPE=""    # "global" or "project"
INSTALLED=()        # log: "skill → tool → path"

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

# ─── Discover skills (folders containing SKILL.md) ─────────────────────────
discover_skills() {
  local dir desc
  for dir in "$SCRIPT_DIR"/skills/*/; do
    [[ -f "$dir/SKILL.md" ]] || continue
    local name
    name="$(basename "$dir")"
    # Extract description from YAML frontmatter (awk for macOS/Linux compat)
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
    echo "${RED}No skills found (no subdirectories with SKILL.md in skills/).${RESET}"
    exit 1
  fi
}

# ─── Interactive checkbox list (Bash 3.2 compatible) ────────────────────────
# Usage: checkbox_select <title> <items_array_name> <descs_array_name> <selection_array_name>
# Modifies the selection array in-place (0/1 values) via eval.
checkbox_select() {
  local title="$1"
  local items_name=$2
  local descs_name=$3
  local sel_name=$4

  eval "local count=\${#${items_name}[@]}"
  local cursor=0

  # Hide cursor, enable raw input
  tput civis 2>/dev/null || true
  stty -echo -icanon min 1 time 0 2>/dev/null || true

  while true; do
    # Draw the list
    printf "\033[2J\033[H"  # clear screen, move to top
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

    # Read a keypress
    local key
    key=$(dd bs=1 count=1 2>/dev/null) || true
    if [[ "$key" == $'\x1b' ]]; then
      local seq
      seq=$(dd bs=1 count=2 2>/dev/null) || true
      case "$seq" in
        '[A') [[ $cursor -gt 0 ]] && (( cursor-- )) || true ;;       # Up
        '[B') [[ $cursor -lt $((count - 1)) ]] && (( cursor++ )) || true ;;  # Down
      esac
    elif [[ "$key" == " " ]]; then
      # Toggle
      eval "local cur_val=\${${sel_name}[$cursor]}"
      if [[ "$cur_val" -eq 0 ]]; then
        eval "${sel_name}[$cursor]=1"
      else
        eval "${sel_name}[$cursor]=0"
      fi
    elif [[ "$key" == "" ]]; then
      # Enter
      break
    fi
  done

  # Restore terminal
  stty echo icanon 2>/dev/null || true
  tput cnorm 2>/dev/null || true
}

# ─── Interactive single-choice selector ──────────────────────────────────────
# Usage: radio_select <title> <items_array_name> <descs_array_name> <result_var_name>
# Sets the result variable to the selected index.
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
  local src="$SCRIPT_DIR/skills/$skill"
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
        echo "<!-- pskills: $skill -->"
        strip_frontmatter "$src/SKILL.md"
        echo "<!-- /pskills: $skill -->"
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

# ─── Main ───────────────────────────────────────────────────────────────────
main() {
  detect_os

  echo "${BOLD}${CYAN}"
  echo "  ┌─────────────────────────────────────┐"
  echo "  │         pskills installer            │"
  echo "  └─────────────────────────────────────┘${RESET}"
  echo ""
  echo "  OS detected: ${BOLD}${OS}${RESET}"
  echo ""

  # Discover available skills
  discover_skills

  # ── Step 1: Select skills ──
  # Build tool descriptions for display (empty — tools have no extra desc)
  local TOOL_DESCS=()
  TOOL_DESCS+=("~/.claude/skills/")
  TOOL_DESCS+=("~/.agents/skills/ + .cursor/rules/")
  TOOL_DESCS+=("~/.agents/skills/ + .windsurf/rules/")
  TOOL_DESCS+=("~/.agents/skills/ + .github/instructions/")
  TOOL_DESCS+=("~/.agents/skills/ + ~/.codex/AGENTS.md")
  TOOL_DESCS+=("~/.agents/skills/")
  TOOL_DESCS+=("~/.agents/skills/")

  # Initialise tool selection array
  for (( i = 0; i < ${#TOOLS[@]}; i++ )); do
    TOOL_SEL+=(0)
  done

  # Prepend "Install All" option
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
    # Copy individual selections back (skip index 0 which is "Install All")
    for (( i = 0; i < ${#SKILLS[@]}; i++ )); do
      SKILL_SEL[$i]=${ALL_SKILL_SEL[$((i + 1))]}
    done
  fi

  # Check if any skills were selected
  local any_skill=0
  for s in "${SKILL_SEL[@]}"; do [[ $s -eq 1 ]] && any_skill=1 && break; done
  if [[ $any_skill -eq 0 ]]; then
    printf "\033[2J\033[H"
    echo "${YELLOW}No skills selected — exiting.${RESET}"
    exit 0
  fi

  # ── Step 2: Select tools ──
  checkbox_select "Select target tools:" TOOLS TOOL_DESCS TOOL_SEL

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
    for (( j = 0; j < ${#TOOLS[@]}; j++ )); do
      [[ ${TOOL_SEL[$j]} -eq 0 ]] && continue
      echo "  ${GREEN}✔${RESET} ${BOLD}${SKILLS[$i]}${RESET} → ${TOOLS[$j]}"
      install_skill_for_tool "${SKILLS[$i]}" "${TOOLS[$j]}"
    done
  done

  # ── Step 5: Summary ──
  print_summary
  echo "${GREEN}Done!${RESET}"
}

main "$@"
