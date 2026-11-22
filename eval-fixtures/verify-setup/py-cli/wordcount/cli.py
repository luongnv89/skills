import argparse
import sys

from wordcount import __version__


def count(text):
    return len(text.splitlines()), len(text.split()), len(text)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="wordcount", description="Count lines, words and characters.")
    parser.add_argument("--version", action="version", version=f"wordcount {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    count_cmd = sub.add_parser("count", help="print lines, words and characters of a file")
    count_cmd.add_argument("path")
    count_cmd.add_argument("--json", action="store_true", help="print JSON instead of a table")
    args = parser.parse_args(argv)

    try:
        with open(args.path, encoding="utf-8") as handle:
            lines, words, chars = count(handle.read())
    except FileNotFoundError:
        print(f"wordcount: {args.path}: no such file", file=sys.stderr)
        return 2
    if args.json:
        print(f'{{"lines": {lines}, "words": {words}, "chars": {chars}}}')
    else:
        print(f"{lines} lines, {words} words, {chars} chars")
    return 0
