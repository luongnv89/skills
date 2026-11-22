const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const port = Number(process.env.PORT || 4173);
const page = fs.readFileSync(path.join(__dirname, "index.html"));

const server = http.createServer((req, res) => {
  if (req.url === "/health") {
    res.writeHead(200, { "content-type": "text/plain" });
    res.end("ok");
    return;
  }
  if (req.url === "/" || req.url === "/index.html") {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    res.end(page);
    return;
  }
  if (req.url === "/about") {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    res.end("<!doctype html><title>About</title><h1>About Notepad</h1><p>Notes stay in this tab.</p>");
    return;
  }
  res.writeHead(404, { "content-type": "text/html; charset=utf-8" });
  res.end("<!doctype html><title>Not found</title><h1>Page not found</h1>");
});

server.listen(port, () => {
  console.log(`notepad listening on http://localhost:${port}`);
});
