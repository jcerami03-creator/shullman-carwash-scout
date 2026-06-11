const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const root = __dirname;
const port = Number(process.env.PORT || 8080);
const host = process.env.HOST || "127.0.0.1";
const username = process.env.SCOUT_USER || "shullman";
const password = process.env.SCOUT_PASSWORD || "";

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".pdf": "application/pdf",
  ".png": "image/png",
  ".txt": "text/plain; charset=utf-8",
  ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
};

function timingSafeEqualString(left, right) {
  const a = Buffer.from(String(left));
  const b = Buffer.from(String(right));
  if (a.length !== b.length) return false;
  return cryptoSafeCompare(a, b);
}

function cryptoSafeCompare(a, b) {
  try {
    return require("node:crypto").timingSafeEqual(a, b);
  } catch {
    return false;
  }
}

function authorized(req) {
  if (!password) return true;
  const header = req.headers.authorization || "";
  if (!header.startsWith("Basic ")) return false;
  const decoded = Buffer.from(header.slice(6), "base64").toString("utf8");
  const splitAt = decoded.indexOf(":");
  if (splitAt === -1) return false;
  const user = decoded.slice(0, splitAt);
  const pass = decoded.slice(splitAt + 1);
  return timingSafeEqualString(user, username) && timingSafeEqualString(pass, password);
}

function sendAuth(res) {
  res.writeHead(401, {
    "WWW-Authenticate": 'Basic realm="Shullman Carwash Scout"',
    "Content-Type": "text/plain; charset=utf-8",
  });
  res.end("Login required.");
}

function safePath(urlPath) {
  const pathname = decodeURIComponent(urlPath.split("?")[0].split("#")[0]);
  const requested = pathname === "/" ? "/index.html" : pathname;
  const resolved = path.resolve(root, `.${requested}`);
  if (!resolved.startsWith(root)) return "";
  return resolved;
}

const server = http.createServer((req, res) => {
  if (!authorized(req)) {
    sendAuth(res);
    return;
  }

  const filePath = safePath(req.url || "/");
  if (!filePath) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }

  fs.stat(filePath, (statError, stat) => {
    if (statError || !stat.isFile()) {
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Not found");
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, {
      "Content-Type": mimeTypes[ext] || "application/octet-stream",
      "Content-Length": stat.size,
      "Cache-Control": ext === ".html" ? "no-cache" : "public, max-age=300",
      "X-Content-Type-Options": "nosniff",
    });
    fs.createReadStream(filePath).pipe(res);
  });
});

server.listen(port, host, () => {
  console.log(`Carwash Scout running on ${host}:${port}`);
});
