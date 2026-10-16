#!/usr/bin/env python3
"""Resolve the inherited launch profile, and with --start launch a worker on it.

Every worker mirrors the main agent (the one running the skill) unless the user
names something else: the same harness kind, model, thinking level and setup
flags. That is the inherited launch profile.

Rex reports the main agent's kind through its program status record and its
foreground process. The root process's argv carries its launch flags. Neither
carries a model or thinking level chosen mid-session, so the main agent passes
its live values with --main-model and --main-thinking. Claude Code also exports
CLAUDE_EFFORT, read here when this script runs inside the root block.

Resolution, first source with a value wins:

    kind      --kind  >  main agent's kind (root record app, else argv0/script)
    model     --model or a native flag  >  --main-model  >  root argv  >  UNKNOWN
    thinking  --thinking or a native flag  >  --main-thinking  >  CLAUDE_EFFORT
              >  root argv  >  UNKNOWN
    flags     root argv, filtered through the kind's setup-flag allowlist

A worker of a different kind inherits nothing else. Root argv is read from the
local kernel (/proc on Linux, sysctl KERN_PROCARGS2 on macOS), and only when
the Rex server is local; unreadable same-kind argv fails closed unless
--without flags opts out. Session, resume, print, prompt, credential-bearing
and unrecognised flags are dropped and named. Setup-flag values are never
printed, because inline settings or MCP JSON can carry credentials.

--start NAME splits the rightmost column of the root window (or opens a new
window with --new-window), runs the worker as that block's command through the
user's interactive shell, equalizes the columns, and returns only once the
worker reports a ready program status.

Exit codes:
    0  profile resolved (with --start: the worker also reported ready)
    1  error: unreadable main kind without --kind, unreadable same-kind argv
       without --without flags, unmapped --model/--thinking, or a failed start
    2  usage error
    3  with --start: the worker booted into a dialog (blocked); a human is needed

Usage:
    launch_profile.py [--session S] [--root-block B] [--main-model M] [--main-thinking T]
                      [--kind K] [--model M] [--thinking T] [--without bypass|flags]
                      [--start NAME [--cwd DIR] [--new-window] [--timeout SECONDS]]
                      [-- native flags...]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

import grid
import rexlib
from rexlib import RexError

SWITCH, VALUE, VALUES = 0, 1, "+"  # flag arity; VALUES = tokens up to the next flag
POSIX_SHELLS = {"zsh", "bash", "sh", "dash", "ksh", "mksh"}


def _codex_effort(level: str) -> list[str]:
    return ["--config", f'model_reasoning_effort="{level}"']


# Setup flags carried into a worker, with their arity. Checked against the
# --help of claude 2.1.301, pi 1.3.0 and codex 0.162.1. An unlisted flag is
# dropped: session, resume, print and prompt flags, credentials (pi --api-key),
# and anything a newer CLI added. `bypass` names permission or trust overrides
# that are inherited but disclosed: None matches any use, a set those values.
KINDS: dict[str, dict] = {
    "claude": {
        "binaries": ("claude",),
        "model_keys": {"--model"},
        "thinking_keys": {"--effort"},
        "emit_model": lambda v: ["--model", v],
        "emit_thinking": lambda v: ["--effort", v],
        "thinking_env": "CLAUDE_EFFORT",
        "aliases": {"--allowedTools": "--allowed-tools", "--disallowedTools": "--disallowed-tools"},
        "flags": {
            "--model": VALUE, "--effort": VALUE, "--fallback-model": VALUE,
            "--permission-mode": VALUE, "--dangerously-skip-permissions": SWITCH,
            "--allow-dangerously-skip-permissions": SWITCH, "--add-dir": VALUES,
            "--mcp-config": VALUES, "--strict-mcp-config": SWITCH, "--settings": VALUE,
            "--setting-sources": VALUE, "--plugin-dir": VALUE, "--plugin-url": VALUE,
            "--agent": VALUE, "--agents": VALUE, "--allowed-tools": VALUES,
            "--disallowed-tools": VALUES, "--tools": VALUES, "--system-prompt": VALUE,
            "--append-system-prompt": VALUE, "--betas": VALUES, "--autocompact": VALUE,
            "--chrome": SWITCH, "--no-chrome": SWITCH, "--ide": SWITCH, "--bare": SWITCH,
            "--safe-mode": SWITCH, "--restricted": SWITCH, "--verbose": SWITCH,
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
            "-t": "--tools", "-xt": "--exclude-tools", "-nt": "--no-tools",
            "-nbt": "--no-builtin-tools", "-e": "--extension", "-ne": "--no-extensions",
            "-ns": "--no-skills", "-np": "--no-prompt-templates", "-nc": "--no-context-files",
            "-a": "--approve", "-na": "--no-approve",
        },
        "flags": {
            "--provider": VALUE, "--model": VALUE, "--thinking": VALUE, "--models": VALUE,
            "--system-prompt": VALUE, "--append-system-prompt": VALUE, "--session-dir": VALUE,
            "--no-session": SWITCH, "--tools": VALUE, "--exclude-tools": VALUE,
            "--no-tools": SWITCH, "--no-builtin-tools": SWITCH, "--extension": VALUE,
            "--no-extensions": SWITCH, "--skill": VALUE, "--no-skills": SWITCH,
            "--prompt-template": VALUE, "--no-prompt-templates": SWITCH, "--theme": VALUE,
            "--use-theme": VALUE, "--no-themes": SWITCH, "--no-context-files": SWITCH,
            "--tui-mode": VALUE, "--approve": SWITCH, "--no-approve": SWITCH,
            "--offline": SWITCH, "--verbose": SWITCH, "--advisor-model": VALUE,
            "--advisor-thinking": VALUE, "--advisor-max-uses": VALUE,
            "--advisor-cache": VALUE, "--advisor-enabled": SWITCH,
        },
        "bypass": {"--approve": None},
    },
    "codex": {
        "binaries": ("codex",),
        "model_keys": {"--model", "--config:model"},
        "thinking_keys": {"--config:model_reasoning_effort"},
        "emit_model": lambda v: ["--model", v],
        "emit_thinking": _codex_effort,
        "aliases": {"-m": "--model", "-c": "--config", "-p": "--profile", "-s": "--sandbox",
                    "-a": "--ask-for-approval", "-C": "--cd"},
        "flags": {
            "--model": VALUE, "--config": VALUE, "--profile": VALUE, "--sandbox": VALUE,
            "--ask-for-approval": VALUE, "--dangerously-bypass-approvals-and-sandbox": SWITCH,
            "--dangerously-bypass-hook-trust": SWITCH, "--approve-for-me": SWITCH,
            "--enable": VALUE, "--disable": VALUE, "--strict-config": SWITCH, "--oss": SWITCH,
            "--local-provider": VALUE, "--cd": VALUE, "--add-dir": VALUE, "--search": SWITCH,
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
            groups.append({"key": group_key(name, values), "name": name, "tokens": tokens[i:end], "values": values})
        i = end
    if positionals:
        dropped.append(f"{positionals} positional")
    return groups, dropped


def read_process_argv(pid: int) -> list[str] | None:
    """Exact argv of a local process (see rexlib.read_process)."""
    return rexlib.read_process(pid)[0]


def binary_name(token: str) -> str:
    base = os.path.basename(token)
    for ext in (".js", ".mjs", ".cjs"):
        if base.endswith(ext):
            return base[: -len(ext)]
    return base


def read_main(session: str, root: str) -> tuple[dict | None, str]:
    try:
        agent = rexlib.inspect_agent(session, root)
    except RexError as err:
        return None, str(err)
    if agent["status"] in ("no-agent", "exited") or not agent["kind"]:
        return None, f"no agent runs in block {root} (status {agent['status']})"
    return agent, ""


def read_root_argv(session: str, root: str, spec: dict, pid: int | None) -> tuple[list[str] | None, str]:
    """Return the tokens after the harness binary in the root process's argv."""
    try:
        endpoint = rexlib.whoami().get("endpoint") or ""
    except RexError as err:
        return None, str(err)
    if not endpoint.startswith("unix:"):
        return None, f"the Rex server is remote ({endpoint}), so the root process is not on this machine"
    if not pid:
        return None, "Rex reported no foreground process for the root block"
    argv = read_process_argv(pid)
    if not argv:
        return None, f"argv of process {pid} is unreadable on this machine"
    indexes = [i for i, tok in enumerate(argv) if binary_name(tok) in spec["binaries"]]
    wrapped = indexes and indexes[0] == 1 and binary_name(argv[0]) in {"node", "bun"}
    if indexes and (indexes[0] == 0 or wrapped):
        return argv[indexes[0] + 1 :], ""
    return None, f"process {pid} is not running {'/'.join(spec['binaries'])} (argv0 {binary_name(argv[0])})"


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


def worker_binary(kind: str, main: dict | None, root_proc: dict) -> str:
    """Same install as main for a same-kind worker; otherwise the bare name on PATH."""
    spec = KINDS.get(kind, {"binaries": (kind,)})
    if main and main["kind"] == kind:
        fg = root_proc.get("foreground") or {}
        for key in ("invoked_path", "script", "argv0"):
            path = fg.get(key) or ""
            if os.path.isabs(path) and binary_name(path) in spec["binaries"]:
                return path
    return spec["binaries"][0]


def build_profile(args, native: list[str]) -> tuple[dict | None, list[str], str]:
    """Return (profile, worker argv after the binary, error)."""
    session, root = args.session, args.root_block
    main, err = read_main(session, root)
    main_kind = main["kind"] if main else None
    if main_kind is None:
        if not args.kind:
            return None, [], (f"cannot read the main agent's harness from block {root} ({err}). "
                              "Pass --kind KIND --without flags for an explicit reduced-inheritance "
                              f"worker, or check 'rex block call -s {session} -b {root} process'.")
        if "flags" not in args.without:
            return None, [], (f"cannot verify whether worker kind '{args.kind}' matches the main "
                              f"agent's unreadable harness ({err}). Pass --without flags to "
                              "explicitly start without inheriting the main profile.")
    kind = args.kind or main_kind
    inherited = main_kind is not None and kind == main_kind
    spec = KINDS.get(kind)
    warnings: list[str] = []
    if main_kind is None:
        warnings.append(f"main agent's harness unreadable ({err}); model, thinking level and "
                        "setup flags not inherited")

    if spec is None:
        if args.model or args.thinking:
            return None, [], (f"no model/thinking flag mapping for kind '{kind}'. Pass its native "
                              f"flag after '--' instead (check '{kind} --help').")
        if inherited:
            warnings.append(f"no flag table for kind '{kind}': only the kind is inherited, not "
                            "model, thinking level or launch flags")
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
        tail, perr = read_root_argv(session, root, spec, main.get("pid"))
        if tail is None:
            if "flags" not in args.without:
                return None, [], (f"cannot safely inherit the main agent's setup flags ({perr}). "
                                  "Pass --without flags to explicitly start with reduced "
                                  "inheritance.")
            warnings.append(f"root launch flags unreadable ({perr}); setup flag inheritance "
                            "explicitly disabled")
            flags_source = "opted out"
        else:
            root_groups, dropped = parse_groups(spec, tail, strict=True)
            flags_source = "root argv"

    explicit_groups, _ = parse_groups(spec, native, strict=False)
    env = None
    env_name = spec.get("thinking_env")
    if inherited and env_name and os.environ.get("REX_BLOCK") == root and os.environ.get(env_name):
        env = (env_name, os.environ[env_name])
    model, model_src, model_add = resolve_field(
        spec, "model", args.model, args.main_model if inherited else "", None, root_groups, explicit_groups)
    thinking, thinking_src, thinking_add = resolve_field(
        spec, "thinking", args.thinking, args.main_thinking if inherited else "", env, root_groups, explicit_groups)
    for field, value, source in (("model", model, model_src), ("thinking", thinking, thinking_src)):
        launched = [group_value(g) for g in root_groups if g["key"] in spec[f"{field}_keys"]]
        if source == "self-report" and launched and launched[-1] != value:
            warnings.append(f"self-reported {field} {value} differs from launch argv {launched[-1]}; "
                            "confirm the live value before spawning more workers")
    if not inherited:
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
        "kind": kind, "main_kind": main_kind, "inherited": inherited,
        "model": {"value": model, "source": model_src},
        "thinking": {"value": thinking, "source": thinking_src},
        "flags": sorted({stem(g["name"]) for g in kept if g["key"] not in live_keys}),
        "flags_source": flags_source, "without": sorted(set(args.without)),
        "explicit": [stem(g["name"]) for g in explicit_groups if g["name"]],
        "bypass": [label for g in kept if (label := bypass_label(spec, g))],
        "dropped": dropped, "warnings": warnings, "argc": len(argv),
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


def unique_name(session: str, name: str) -> str:
    taken = {(b.get("label") or "").lower() for b in rexlib.list_blocks(session)}
    return name if name not in taken else f"{name[:21]}-{int(time.time())}"


def wait_ready(session: str, block: str, watch: rexlib.Watch, timeout: float):
    """(outcome, detail): ready, blocked, exited or timeout, from the worker's own status.

    Ready needs an idle or done record owned by the worker's process. A CLI that
    reports nothing at rest, or sits in a dialog that reports nothing, times out.
    """
    start, next_poll = time.monotonic(), 0.0
    while time.monotonic() - start < timeout:
        watch.pump(0.25)
        for ev in watch.take(block):
            name, body = ev.get("name"), ev.get("payload") or {}
            if name == "child_exited":
                return "exited", body
            if name == "program_status_changed" and not body.get("id"):
                state = (body.get("record") or {}).get("state")
                if state == "blocked":
                    return "blocked", body.get("record")
                if state == "error":
                    return "error", body.get("record")
                if state in ("idle", "done"):
                    return "ready", body.get("record")
        if time.monotonic() >= next_poll:
            next_poll = time.monotonic() + 0.5
            rec, proc = rexlib.poll_root(session, block)
            if proc.get("child") is None:
                return "exited", proc.get("last_exit") or {}
            owner = (rec or {}).get("owner") or {}
            if rec and (not owner or owner.get("pid") == (proc.get("foreground") or {}).get("pid")):
                state = rec.get("state")
                if state == "blocked":
                    return "blocked", rec
                if state == "error":
                    return "error", rec
                if state in ("idle", "done"):
                    return "ready", rec
    return "timeout", None


def start_worker(args, profile: dict, argv: list[str]) -> int:
    session, root = args.session, args.root_block
    if not rexlib.NAME_RE.match(args.start):
        print(f"Error: worker name '{args.start}' must match [a-z][a-z0-9_-]{{0,31}}.", file=sys.stderr)
        return 2
    name = unique_name(session, args.start)
    if name != args.start:
        print(f"note: '{args.start}' is taken in this session; using '{name}'", file=sys.stderr)
    root_proc = rexlib.block_call(session, root, "process")
    main = {"kind": profile["main_kind"]} if profile["main_kind"] else None
    binary = worker_binary(profile["kind"], main, root_proc)
    command = ["env", f"REX_AGENT_ROLE={name}", binary, *argv]
    shell = os.environ.get("SHELL", "")
    if os.path.isabs(shell) and os.path.basename(shell) in POSIX_SHELLS:
        command = [shell, "-ic", 'exec "$0" "$@"', *command]
    else:
        print(f"warning: SHELL={shell or 'unset'} is not a POSIX shell, so the worker starts "
              "without the interactive shell config (exports from rc files are missing)", file=sys.stderr)
    cwd = os.path.abspath(args.cwd or os.getcwd())
    watch = rexlib.Watch(session)
    widths: list[float] = []
    try:
        if args.new_window:
            made = rexlib.run_json(["window", "new", "-s", session, name, "-c", cwd, "--focus=false",
                                    "--keep-open", "--json", "--", *command])
            block = made["block_ids"][0]
            rexlib.run(["block", "rename", "-s", session, block, name])
        else:
            win, _, cols = grid.columns(session, root)
            made = rexlib.run_json(["split", "-s", session, "-b", cols[-1]["block_id"], "--split=right",
                                    "--focus=false", "--label", name, "-c", cwd, "--keep-open", "--json",
                                    "--", *command])
            made.setdefault("window_id", win.get("window_id", ""))
            block = made["block_ids"][0]
            try:
                widths = grid.equalize(session, root)
            except RexError as err:
                print(f"Error: {err} Worker '{name}' is in block {block}; ask before closing it "
                      f"('rex block close -s {session} {block}').", file=sys.stderr)
                return 1
        outcome, detail = wait_ready(session, block, watch, args.timeout)
    finally:
        watch.close()
    report = {"name": name, "block_id": block, "window_id": made.get("window_id", ""),
              "kind": profile["kind"], "outcome": outcome, "widths": [round(w, 4) for w in widths]}
    if outcome == "ready":
        print(json.dumps(report))
        return 0
    if outcome == "blocked":
        print(json.dumps(report))
        print(f"Error: worker '{name}' booted into a dialog ({(detail or {}).get('kind') or 'blocked'}): "
              f"{(detail or {}).get('msg') or 'see the pane'}. Focus it with 'rex focus -s {session} "
              f"{block}' and let the human answer; never answer it for them.", file=sys.stderr)
        return 3
    screen = ""
    try:
        screen = "\n".join(line for line in rexlib.capture(session, block).splitlines() if line.strip())[-600:]
    except RexError:
        pass
    reason = (f"its program exited ({(detail or {}).get('error') or (detail or {}).get('exit_code')})"
              if outcome == "exited" else
              f"it reported error: {(detail or {}).get('msg') or 'see the pane'}" if outcome == "error" else
              f"no idle program status within {args.timeout:.0f}s (a dialog may be up, or the CLI "
              "does not report OSC 7501 idle)")
    print(f"Error: worker '{name}' did not start: {reason}. Block {block} is an orphan; read it with "
          f"'rex capture -s {session} -b {block}' and ask before closing it."
          + (f"\nLast screen lines:\n{screen}" if screen else ""), file=sys.stderr)
    return 1


def main(argv: list[str]) -> int:
    own, native = (argv[: argv.index("--")], argv[argv.index("--") + 1 :]) if "--" in argv else (argv, [])
    parser = argparse.ArgumentParser(prog="launch_profile.py", allow_abbrev=False,
                                     description="Resolve the inherited launch profile for a Rex worker; --start launches it.")
    parser.add_argument("--session", default=os.environ.get("REX_SESSION", ""), help="session ID (default: $REX_SESSION)")
    parser.add_argument("--root-block", default=os.environ.get("REX_BLOCK", ""),
                        help="the main agent's block (default: $REX_BLOCK)")
    parser.add_argument("--main-model", default="", help="the main agent's own exact model ID (self-report)")
    parser.add_argument("--main-thinking", default="", help="the main agent's own thinking level (self-report)")
    parser.add_argument("--kind", default="", help="worker kind the user named; a different kind inherits nothing else")
    parser.add_argument("--model", default="", help="worker model the user named")
    parser.add_argument("--thinking", default="", help="worker thinking level the user named")
    parser.add_argument("--without", action="append", choices=("bypass", "flags"), default=[],
                        help="drop inherited permission-bypass flags, or every inherited setup flag")
    parser.add_argument("--start", metavar="NAME", default="", help="launch worker NAME on the profile")
    parser.add_argument("--cwd", default="", help="worker working directory (with --start; default: current)")
    parser.add_argument("--new-window", action="store_true", help="open the worker in its own tab, not a column")
    parser.add_argument("--timeout", type=float, default=60.0, help="readiness timeout in seconds (default 60)")
    args = parser.parse_args(own)
    if not args.session or not args.root_block:
        parser.error("--session or --root-block is empty: run inside a Rex terminal, or pass the IDs "
                     "from 'rex whoami --json'")
    try:
        profile, worker_argv, err = build_profile(args, native)
        if profile is None:
            print(f"Error: {err}", file=sys.stderr)
            return 1
        print(summary(profile), file=sys.stderr)
        if not args.start:
            print(json.dumps(profile))
            return 0
        return start_worker(args, profile, worker_argv)
    except RexError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
