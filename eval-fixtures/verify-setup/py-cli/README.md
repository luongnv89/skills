# wordcount

Count lines, words and characters in a text file.

## Usage

Run it from the repository root without installing:

```bash
python3 -m wordcount count tests/fixtures/sample.txt
# 2 lines, 9 words, 44 chars

python3 -m wordcount count tests/fixtures/sample.txt --json
# {"lines": 2, "words": 9, "chars": 44}
```

A missing file prints `wordcount: <path>: no such file` and exits with status 2.
