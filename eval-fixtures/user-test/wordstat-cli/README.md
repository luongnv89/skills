# wordstat

Count lines and words in a text file and list its most frequent words.

## Usage

```bash
python3 wordstat.py notes.txt              # "12 lines, 230 words" + top 5 words
python3 wordstat.py notes.txt --top 10     # top 10 words
python3 wordstat.py notes.txt --json       # machine-readable output for scripts
```

Works on files of any size. Requires Python 3.8+ and nothing else.

## Test

```bash
python3 -m unittest discover -s tests -q
```
