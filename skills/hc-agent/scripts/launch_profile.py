#!/usr/bin/env python3
"""Resolve the inherited launch profile, and with --start launch a worker on it.

Every worker mirrors the main agent (the one running the skill) unless the user
names something else: the same harness kind, model, thinking level and setup
flags. That is the inherited launch profile.

`hc get $HC_TERMINAL_ID` reports the main agent's kind (.status.app) and two
argv lists: the terminal's top-level argv, which may be a wrapper such as
`mcc run -- <prompt>` that picks the account, and the foreground process's
full argv. Neither carries a model or thinking level chosen mid-session, so
the main agent passes its live values with --main-model and --main-thinking.
Claude Code also exports CLAUDE_EFFORT, read here when this script runs inside
the root terminal.

Resolution, first source with a value wins:

    kind      --kind  >  main agent's kind (status.app, else foreground argv0)
    model     --model or a native flag  >  --main-model  >  root argv  >  UNKNOWN
    thinking  --thinking or a native flag  >  --main-thinking  >  CLAUDE_EFFORT
              >  root argv  >  UNKNOWN
    flags     root argv, filtered through the kind's setup-flag allowlist

Root argv is the foreground process's argv after the harness binary, or, when
main runs through a wrapper, the wrapper's own arguments after its `--`. The
worker keeps the wrapper prefix up to `--`, so it runs on the same account; a
wrapper without `--` fails closed unless --without wrapper drops it. Positional
arguments (main's own prompt) never carry over. A worker of a different kind
inherits nothing else. Session, resume, print, prompt, credential-bearing and
unrecognised flags are dropped and named. Setup-flag values are never printed.

--start NAME splits a pane of the root's tab to the right with
`herdr-app do pane.split --pane <explicit pane> --argv <json>` (never
terminal.open, terminal.keep or `hc run`, which follow the focused pane or die
with their parent), labels the new terminal, puts focus back where it was,
and returns once the worker reports an idle or done status.

Exit codes:
    0  profile resolved (with --start: the worker also reported ready)
    1  error: unreadable main kind without --kind, unreadable same-kind argv
       without --without flags, an unsplittable wrapper, unmapped
       --model/--thinking, or a failed start
    2  usage error
    3  with --start: the worker booted into a dialog (blocked); a human is needed

Usage:
    launch_profile.py [--root T] [--main-model M] [--main-thinking T]
                      [--kind K] [--model M] [--thinking T]
                      [--without bypass|flags|wrapper]
                      [--start NAME [--role worker|main] [--cwd DIR] [--timeout SECONDS]]
                      [-- native flags...]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

import hclib
from hclib import LABEL, HcError

SWITCH, VALUE, VALUES = 0, 1, "+"  # flag arity; VALUES = tokens up to the next flag


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



def binary_name(token: str) -> str:
    return hclib.binary_name(token)


def harness_index(argv: list[str], spec: dict) -> int | None:
    """Index of the harness binary: argv0, or the script a node/bun interpreter runs."""
    idx = [i for i, tok in enumerate(argv) if binary_name(tok) in spec["binaries"]]
    if idx and (idx[0] == 0 or (idx[0] == 1 and binary_name(argv[0]) in {"node", "bun"})):
        return idx[0]
    return None


WRAPPER_ERR = "main runs through the wrapper"


def read_launch(rec: dict, spec: dict, drop_wrapper: bool) -> tuple[dict | None, str, str]:
    """(launch, error, warning). launch = {mode, prefix, tail}: the worker runs prefix + args."""
    top = [a for a in rec.get("argv") or [] if isinstance(a, str)] if isinstance(rec.get("argv"), list) else []
    if top[:3] == hclib.FOLDER_WRAPPER and len(top) >= 5:
        top = top[4:]  # a terminal --start made (a HANDOFF successor): judge the worker argv inside
    fg = hclib.foreground_argv(rec)
    fi = harness_index(fg, spec) if fg else None
    direct = not top or harness_index(top, spec) is not None or binary_name(top[0]) in hclib.SHELLS
    warning = ""
    if not direct and not drop_wrapper:
        if "--" in top:
            cut = top.index("--")
            return {"mode": "wrapper", "prefix": top[: cut + 1], "tail": top[cut + 1 :]}, "", ""
        return None, (f"{WRAPPER_ERR} '{binary_name(top[0])}' with no '--' separator, so its "
                      "own arguments cannot be told apart from the harness's. Pass --without wrapper to "
                      "launch the harness directly (it may then use another account)"), ""
    if not direct:
        warning = (f"wrapper '{binary_name(top[0])}' dropped (--without wrapper): the worker runs the harness "
                   "directly and may use another account or config")
    if fi is None:
        return None, ("the root's foreground process is not running "
                      f"{'/'.join(spec['binaries'])} (hc get foreground.argv)"), warning
    return {"mode": "direct", "prefix": fg[: fi + 1], "tail": fg[fi + 1 :]}, "", warning


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
    """Return (profile, the worker's full argv, error)."""
    root = args.root
    try:
        rec = hclib.get(root)
        status, main_kind = hclib.classify(rec)
        err = "" if main_kind and status not in ("no-agent", "exited") else f"no agent runs in {root} ({status})"
    except HcError as exc:
        rec, main_kind, err = {}, "", str(exc)
    main_kind = main_kind if not err else None
    if main_kind is None:
        if not args.kind:
            return None, [], (f"cannot read the main agent's harness from terminal {root} ({err}). Pass "
                              "--kind KIND --without flags for an explicit reduced-inheritance worker, or "
                              f"check 'hc get {root}'.")
        if "flags" not in args.without:
            return None, [], (f"cannot verify whether worker kind '{args.kind}' matches the main agent's "
                              f"unreadable harness ({err}). Pass --without flags to explicitly start without "
                              "inheriting the main profile.")
    kind = args.kind or main_kind
    inherited = main_kind is not None and kind == main_kind
    spec = KINDS.get(kind)
    bin_spec = spec or {"binaries": (kind,)}
    warnings: list[str] = []
    if main_kind is None:
        warnings.append(f"main agent's harness unreadable ({err}); model, thinking level and setup flags "
                        "not inherited")
    launch, lerr, lwarn = (read_launch(rec, bin_spec, "wrapper" in args.without) if inherited
                           else ({"mode": "bare", "prefix": [bin_spec["binaries"][0]], "tail": []}, "", ""))
    if lwarn:
        warnings.append(lwarn)
    if launch is None and lerr.startswith(WRAPPER_ERR):
        return None, [], lerr  # the account a wrapper picks is never guessed, even with --without flags

    if spec is None:
        if args.model or args.thinking:
            return None, [], (f"no model/thinking flag mapping for kind '{kind}'. Pass its native flag after "
                              f"'--' instead (check '{kind} --help').")
        if inherited:
            warnings.append(f"no flag table for kind '{kind}': only the kind is inherited, not model, "
                            "thinking level or launch flags")
        prefix = launch["prefix"] if launch else [kind]
        if launch is None:
            warnings.append(f"root launch unreadable ({lerr}); starting bare '{kind}' from PATH")
        profile = {
            "kind": kind, "main_kind": main_kind, "inherited": inherited,
            "launch": {"mode": launch["mode"] if launch else "bare", "via": binary_name(prefix[0])},
            "model": {"value": "", "source": "not mapped"}, "thinking": {"value": "", "source": "not mapped"},
            "flags": [], "flags_source": "not mapped", "without": sorted(set(args.without)),
            "explicit": [stem(t) for t in native if is_flag(t)],
            "bypass": [], "dropped": [], "warnings": warnings, "argc": len(native),
        }
        return profile, [*prefix, *native], ""

    root_groups: list[dict] = []
    dropped: list[str] = []
    flags_source = "not inherited"
    if inherited:
        if launch is None:
            if "flags" not in args.without:
                return None, [], (f"cannot safely inherit the main agent's setup flags ({lerr}). Pass "
                                  "--without flags to explicitly start with reduced inheritance.")
            warnings.append(f"root launch flags unreadable ({lerr}); setup flag inheritance explicitly disabled")
            flags_source = "opted out"
            launch = {"mode": "bare", "prefix": [spec["binaries"][0]], "tail": []}
        else:
            root_groups, dropped = parse_groups(spec, launch["tail"], strict=True)
            flags_source = "wrapper argv" if launch["mode"] == "wrapper" else "root argv"

    explicit_groups, _ = parse_groups(spec, native, strict=False)
    env = None
    env_name = spec.get("thinking_env")
    if inherited and env_name and os.environ.get("HC_TERMINAL_ID") == root and os.environ.get(env_name):
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
        "launch": {"mode": launch["mode"], "via": binary_name(launch["prefix"][0])},
        "model": {"value": model, "source": model_src},
        "thinking": {"value": thinking, "source": thinking_src},
        "flags": sorted({stem(g["name"]) for g in kept if g["key"] not in live_keys}),
        "flags_source": flags_source, "without": sorted(set(args.without)),
        "explicit": [stem(g["name"]) for g in explicit_groups if g["name"]],
        "bypass": [label for g in kept if (label := bypass_label(spec, g))],
        "dropped": dropped, "warnings": warnings, "argc": len(argv),
    }
    return profile, [*launch["prefix"], *argv], ""


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



def unique_name(root: hclib.Root, name: str) -> str:
    members = root.panes()
    taken = [r for r in hclib.ls_labeled(f"{LABEL}.name={name}", f"{LABEL}.tab={root.tab}")
             if r.get("address") in members]
    return name if not taken else f"{name[:21]}-{int(time.time())}"


def split_target(root: hclib.Root) -> str:
    """The newest hc-agent pane in the root's tab, else root's own pane.

    The app reports no layout geometry, so the rightmost pane cannot be read.
    Splitting the last spawned pane to the right keeps spawn order left to right.
    """
    members = root.panes()
    newest, newest_ms = root.pane, -1
    for row in hclib.ls_labeled(f"{LABEL}.tab={root.tab}"):
        addr = row.get("address")
        if addr not in members or addr == root.addr:
            continue
        created = hclib.get(addr).get("created_ms") or 0
        if created > newest_ms:
            newest, newest_ms = members[addr], created
    return newest


def start_worker(args, profile: dict, argv: list[str]) -> int:
    if not hclib.NAME_RE.match(args.start) or hclib.ADDRESS_RE.match(args.start):
        print(f"Error: worker name '{args.start}' must match [a-z][a-z0-9_-]{{0,31}} and must not look like "
              "a terminal address (t7, t2x).", file=sys.stderr)
        return 2
    root = hclib.resolve_root(args.root)
    name = unique_name(root, args.start)
    if name != args.start:
        print(f"note: '{args.start}' is taken in this tab; using '{name}'", file=sys.stderr)
    cwd = os.path.abspath(args.cwd or (root.rec.get("foreground") or {}).get("cwd") or root.rec.get("cwd")
                          or os.getcwd())
    command = list(argv)
    if os.path.isfile("/bin/sh"):
        command = [*hclib.FOLDER_WRAPPER, cwd, *command]
    target = split_target(root)
    prior = hclib.app_status().get("focused_pane") or root.pane
    term = pane = ""
    restored = False
    try:
        made = hclib.app_do("pane.split", direction="right", pane=target, argv=json.dumps(command))
        term, pane = made.get("terminal") or "", made.get("pane") or ""
        if not term or not pane:
            raise HcError(f"pane.split returned no terminal/pane ({json.dumps(made)[:200]}); inspect "
                          "'herdr-app ls' before retrying.")
        hclib.label(term, {f"{LABEL}.role": args.role, f"{LABEL}.name": name,
                           f"{LABEL}.space": root.space, f"{LABEL}.tab": root.tab})
    except HcError as err:
        where = f" Terminal {term} (pane {pane}) is an orphan; ask before closing it." if term else ""
        print(f"Error: {err}{where}", file=sys.stderr)
        return 1
    finally:
        try:
            hclib.app_do("pane.focus", pane=prior)
            restored = hclib.app_status().get("focused_pane") == prior
        except HcError as err:
            print(f"warning: could not put focus back on pane {prior}: {err}", file=sys.stderr)
        if not restored:
            print(f"warning: focus is not back on pane {prior}; the split moved it. Tell the user before "
                  "they type.", file=sys.stderr)
    outcome, rec = hclib.poll_ready(term, args.timeout)
    report = {"name": name, "terminal": term, "pane": pane, "split_from": target, "kind": profile["kind"],
              "outcome": outcome, "cwd": (rec.get("foreground") or {}).get("cwd"), "focus_restored": restored}
    if report["cwd"] and os.path.abspath(report["cwd"]) != cwd:
        print(f"warning: worker '{name}' runs in {report['cwd']}, not {cwd}", file=sys.stderr)
    if outcome == "ready":
        print(json.dumps(report))
        return 0
    st = rec.get("status") if isinstance(rec.get("status"), dict) else {}
    if outcome == "blocked":
        print(json.dumps(report))
        print(f"Error: worker '{name}' booted into a dialog: {(st or {}).get('msg') or 'see the pane'}. Show it "
              f"with 'herdr-app do agent.focus --terminal {term}' and let the human answer; never answer it "
              "for them.", file=sys.stderr)
        return 3
    reason = ("its program exited" if outcome == "exited" else
              f"it reported error: {(st or {}).get('msg') or 'see the pane'}" if outcome == "error" else
              f"no idle status within {args.timeout:.0f}s (a dialog may be up, or the CLI does not report "
              "OSC 7501 status)")
    print(f"Error: worker '{name}' did not start: {reason}. Terminal {term} (pane {pane}) is an orphan; read "
          f"it with 'hc read {term} --lines 40' and ask before closing it.", file=sys.stderr)
    return 1


def main(argv: list[str]) -> int:
    own, native = (argv[: argv.index("--")], argv[argv.index("--") + 1 :]) if "--" in argv else (argv, [])
    parser = argparse.ArgumentParser(prog="launch_profile.py", allow_abbrev=False,
                                     description="Resolve the inherited launch profile for a Herdr app worker; "
                                                 "--start launches it.")
    parser.add_argument("--root", default=os.environ.get("HC_TERMINAL_ID", ""),
                        help="the main agent's terminal (default: $HC_TERMINAL_ID)")
    parser.add_argument("--main-model", default="", help="the main agent's own exact model ID (self-report)")
    parser.add_argument("--main-thinking", default="", help="the main agent's own thinking level (self-report)")
    parser.add_argument("--kind", default="", help="worker kind the user named; a different kind inherits nothing else")
    parser.add_argument("--model", default="", help="worker model the user named")
    parser.add_argument("--thinking", default="", help="worker thinking level the user named")
    parser.add_argument("--without", action="append", choices=("bypass", "flags", "wrapper"), default=[],
                        help="drop inherited permission-bypass flags, every inherited setup flag, or main's wrapper")
    parser.add_argument("--start", metavar="NAME", default="", help="launch worker NAME on the profile")
    parser.add_argument("--role", choices=("worker", "main"), default="worker",
                        help="label role: main for a HANDOFF successor, which teardown never closes")
    parser.add_argument("--cwd", default="", help="worker folder (with --start; default: root's folder)")
    parser.add_argument("--timeout", type=float, default=60.0, help="readiness timeout in seconds (default 60)")
    args = parser.parse_args(own)
    if not args.root:
        parser.error("--root is empty: run inside a Herdr app terminal ($HC_TERMINAL_ID), or pass the address")
    if os.environ.get("HERDR_ENV") == "1":
        print("Error: HERDR_ENV=1: this is a Herdr TUI pane; use the herdr-agent skill instead.", file=sys.stderr)
        return 1
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
    except HcError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
