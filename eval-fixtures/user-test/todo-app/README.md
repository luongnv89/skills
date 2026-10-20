# Todo

A small todo list: add todos, tick them off, search, filter, see stats, and email the open
list to your team.

## Run

```bash
python3 server.py
```

Then open http://127.0.0.1:8765/ (set `PORT` to use another port). No dependencies beyond
Python 3.8+.

## Features

- Add a todo with the field at the top (press Enter or click Add).
- Tick a todo to mark it done; × deletes it.
- Search filters the list as you type; All, Active and Done filter by status.
- Double-click a todo to rename it.
- The footer shows how many todos are left.
- Stats shows how many todos are done and open.
- "Email list to team" sends the open todos to everyone on your team.

## Test

```bash
python3 -m unittest discover -s tests -q
```
