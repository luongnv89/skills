# Notepad

A one-page notepad. Type a note, press **Add**, and it appears in the list with a running count. Press `/` anywhere to jump to the input.

## Run

```bash
npm start
```

It listens on port 4173 (set `PORT` to change it). `GET /health` returns `ok` once the server is up. `/about` describes the app; any other path is a 404 page.
