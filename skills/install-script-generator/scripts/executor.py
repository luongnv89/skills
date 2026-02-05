#!/usr/bin/env python3
"""
Installation Plan Executor - Executes installation steps with verification.
Handles rollback on failure and generates detailed reports.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Try to use PyYAML if available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def simple_yaml_load(content):
    """Simple YAML parser for when PyYAML is not available."""
    # This is a basic parser - for complex YAML, PyYAML is recommended
    result = {}
    current_list = None
    current_list_key = None
    current_item = None

    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith('#'):
            i += 1
            continue

        indent = len(line) - len(line.lstrip())

        if stripped.startswith('- '):
            # List item
            if current_list_key:
                item_content = stripped[2:]
                if ':' in item_content:
                    # Start of a dict in list
                    current_item = {}
                    key, _, value = item_content.partition(':')
                    value = value.strip()
                    if value:
                        current_item[key.strip()] = parse_value(value)
                    else:
                        current_item[key.strip()] = None
                    current_list.append(current_item)
                else:
                    current_list.append(parse_value(item_content))
        elif ':' in stripped:
            key, _, value = stripped.partition(':')
            key = key.strip()
            value = value.strip()

            if indent == 0:
                # Top-level key
                if value:
                    result[key] = parse_value(value)
                else:
                    # Check if next line starts a list
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith('-'):
                        result[key] = []
                        current_list = result[key]
                        current_list_key = key
                    else:
                        result[key] = {}
            elif current_item is not None:
                # Key within a list item
                current_item[key] = parse_value(value) if value else None

        i += 1

    return result


def parse_value(value):
    """Parse a YAML value string."""
    if value.lower() == 'null' or value.lower() == 'none' or value == '~':
        return None
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def yaml_load(content):
    """Load YAML content."""
    if HAS_YAML:
        return yaml.safe_load(content)
    else:
        return simple_yaml_load(content)


def run_command(command, timeout=300):
    """Run a command and return result."""
    if not command or command.startswith('#'):
        return {
            "success": True,
            "output": "Skipped (no command or placeholder)",
            "error": None,
            "returncode": 0,
        }

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": None,
            "error": f"Command timed out after {timeout} seconds",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "output": None,
            "error": str(e),
            "returncode": -1,
        }


def execute_plan(plan, dry_run=False):
    """Execute the installation plan."""
    report = {
        "target": plan.get("target", "unknown"),
        "platform": plan.get("platform", "unknown"),
        "started_at": datetime.now().isoformat(),
        "dry_run": dry_run,
        "steps": [],
        "success": True,
        "failed_step": None,
    }

    executed_steps = []

    print(f"\n{'=' * 60}")
    print(f"Installing: {plan.get('target', 'unknown')}")
    print(f"Platform: {plan.get('platform', 'unknown')}")
    print(f"{'=' * 60}\n")

    for step in plan.get("steps", []):
        step_num = step.get("step", "?")
        step_name = step.get("name", "Unnamed step")
        command = step.get("command", "")
        verify = step.get("verify", "")
        rollback = step.get("rollback")
        critical = step.get("critical", True)

        step_report = {
            "step": step_num,
            "name": step_name,
            "status": "pending",
            "command_result": None,
            "verify_result": None,
        }

        print(f"[Step {step_num}] {step_name}")
        print(f"  Command: {command}")

        if dry_run:
            print("  Status: SKIPPED (dry run)")
            step_report["status"] = "skipped"
            report["steps"].append(step_report)
            continue

        # Execute command
        print("  Executing...", end=" ", flush=True)
        result = run_command(command)
        step_report["command_result"] = result

        if not result["success"]:
            print("FAILED")
            print(f"  Error: {result['error']}")
            step_report["status"] = "failed"
            report["steps"].append(step_report)

            if critical:
                report["success"] = False
                report["failed_step"] = step_num

                # Execute rollbacks
                print("\n  Rolling back previous steps...")
                for prev_step in reversed(executed_steps):
                    rb_cmd = prev_step.get("rollback")
                    if rb_cmd:
                        print(f"    Rolling back: {prev_step.get('name')}")
                        run_command(rb_cmd)

                break
            else:
                print("  (Non-critical step, continuing...)")
                continue

        print("OK")

        # Verify
        if verify:
            print(f"  Verifying: {verify}")
            verify_result = run_command(verify)
            step_report["verify_result"] = verify_result

            if not verify_result["success"]:
                print("  Verification FAILED")
                step_report["status"] = "verify_failed"

                if critical:
                    report["success"] = False
                    report["failed_step"] = step_num

                    # Execute rollbacks
                    print("\n  Rolling back...")
                    if rollback:
                        run_command(rollback)
                    for prev_step in reversed(executed_steps):
                        rb_cmd = prev_step.get("rollback")
                        if rb_cmd:
                            print(f"    Rolling back: {prev_step.get('name')}")
                            run_command(rb_cmd)

                    report["steps"].append(step_report)
                    break
            else:
                print("  Verification: OK")

        step_report["status"] = "success"
        report["steps"].append(step_report)
        executed_steps.append(step)

    report["completed_at"] = datetime.now().isoformat()

    print(f"\n{'=' * 60}")
    if report["success"]:
        print(f"SUCCESS: {plan.get('target')} installed successfully!")
    else:
        print(f"FAILED: Installation failed at step {report['failed_step']}")
    print(f"{'=' * 60}\n")

    return report


def generate_report_markdown(report):
    """Generate a markdown report."""
    lines = [
        f"# Installation Report: {report['target']}",
        "",
        f"**Platform:** {report['platform']}",
        f"**Started:** {report['started_at']}",
        f"**Completed:** {report.get('completed_at', 'N/A')}",
        f"**Status:** {'SUCCESS' if report['success'] else 'FAILED'}",
        "",
    ]

    if report.get("dry_run"):
        lines.append("*This was a dry run - no commands were executed.*\n")

    lines.append("## Steps")
    lines.append("")

    for step in report.get("steps", []):
        status_icon = {
            "success": "✅",
            "failed": "❌",
            "verify_failed": "⚠️",
            "skipped": "⏭️",
            "pending": "⏳",
        }.get(step["status"], "❓")

        lines.append(f"### Step {step['step']}: {step['name']}")
        lines.append(f"**Status:** {status_icon} {step['status'].upper()}")
        lines.append("")

        if step.get("command_result"):
            result = step["command_result"]
            if result.get("output"):
                lines.append("**Output:**")
                lines.append("```")
                lines.append(result["output"][:1000])  # Truncate long output
                lines.append("```")
            if result.get("error") and not result["success"]:
                lines.append("**Error:**")
                lines.append("```")
                lines.append(result["error"][:500])
                lines.append("```")

        lines.append("")

    if not report["success"]:
        lines.append("## Troubleshooting")
        lines.append("")
        lines.append(f"The installation failed at step {report['failed_step']}.")
        lines.append("Please check the error output above and ensure:")
        lines.append("- You have the required permissions (sudo/admin)")
        lines.append("- Your package manager is properly configured")
        lines.append("- Network connectivity is available")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Execute installation plan")
    parser.add_argument("--plan", default="installation_plan.yaml", help="Installation plan file")
    parser.add_argument("--output", default="install_report.md", help="Output report file")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--json", action="store_true", help="Output JSON report instead of markdown")

    args = parser.parse_args()

    # Load plan
    plan_file = Path(args.plan)
    if not plan_file.exists():
        print(f"Error: Plan file not found: {plan_file}", file=sys.stderr)
        return 1

    with open(plan_file) as f:
        plan = yaml_load(f.read())

    # Execute plan
    report = execute_plan(plan, dry_run=args.dry_run)

    # Write report
    output_file = Path(args.output)
    if args.json:
        with open(output_file.with_suffix('.json'), "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {output_file.with_suffix('.json')}")
    else:
        markdown = generate_report_markdown(report)
        with open(output_file, "w") as f:
            f.write(markdown)
        print(f"Report saved to: {output_file}")

    return 0 if report["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
