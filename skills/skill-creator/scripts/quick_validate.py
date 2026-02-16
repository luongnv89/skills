#!/usr/bin/env python3
"""
Skill validation script - checks structure, frontmatter, and content quality.

Usage:
    python quick_validate.py <skill_directory>
"""

import sys
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


def validate_skill(skill_path):
    """
    Validate a skill directory for structure, frontmatter, and content quality.

    Returns:
        (bool, str): Tuple of (is_valid, message)
    """
    skill_path = Path(skill_path)
    warnings = []

    # ── Structure checks ──

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Check for README.md (required)
    if not (skill_path / 'README.md').exists():
        warnings.append("WARNING: README.md not found -- every skill should include a README.md for human-readable documentation")

    # Read content
    content = skill_md.read_text()

    # ── Frontmatter checks ──

    if not content.startswith('---'):
        return False, "No YAML frontmatter found (must start with ---)"

    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format (missing closing ---)"

    frontmatter_text = match.group(1)

    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    # Check allowed properties
    ALLOWED_PROPERTIES = {
        'name', 'version', 'description', 'license',
        'allowed-tools', 'metadata', 'argument-hint',
        'disable-model-invocation', 'compatibility'
    }
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    # Check required fields
    if 'name' not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if 'version' not in frontmatter:
        return False, "Missing 'version' in frontmatter"
    if 'description' not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    # ── Name validation ──

    name = frontmatter.get('name', '')
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()

    if not name:
        return False, "Name cannot be empty"

    if not re.match(r'^[a-z0-9-]+$', name):
        return False, f"Name '{name}' must be kebab-case (lowercase letters, digits, and hyphens only)"

    if name.startswith('-') or name.endswith('-') or '--' in name:
        return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"

    if len(name) > 64:
        return False, f"Name too long ({len(name)} chars). Maximum is 64."

    # Check name matches folder
    if name != skill_path.name:
        warnings.append(f"WARNING: Name '{name}' does not match folder name '{skill_path.name}'")

    # Check reserved prefixes
    if name.startswith('claude') or name.startswith('anthropic'):
        return False, f"Name '{name}' uses a reserved prefix ('claude' or 'anthropic')"

    # ── Version validation ──

    version = frontmatter.get('version', '')
    if isinstance(version, (int, float)):
        version = str(version)
    if not isinstance(version, str):
        return False, f"Version must be a string, got {type(version).__name__}"
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        return False, f"Version '{version}' must follow semver (MAJOR.MINOR.PATCH, e.g., 1.0.0)"

    # ── Description validation ──

    description = frontmatter.get('description', '')
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()

    if not description:
        return False, "Description cannot be empty"

    if '<' in description or '>' in description:
        return False, "Description cannot contain XML angle brackets (< or >)"

    if len(description) > 1024:
        return False, f"Description too long ({len(description)} chars). Maximum is 1024."

    # Description quality: check for WHAT + WHEN pattern
    trigger_keywords = [
        'use when', 'use this when', 'trigger', 'use for',
        'ask to', 'asks to', 'asks for', 'mentions',
        'says', 'want to', 'wants to', 'need to', 'needs to'
    ]
    desc_lower = description.lower()
    has_trigger = any(kw in desc_lower for kw in trigger_keywords)
    if not has_trigger:
        warnings.append(
            "WARNING: Description may be missing trigger phrases. "
            "Include WHEN to use this skill (e.g., 'Use when user asks to...', 'Use for...')"
        )

    if len(description) < 50:
        warnings.append("WARNING: Description is very short. Consider adding more detail about what the skill does and when to use it.")

    # ── Body content checks ──

    body = content[match.end():].strip()

    if not body:
        return False, "SKILL.md body is empty (must contain instructions)"

    # Check for remaining TODO placeholders
    todo_matches = re.findall(r'\[TODO[:\]].{0,80}', body, re.IGNORECASE)
    if todo_matches:
        return False, f"Found TODO placeholder(s) in body: {todo_matches[0]}..."

    # Check SKILL.md size
    line_count = len(content.splitlines())
    if line_count > 500:
        warnings.append(f"WARNING: SKILL.md is {line_count} lines (recommended max: 500). Consider moving details to references/.")

    word_count = len(body.split())
    if word_count > 5000:
        warnings.append(f"WARNING: SKILL.md body is ~{word_count} words (recommended max: 5000). Consider moving details to references/.")

    # Check for examples section
    if not re.search(r'^##\s.*example', body, re.IGNORECASE | re.MULTILINE):
        warnings.append("WARNING: No 'Examples' section found. Consider adding usage examples.")

    # Check for error handling section
    error_patterns = [r'error\s*handling', r'troubleshoot', r'common\s*issues', r'error.*scenario']
    has_error_section = any(re.search(p, body, re.IGNORECASE) for p in error_patterns)
    if not has_error_section:
        warnings.append("WARNING: No error handling section found. Consider adding error handling guidance.")

    # Check for references to bundled resources
    refs_dir = skill_path / 'references'
    scripts_dir = skill_path / 'scripts'
    if refs_dir.exists() and list(refs_dir.iterdir()):
        ref_files = [f.name for f in refs_dir.iterdir() if f.is_file()]
        for ref_file in ref_files:
            if ref_file not in body and f"references/{ref_file}" not in body:
                warnings.append(f"WARNING: Reference file '{ref_file}' exists but is not mentioned in SKILL.md body.")

    if scripts_dir.exists() and list(scripts_dir.iterdir()):
        script_files = [f.name for f in scripts_dir.iterdir() if f.is_file() and not f.name.startswith('__')]
        for script_file in script_files:
            if script_file not in body and f"scripts/{script_file}" not in body:
                warnings.append(f"WARNING: Script file '{script_file}' exists but is not mentioned in SKILL.md body.")

    # ── Build result ──

    if warnings:
        warning_text = "\n".join(f"  - {w}" for w in warnings)
        return True, f"Skill is valid with warnings:\n{warning_text}"

    return True, "Skill is valid!"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_validate.py <skill_directory>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)
