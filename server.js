const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const root = __dirname;
const port = Number(process.env.PORT || 8080);
const host = process.env.HOST || "127.0.0.1";
const username = process.env.SCOUT_USER || "shullman";
const password = process.env.SCOUT_PASSWORD || "";
const uploadRoot = path.resolve(process.env.UPLOAD_DIR || path.join(root, "runtime-uploads"));
const uploadMetaPath = path.join(uploadRoot, "metadata.json");
const manualRecordsPath = path.join(uploadRoot, "manual-records.json");
const maxUploadBytes = Number(process.env.UPLOAD_MAX_BYTES || 100 * 1024 * 1024);

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
  ".webp": "image/webp",
  ".doc": "application/msword",
  ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ".xls": "application/vnd.ms-excel",
  ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  ".zip": "application/zip",
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

function sendJson(res, status, payload) {
  const body = JSON.stringify(payload, null, 2);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
    "Cache-Control": "no-cache",
    "X-Content-Type-Options": "nosniff",
  });
  res.end(body);
}

function sendText(res, status, text) {
  res.writeHead(status, { "Content-Type": "text/plain; charset=utf-8" });
  res.end(text);
}

function ensureUploadRoot() {
  fs.mkdirSync(uploadRoot, { recursive: true });
}

function readUploadMetadata() {
  try {
    ensureUploadRoot();
    const parsed = JSON.parse(fs.readFileSync(uploadMetaPath, "utf8"));
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeUploadMetadata(items) {
  ensureUploadRoot();
  fs.writeFileSync(uploadMetaPath, JSON.stringify(items, null, 2), "utf8");
}

function readManualRecords() {
  try {
    ensureUploadRoot();
    const parsed = JSON.parse(fs.readFileSync(manualRecordsPath, "utf8"));
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeManualRecords(records) {
  ensureUploadRoot();
  fs.writeFileSync(manualRecordsPath, JSON.stringify(records, null, 2), "utf8");
}

function cleanText(value, maxLength = 8000) {
  return String(value == null ? "" : value).replace(/\s+/g, " ").trim().slice(0, maxLength);
}

function cleanRecordPayload(payload) {
  const record = {};
  const allowed = [
    "name",
    "year",
    "market",
    "state",
    "asking_price",
    "sales",
    "ebitda",
    "cars_per_year",
    "acres",
    "phone",
    "website",
    "research_url",
    "maps_url",
    "traffic_count",
    "note",
    "source",
    "full_text",
  ];
  allowed.forEach((key) => {
    if (payload && payload[key] != null) record[key] = cleanText(payload[key], key === "full_text" || key === "note" ? 12000 : 1000);
  });
  const hasContent = Object.values(record).some(Boolean);
  if (!hasContent) return null;
  record.name = record.name || record.market || "New car wash listing";
  record.source = record.source || "Admin Added Listing";
  record.added_at = new Date().toISOString();
  record.id = `manual-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return record;
}

function readJsonBody(req, maxBytes, callback) {
  const chunks = [];
  let total = 0;
  req.on("data", (chunk) => {
    total += chunk.length;
    if (total > maxBytes) {
      req.destroy();
      return;
    }
    chunks.push(chunk);
  });
  req.on("end", () => {
    if (total > maxBytes) {
      callback(new Error("Request is too large."));
      return;
    }
    try {
      const text = Buffer.concat(chunks).toString("utf8") || "{}";
      callback(null, JSON.parse(text));
    } catch {
      callback(new Error("Could not read the submitted record."));
    }
  });
  req.on("error", () => callback(new Error("Request failed.")));
}

function cleanFilename(filename) {
  const ext = path.extname(filename || "").toLowerCase();
  const base = path.basename(filename || "upload", ext).replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "") || "upload";
  return `${base}${ext || ".bin"}`;
}

function uploadDocForFile(item) {
  const isImage = /^image\//i.test(item.mime || "") || /\.(?:png|jpe?g|webp)$/i.test(item.filename);
  const url = `/uploads/${encodeURIComponent(item.storedName)}`;
  return {
    title: item.title || item.filename,
    file_name: item.filename,
    category: isImage ? "Image Scans" : "Deal Records",
    group: isImage ? "Admin Phone Uploads" : "Admin Uploaded Documents",
    pdf_url: url,
    text_url: "",
    page_count: 1,
    evidence_page_count: 0,
    evidence_row_count: 0,
    pages: [],
    evidence_rows: [],
    uploaded_at: item.uploadedAt,
    gallery_images: isImage
      ? [
          {
            page: "1",
            group: "Admin Phone Uploads",
            interpretation: "Image uploaded through the admin page. Review visually; OCR/AI extraction requires the processing worker.",
            image_url: url,
            pdf_page_url: url,
          },
        ]
      : [],
  };
}

function parseMultipart(buffer, contentType) {
  const boundaryMatch = String(contentType || "").match(/boundary=(?:"([^"]+)"|([^;]+))/i);
  if (!boundaryMatch) return [];
  const boundary = Buffer.from(`--${boundaryMatch[1] || boundaryMatch[2]}`);
  const parts = [];
  let start = buffer.indexOf(boundary);
  while (start !== -1) {
    start += boundary.length;
    if (buffer[start] === 45 && buffer[start + 1] === 45) break;
    if (buffer[start] === 13 && buffer[start + 1] === 10) start += 2;
    const headerEnd = buffer.indexOf(Buffer.from("\r\n\r\n"), start);
    if (headerEnd === -1) break;
    const header = buffer.slice(start, headerEnd).toString("utf8");
    let bodyStart = headerEnd + 4;
    let next = buffer.indexOf(boundary, bodyStart);
    if (next === -1) break;
    let bodyEnd = next;
    if (buffer[bodyEnd - 2] === 13 && buffer[bodyEnd - 1] === 10) bodyEnd -= 2;
    const name = (header.match(/name="([^"]+)"/i) || [])[1] || "";
    const filename = (header.match(/filename="([^"]*)"/i) || [])[1] || "";
    const mime = (header.match(/content-type:\s*([^\r\n]+)/i) || [])[1] || "application/octet-stream";
    parts.push({ name, filename, mime, data: buffer.slice(bodyStart, bodyEnd) });
    start = next;
  }
  return parts;
}

function handleApiUploads(req, res) {
  if (req.method === "GET") {
    const uploads = readUploadMetadata().map(uploadDocForFile);
    sendJson(res, 200, { uploads });
    return;
  }

  if (req.method !== "POST") {
    sendJson(res, 405, { error: "Method not allowed" });
    return;
  }

  const chunks = [];
  let total = 0;
  req.on("data", (chunk) => {
    total += chunk.length;
    if (total > maxUploadBytes) {
      req.destroy();
      return;
    }
    chunks.push(chunk);
  });
  req.on("end", () => {
    if (total > maxUploadBytes) {
      sendJson(res, 413, { error: "Upload is too large." });
      return;
    }

    const body = Buffer.concat(chunks);
    const parts = parseMultipart(body, req.headers["content-type"]);
    const files = parts.filter((part) => part.filename && part.data.length);
    if (!files.length) {
      sendJson(res, 400, { error: "No file was uploaded." });
      return;
    }

    ensureUploadRoot();
    const metadata = readUploadMetadata();
    const saved = files.map((file) => {
      const original = cleanFilename(file.filename);
      const storedName = `${new Date().toISOString().replace(/[:.]/g, "-")}-${original}`;
      const target = path.join(uploadRoot, storedName);
      fs.writeFileSync(target, file.data);
      const item = {
        id: storedName,
        filename: original,
        storedName,
        mime: file.mime,
        size: file.data.length,
        uploadedAt: new Date().toISOString(),
        title: original.replace(/\.[^.]+$/, ""),
      };
      metadata.unshift(item);
      return uploadDocForFile(item);
    });
    writeUploadMetadata(metadata);
    sendJson(res, 201, { uploads: saved });
  });
  req.on("error", () => sendJson(res, 500, { error: "Upload failed." }));
}

function handleManualRecords(req, res) {
  if (req.method === "GET") {
    sendJson(res, 200, { records: readManualRecords() });
    return;
  }

  if (req.method !== "POST") {
    sendJson(res, 405, { error: "Method not allowed" });
    return;
  }

  readJsonBody(req, 2 * 1024 * 1024, (error, payload) => {
    if (error) {
      sendJson(res, 400, { error: error.message });
      return;
    }
    const incoming = Array.isArray(payload?.records) ? payload.records : [payload?.record || payload];
    const cleaned = incoming.map(cleanRecordPayload).filter(Boolean);
    if (!cleaned.length) {
      sendJson(res, 400, { error: "Add at least a name, address, URL, or note." });
      return;
    }
    const records = readManualRecords();
    cleaned.reverse().forEach((record) => records.unshift(record));
    writeManualRecords(records);
    sendJson(res, 201, { records: cleaned, total: records.length });
  });
}

function serveUpload(req, res) {
  const pathname = decodeURIComponent((req.url || "").split("?")[0]);
  const relative = pathname.replace(/^\/uploads\/?/, "");
  const filePath = path.resolve(uploadRoot, relative);
  if (!filePath.startsWith(uploadRoot)) {
    sendText(res, 403, "Forbidden");
    return;
  }
  fs.stat(filePath, (error, stat) => {
    if (error || !stat.isFile()) {
      sendText(res, 404, "Not found");
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, {
      "Content-Type": mimeTypes[ext] || "application/octet-stream",
      "Content-Length": stat.size,
      "Cache-Control": "public, max-age=300",
      "X-Content-Type-Options": "nosniff",
    });
    fs.createReadStream(filePath).pipe(res);
  });
}

const server = http.createServer((req, res) => {
  if (!authorized(req)) {
    sendAuth(res);
    return;
  }

  if ((req.url || "").startsWith("/api/uploads")) {
    handleApiUploads(req, res);
    return;
  }

  if ((req.url || "").startsWith("/api/manual-records")) {
    handleManualRecords(req, res);
    return;
  }

  if ((req.url || "").startsWith("/uploads/")) {
    serveUpload(req, res);
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
