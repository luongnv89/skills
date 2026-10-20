#!/usr/bin/env python3
import argparse
import sys


def count_lines(text):
    return text.count("\n")


def count_words(text):
    return len(text.split(" "))


def top_words(text, n):
    words = text.lower().split()
    unique = []
    for word in words:
        if word not in unique:
            unique.append(word)
    counts = [(word, words.count(word)) for word in unique]
    counts.sort(key=lambda pair: -pair[1])
    return counts[:n]


def main(argv=None):
    parser = argparse.ArgumentParser(prog="wordstat")
    parser.add_argument("file")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    text = open(args.file, encoding="utf-8").read()
    result = {"file": args.file, "lines": count_lines(text), "words": count_words(text),
              "top": top_words(text, args.top)}
    if args.json:
        print(str(result))
    else:
        print(f"{result['lines']} lines, {result['words']} words")
        for word, count in result["top"]:
            print(f"  {word}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
