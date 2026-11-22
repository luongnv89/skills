const http = require("node:http");

const port = Number(process.env.PORT || 3100);
const todos = [];
let nextId = 1;

function send(res, status, body) {
  res.writeHead(status, { "content-type": "application/json" });
  res.end(JSON.stringify(body));
}

const server = http.createServer((req, res) => {
  if (req.method === "GET" && req.url === "/health") {
    send(res, 200, { status: "ok" });
    return;
  }
  if (req.method === "GET" && req.url === "/api/todos") {
    send(res, 200, todos);
    return;
  }
  if (req.method === "POST" && req.url === "/api/todos") {
    let raw = "";
    req.on("data", (chunk) => (raw += chunk));
    req.on("end", () => {
      let input;
      try {
        input = JSON.parse(raw);
      } catch {
        send(res, 400, { error: "invalid JSON" });
        return;
      }
      if (typeof input.title !== "string" || input.title.trim() === "") {
        send(res, 400, { error: "title is required" });
        return;
      }
      const todo = { id: nextId++, title: input.title.trim(), done: false };
      todos.push(todo);
      send(res, 201, todo);
    });
    return;
  }
  send(res, 404, { error: "not found" });
});

server.listen(port, () => {
  console.log(`todo-api listening on http://localhost:${port}`);
});
