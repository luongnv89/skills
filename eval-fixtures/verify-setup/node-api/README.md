# todo-api

An in-memory todo API. Data lives only in the running process, so every start begins empty.

## Run

```bash
npm start
```

Listens on port 3100 (set `PORT` to change it).

## Endpoints

| Method | Path | Result |
|---|---|---|
| GET | `/health` | `200 {"status":"ok"}` |
| GET | `/api/todos` | `200` and the list of todos |
| POST | `/api/todos` with `{"title":"..."}` | `201` and the new todo with its `id` and `"done": false`; `400 {"error":"title is required"}` without a title |
