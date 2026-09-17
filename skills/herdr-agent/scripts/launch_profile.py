#!/usr/bin/env python3
"""Resolve the inherited launch profile, and with --start launch a worker on it.

Every worker this skill spawns mirrors the main agent (the one running the
skill) unless the user names something else: the same harness kind, the same
model, the same thinking level, and the same setup flags. That is the inherited
launch profile.

Herdr reports the main agent's kind, and the root pane's argv carries the flags
it was launched with. Neither carries a model or thinking level chosen
mid-session, and the harness config default can differ from both, so a worker
launched bare can silently run a different model or effort. Only the main agent
knows its live values: it passes them with --main-model and --main-thinking.
Claude Code also exports its effort as CLAUDE_EFFORT, which this script reads
itself when it runs inside the root pane.

Resolution, first source with a value wins:

    kind      --kind  >  main agent's kind (`herdr agent get <root-pane>`)
    model     --model or a native flag  >  --main-model  >  root argv  >  UNKNOWN
    thinking  --thinking or a native flag  >  --main-thinking  >  CLAUDE_EFFORT
              >  root argv  >  UNKNOWN
    flags     root argv, filtered through the kind's setup-flag allowlist

Nothing but the kind is inherited when the worker's kind differs from the main
agent's: a Claude model id or effort level means nothing to another CLI. When
the main kind is unreadable, an explicit worker kind proves no relationship:
--without flags is required, and main model/thinking self-reports are ignored.
Root argv is read only for kinds with a verified flag table (claude, pi, codex).
Session, resume, print, prompt, credential-bearing and unrecognised flags are
dropped and named, never guessed at. An UNKNOWN model or thinking level is not
an error: the worker starts on its config default and the profile line says so.
Unreadable setup flags fail closed unless --without flags explicitly disables
their inheritance. Setup-flag values are never printed, because inline settings
or MCP JSON can carry credentials.

Exit codes:
    0  profile resolved (with --start: the agent also reported ready)
    1  error: herdr missing, main agent's kind unreadable and no --kind given,
       same-kind root argv unreadable without --without flags,
       --model/--thinking for a kind with no flag mapping, or agent start failed
    2  usage error

Inherited permission-bypass flags are carried like any other setup flag, and
the summary names them on a ⚠ line; --without bypass drops them, and
--without flags drops every inherited setup flag but the model and thinking.

Usage:
    launch_profile.py --root-pane ID [--main-model M] [--main-thinking T]
                      [--kind K] [--model M] [--thinking T] [--without bypass|flags]
                      [--start NAME --pane ID [--timeout MS]] [-- native flags...]

Without --start the profile is printed as JSON on stdout and as one summary
line on stderr. With --start the summary goes to stderr, then
`herdr agent start NAME --kind K --pane ID --timeout MS -- <profile args>` runs.
"""

from __future__ import annotations

import argparse
import re
import json
import os
import shutil
import subprocess
import sys

SWITCH, VALUE, VALUES = 0, 1, "+"  # flag arity; VALUES = tokens up to the next flag


def _codex_effort(level: str) -> list[str]:
    return ["--config", f'model_reasoning_effort="{level}"']


# Setup flags carried into a worker, with their arity. Verified against
# `claude --help` 2.1.274, `pi --help`, and `codex --help` 0.153.4. A flag that
# is not listed is dropped: that covers session, resume, print and prompt
# flags, credentials (pi --api-key), and anything a newer CLI added.
# `bypass` names permission or trust overrides that are inherited but disclosed:
# None matches any use, a set matches those values only.
KINDS: dict[str, dict] = {
    "claude": {
        "binaries": ("claude",),
        "model_keys": {"--model"},
        "thinking_keys": {"--effort"},
        "emit_model": lambda v: ["--model", v],
        "emit_thinking": lambda v: ["--effort", v],
        "thinking_env": "CLAUDE_EFFORT",
        "aliases": {
            "--allowedTools": "--allowed-tools",
            "--disallowedTools": "--disallowed-tools",
        },
        "flags": {
            "--model": VALUE,
            "--effort": VALUE,
            "--fallback-model": VALUE,
            "--permission-mode": VALUE,
            "--dangerously-skip-permissions": SWITCH,
            "--allow-dangerously-skip-permissions": SWITCH,
            "--add-dir": VALUES,
            "--mcp-config": VALUES,
            "--strict-mcp-config": SWITCH,
            "--settings": VALUE,
            "--setting-sources": VALUE,
            "--plugin-dir": VALUE,
            "--plugin-url": VALUE,
            "--agent": VALUE,
            "--agents": VALUE,
            "--allowed-tools": VALUES,
            "--disallowed-tools": VALUES,
            "--tools": VALUES,
            "--system-prompt": VALUE,
            "--system-prompt-file": VALUE,
            "--append-system-prompt": VALUE,
            "--append-system-prompt-file": VALUE,
            "--betas": VALUES,
            "--autocompact": VALUE,
            "--chrome": SWITCH,
            "--no-chrome": SWITCH,
            "--ide": SWITCH,
            "--bare": SWITCH,
            "--safe-mode": SWITCH,
            "--restricted": SWITCH,
            "--verbose": SWITCH,
            "--ax-screen-reader": SWITCH,
        },
        "bypass": {
            "--dangerously-skip-permissions": None,
            "--allow-dangerously-skip-permissions": None,
            "--permission-mode": {"bypassPermissions"},
        },
    },
    "pi": {
        "binaries": ("pi",),
        "model_keys": {"--model"},
        "thinking_keys": {"--thinking"},
        "emit_model": lambda v: ["--model", v],
        "emit_thinking": lambda v: ["--thinking", v],
        "aliases": {
            "-t": "--tools",
            "-xt": "--exclude-tools",
            "-nt": "--no-tools",
            "-nbt": "--no-builtin-tools",
            "-e": "--extension",
            "-ne": "--no-extensions",
            "-ns": "--no-skills",
            "-np": "--no-prompt-templates",
            "-nc": "--no-context-files",
            "-a": "--approve",
            "-na": "--no-approve",
        },
        "flags": {
            "--provider": VALUE,
            "--model": VALUE,
            "--thinking": VALUE,
            "--models": VALUE,
            "--system-prompt": VALUE,
            "--append-system-prompt": VALUE,
            "--session-dir": VALUE,
            "--no-session": SWITCH,
            "--tools": VALUE,
            "--exclude-tools": VALUE,
            "--no-tools": SWITCH,
            "--no-builtin-tools": SWITCH,
            "--extension": VALUE,
            "--no-extensions": SWITCH,
            "--skill": VALUE,
            "--no-skills": SWITCH,
            "--prompt-template": VALUE,
            "--no-prompt-templates": SWITCH,
            "--theme": VALUE,
            "--use-theme": VALUE,
            "--no-themes": SWITCH,
            "--no-context-files": SWITCH,
            "--tui-mode": VALUE,
            "--approve": SWITCH,
            "--no-approve": SWITCH,
            "--offline": SWITCH,
            "--verbose": SWITCH,
            "--advisor-model": VALUE,
            "--advisor-thinking": VALUE,
            "--advisor-max-uses": VALUE,
            "--advisor-cache": VALUE,
            "--advisor-enabled": SWITCH,
        },
        "bypass": {"--approve": None},
    },
    "codex": {
        "binaries": ("codex",),
        "model_keys": {"--model", "--config:model"},
        "thinking_keys": {"--config:model_reasoning_effort"},
        "emit_model": lambda v: ["--model", v],
        "emit_thinking": _codex_effort,
        "aliases": {
            "-m": "--model",
            "-c": "--config",
            "-p": "--profile",
            "-s": "--sandbox",
            "-a": "--ask-for-approval",
            "-C": "--cd",
        },
        "flags": {
            "--model": VALUE,
            "--config": VALUE,
            "--profile": VALUE,
            "--sandbox": VALUE,
            "--ask-for-approval": VALUE,
            "--dangerously-bypass-approvals-and-sandbox": SWITCH,
            "--dangerously-bypass-hook-trust": SWITCH,
            "--approve-for-me": SWITCH,
            "--enable": VALUE,
            "--disable": VALUE,
            "--strict-config": SWITCH,
            "--oss": SWITCH,
            "--local-provider": VALUE,
            "--cd": VALUE,
            "--add-dir": VALUE,
            "--search": SWITCH,
            "--no-alt-screen": SWITCH,
        },
        "bypass": {
            "--dangerously-bypass-approvals-and-sandbox": None,
            "--dangerously-bypass-hook-trust": None,
            "--sandbox": {"danger-full-access"},
            "--ask-for-approval": {"never"},
            "--config:sandbox_mode": {"danger-full-access"},
            "--config:approval_policy": {"never"},
        },
    },
}


FLAG_STEM = re.compile(r"-{1,2}[A-Za-z][A-Za-z0-9_-]*")


def stem(tok: str) -> str:
    """A printable flag name: never a value, prompt text, or glued credential."""
    match = FLAG_STEM.match(tok)
    return match.group(0)[:40] if match and len(match.group(0)) <= 40 else "1 malformed flag"


def is_flag(tok: str) -> bool:
    return tok.startswith("-") and tok not in ("-", "--")


def group_key(name: str, values: list[str]) -> str:
    """`--config key=value` groups are keyed per config key, not per flag."""
    if name == "--config" and values:
        return "--config:" + values[0].split("=", 1)[0].strip()
    return name


def group_value(group: dict) -> str:
    if not group["values"]:
        return ""
    value = group["values"][0]
    if group["name"] == "--config":
        value = value.split("=", 1)[1] if "=" in value else ""
    return value.strip().strip("\"'")


def parse_groups(spec: dict | None, tokens: list[str], strict: bool):
    """Split argv tokens into flag groups.

    strict (root argv): keep only allowlisted flags that carry their values.
    Unknown flags drop together with the tokens that follow them, and
    positionals (a prompt, a subcommand, anything after `--`) drop too.
    not strict (the caller's explicit native flags): keep every token verbatim
    and only group them, so an explicit flag can replace an inherited one.
    """
    table = spec["flags"] if spec else {}
    aliases = spec["aliases"] if spec else {}
    groups: list[dict] = []
    dropped: list[str] = []
    positionals = 0
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "--" or not is_flag(tok):
            end = len(tokens) if tok == "--" else i + 1
            if strict:
                positionals += end - i - (1 if tok == "--" else 0)
            else:
                groups.append({"key": None, "name": None, "tokens": tokens[i:end], "values": []})
            i = end
            continue
        raw, _, inline = tok.partition("=") if tok.startswith("--") else (tok, "", "")
        name = aliases.get(raw, raw)
        arity = table.get(name)
        if inline or tok.endswith("="):
            end, values = i + 1, [inline]
        elif arity == SWITCH:
            end, values = i + 1, []
        elif arity == VALUE and i + 1 < len(tokens):
            end, values = i + 2, [tokens[i + 1]]
        else:
            end = i + 1
            while end < len(tokens) and not is_flag(tokens[end]) and tokens[end] != "--":
                end += 1
            values = tokens[i + 1 : end]
        if strict and (arity is None or (arity != SWITCH and not values)):
            dropped.append(stem(raw))
        else:
            groups.append(
                {"key": group_key(name, values), "name": name, "tokens": tokens[i:end], "values": values}
            )
        i = end
    if positionals:
        dropped.append(f"{positionals} positional")
    return groups, dropped


def herdr_json(cmd: list[str]) -> tuple[dict | None, str]:
    proc = subprocess.run(["herdr", *cmd], capture_output=True, text=True)
    payload = proc.stdout.strip() or proc.stderr.strip()
    try:
        data = json.loads(payload)
    except ValueError:
        return None, "unparseable herdr output"
    if not isinstance(data, dict):
        return None, "unparseable herdr output"
    if "error" in data:
        err = data["error"]
        return None, str((err.get("code") if isinstance(err, dict) else None) or "error")
    if proc.returncode != 0:
        return None, f"herdr exited {proc.returncode}"
    return data, ""


def read_main_kind(root: str) -> tuple[str | None, str]:
    data, err = herdr_json(["agent", "get", root])
    if data is None:
        return None, err
    agent = (data.get("result") or {}).get("agent")
    kind = agent.get("agent") if isinstance(agent, dict) else None
    if not isinstance(kind, str) or not kind:
        return None, "no agent kind in herdr agent get"
    return kind, ""


def read_root_argv(root: str, spec: dict) -> tuple[list[str] | None, str]:
    """Return tokens after the harness binary, requiring process-info's full argv."""
    data, err = herdr_json(["pane", "process-info", "--pane", root])
    if data is None:
        return None, err
    result = data.get("result")
    info = result.get("process_info") if isinstance(result, dict) else None
    if not isinstance(info, dict):
        return None, "process-info returned a malformed result"
    raw_procs = info.get("foreground_processes")
    if not isinstance(raw_procs, list) or any(not isinstance(p, dict) for p in raw_procs):
        return None, "process-info returned malformed foreground_processes"
    leader = info.get("foreground_process_group_id")
    leaders = [proc for proc in raw_procs if proc.get("pid") == leader]
    candidates = leaders or raw_procs

    def binary_name(token: str) -> str:
        base = os.path.basename(token)
        for ext in (".js", ".mjs", ".cjs"):
            if base.endswith(ext):
                return base[: -len(ext)]
        return base

    for proc in candidates:
        argv0 = proc.get("argv0")
        hinted = isinstance(argv0, str) and binary_name(argv0) in spec["binaries"]
        raw_argv = proc.get("argv")
        if raw_argv is None:
            if hinted:
                return None, "process-info returned argv0 without full argv"
            continue
        if (
            not isinstance(raw_argv, list)
            or not raw_argv
            or any(not isinstance(token, str) or not token for token in raw_argv)
        ):
            if hinted or leaders:
                return None, "process-info returned malformed argv"
            continue
        indexes = [
            idx for idx, token in enumerate(raw_argv)
            if binary_name(token) in spec["binaries"]
        ]
        wrapped = indexes and indexes[0] == 1 and binary_name(raw_argv[0]) in {"node", "bun"}
        if indexes and (hinted or indexes[0] == 0 or wrapped):
            return raw_argv[indexes[0] + 1 :], ""
    return None, "no foreground process has full argv for the harness binary"


def resolve_field(spec, field, explicit, main_value, env, root_groups, explicit_groups):
    """Return (value, source, tokens to add). Tokens are None when nothing is added."""
    keys = spec[f"{field}_keys"]
    emit = spec[f"emit_{field}"]
    for group in explicit_groups:
        if group["key"] in keys:
            return group_value(group), "explicit", None
    if explicit:
        return explicit, "explicit", emit(explicit)
    if main_value:
        return main_value, "self-report", emit(main_value)
    if env:
        return env[1], f"env {env[0]}", emit(env[1])
    for group in reversed(root_groups):
        if group["key"] in keys:
            return group_value(group), "root argv", None
    return "", "UNKNOWN", None


def bypass_label(spec: dict, group: dict) -> str | None:
    rule = spec["bypass"].get(group["key"], spec["bypass"].get(group["name"], False))
    if rule is False:
        return None
    if rule is None:
        return group["name"]
    value = group_value(group)
    return f"{group['key']} {value}" if value in rule else None


def build_profile(args, native: list[str]) -> tuple[dict | None, list[str], str]:
    """Return (profile, argv for agent start, error)."""
    root = args.root_pane
    main_kind, err = read_main_kind(root)
    if main_kind is None:
        if not args.kind:
            return None, [], (
                f"cannot read the main agent's harness from pane {root} ({err}). "
                "Pass --kind KIND --without flags for an explicit reduced-inheritance "
                f"worker, or check 'herdr agent get {root}'."
            )
        if "flags" not in args.without:
            return None, [], (
                f"cannot verify whether worker kind '{args.kind}' matches the main "
                f"agent's unreadable harness ({err}). Pass --without flags to "
                "explicitly start without inheriting the main profile."
            )
    kind = args.kind or main_kind
    inherited = main_kind is not None and kind == main_kind
    self_reported = inherited
    spec = KINDS.get(kind)
    warnings: list[str] = []
    if main_kind is None:
        warnings.append(
            f"main agent's harness unreadable ({err}); model, thinking level and "
            "setup flags not inherited"
        )

    if spec is None:
        if args.model or args.thinking:
            return None, [], (
                f"no model/thinking flag mapping for kind '{kind}'. Pass its native "
                f"flag after '--' instead (check '{kind} --help')."
            )
        if inherited:
            warnings.append(
                f"no flag table for kind '{kind}': only the kind is inherited, not "
                f"model, thinking level or launch flags"
            )
        profile = {
            "kind": kind, "main_kind": main_kind, "inherited": inherited,
            "model": {"value": "", "source": "not mapped"},
            "thinking": {"value": "", "source": "not mapped"},
            "flags": [], "flags_source": "not mapped", "without": sorted(set(args.without)),
            "explicit": [stem(t) for t in native if is_flag(t)],
            "bypass": [], "dropped": [], "warnings": warnings, "argc": len(native),
        }
        return profile, list(native), ""

    root_groups: list[dict] = []
    dropped: list[str] = []
    flags_source = "not inherited"
    if inherited:
        tail, perr = read_root_argv(root, spec)
        if tail is None:
            if "flags" not in args.without:
                return None, [], (
                    f"cannot safely inherit the main agent's setup flags ({perr}). "
                    "The Herdr server's pane process-info API must provide full argv; "
                    "update/restart the server, or pass --without flags to explicitly "
                    "start with reduced inheritance."
                )
            warnings.append(
                f"root launch flags unreadable ({perr}); setup flag inheritance "
                "explicitly disabled"
            )
            flags_source = "opted out"
        else:
            root_groups, dropped = parse_groups(spec, tail, strict=True)
            flags_source = "root argv"

    explicit_groups, _ = parse_groups(spec, native, strict=False)
    env = None
    env_name = spec.get("thinking_env")
    if inherited and env_name and os.environ.get("HERDR_PANE_ID") == root and os.environ.get(env_name):
        env = (env_name, os.environ[env_name])
    model, model_src, model_add = resolve_field(
        spec, "model", args.model, args.main_model if self_reported else "", None, root_groups, explicit_groups
    )
    thinking, thinking_src, thinking_add = resolve_field(
        spec, "thinking", args.thinking, args.main_thinking if self_reported else "", env, root_groups, explicit_groups
    )
    for field, value, source in (("model", model, model_src), ("thinking", thinking, thinking_src)):
        launched = [group_value(g) for g in root_groups if g["key"] in spec[f"{field}_keys"]]
        if source == "self-report" and launched and launched[-1] != value:
            warnings.append(
                f"self-reported {field} {value} differs from launch argv {launched[-1]}; "
                f"confirm the live value before spawning more workers"
            )
    if not self_reported:
        model_src = model_src if model else "not inherited"
        thinking_src = thinking_src if thinking else "not inherited"

    live_keys = spec["model_keys"] | spec["thinking_keys"]
    replaced = {g["key"] for g in explicit_groups if g["key"]}
    if model_add:
        replaced |= spec["model_keys"]
    if thinking_add:
        replaced |= spec["thinking_keys"]
    kept = [g for g in root_groups if g["key"] not in replaced]
    if "flags" in args.without:
        kept = [g for g in kept if g["key"] in live_keys]
    if "bypass" in args.without:
        kept = [g for g in kept if not bypass_label(spec, g)]
    argv = [t for g in kept for t in g["tokens"]] + (model_add or []) + (thinking_add or []) + list(native)

    profile = {
        "kind": kind,
        "main_kind": main_kind,
        "inherited": inherited,
        "model": {"value": model, "source": model_src},
        "thinking": {"value": thinking, "source": thinking_src},
        "flags": sorted({stem(g["name"]) for g in kept if g["key"] not in live_keys}),
        "flags_source": flags_source,
        "without": sorted(set(args.without)),
        "explicit": [stem(g["name"]) for g in explicit_groups if g["name"]],
        "bypass": [label for g in kept if (label := bypass_label(spec, g))],
        "dropped": dropped,
        "warnings": warnings,
        "argc": len(argv),
    }
    return profile, argv, ""


def summary(profile: dict) -> str:
    kind, main_kind = profile["kind"], profile["main_kind"]
    if profile["inherited"]:
        head = f"{kind} (inherited from main)"
    elif main_kind:
        head = f"{kind} (explicit; main is {main_kind}, so model, thinking and flags are not inherited)"
    else:
        head = f"{kind} (explicit; main agent's harness unreadable)"
    parts = [f"Launch profile: {head}"]
    for field in ("model", "thinking"):
        value, source = profile[field]["value"], profile[field]["source"]
        if value:
            parts.append(f"{field} {value} ({source})")
        elif source == "UNKNOWN":
            parts.append(f"{field} UNKNOWN (worker uses its config default)")
        else:
            parts.append(f"{field} — ({source})")
    parts.append(f"flags {', '.join(profile['flags']) or 'none'} ({profile['flags_source']})")
    if profile["without"]:
        parts.append(f"without inherited {', '.join(profile['without'])}")
    if profile["explicit"]:
        parts.append(f"explicit {', '.join(profile['explicit'])}")
    if profile["dropped"]:
        parts.append(f"dropped {', '.join(profile['dropped'])}")
    lines = [" · ".join(parts)]
    if profile["bypass"]:
        lines.append(f"⚠ permission bypass inherited from main: {', '.join(profile['bypass'])}")
    lines.extend(f"warning: {w}" for w in profile["warnings"])
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    own, native = (argv[: argv.index("--")], argv[argv.index("--") + 1 :]) if "--" in argv else (argv, [])
    parser = argparse.ArgumentParser(
        prog="launch_profile.py",
        description="Resolve the inherited launch profile for a Herdr worker; --start launches it.",
        allow_abbrev=False,
    )
    parser.add_argument("--root-pane", default=os.environ.get("HERDR_PANE_ID"),
                        help="the main agent's pane (default: $HERDR_PANE_ID)")
    parser.add_argument("--main-model", default="", help="the main agent's own exact model id (self-report)")
    parser.add_argument("--main-thinking", default="", help="the main agent's own thinking level (self-report)")
    parser.add_argument("--kind", default="", help="worker kind the user named; a different kind inherits nothing else")
    parser.add_argument("--model", default="", help="worker model the user named")
    parser.add_argument("--thinking", default="", help="worker thinking level the user named")
    parser.add_argument("--without", action="append", choices=("bypass", "flags"), default=[],
                        help="drop inherited permission-bypass flags, or every inherited setup flag")
    parser.add_argument("--start", metavar="NAME", default="", help="run herdr agent start NAME with the profile")
    parser.add_argument("--pane", default="", help="pane to start the worker in (with --start)")
    parser.add_argument("--timeout", type=int, default=60000, help="agent start timeout in ms (default 60000)")
    args = parser.parse_args(own)
    if not args.root_pane:
        parser.error("--root-pane is empty: pass the main agent's pane id (normally $HERDR_PANE_ID)")
    if args.start and not args.pane:
        parser.error("--start needs --pane")
    if not shutil.which("herdr"):
        print("Error: herdr not on PATH; install herdr 0.9.0 or later.", file=sys.stderr)
        return 1

    profile, start_argv, err = build_profile(args, native)
    if profile is None:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    print(summary(profile), file=sys.stderr)
    if not args.start:
        print(json.dumps(profile))
        return 0

    cmd = ["herdr", "agent", "start", args.start, "--kind", profile["kind"],
           "--pane", args.pane, "--timeout", str(args.timeout)]
    if start_argv:
        cmd += ["--", *start_argv]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        print(
            f"Error: herdr agent start failed for '{args.start}' in pane {args.pane}. "
            f"A flag the CLI rejects makes it exit at once and the start wait out its "
            f"timeout; read the CLI's own message with 'herdr pane read {args.pane} "
            f"--source recent-unwrapped --lines 20'.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
