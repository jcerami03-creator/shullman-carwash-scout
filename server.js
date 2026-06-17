const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const root = __dirname;
const port = Number(process.env.PORT || 8080);
const host = process.env.HOST || "127.0.0.1";
const username = process.env.SCOUT_USER || "shullman";
const password = process.env.SCOUT_PASSWORD || "";
const openaiApiKey = process.env.OPENAI_API_KEY || "";
const openaiVisionModel = process.env.OPENAI_VISION_MODEL || "gpt-4.1-mini";
const googlePlacesApiKey = process.env.GOOGLE_PLACES_API_KEY || process.env.GOOGLE_MAPS_API_KEY || "";
const trafficApiUrl = process.env.TRAFFIC_API_URL || "";
const uploadRoot = path.resolve(process.env.UPLOAD_DIR || path.join(root, "runtime-uploads"));
const uploadMetaPath = path.join(uploadRoot, "metadata.json");
const manualRecordsPath = path.join(uploadRoot, "manual-records.json");
const maxUploadBytes = Number(process.env.UPLOAD_MAX_BYTES || 100 * 1024 * 1024);

// --- Permanent storage (Upstash Redis REST) ---
// When these env vars are set, manual records are saved to Upstash so they
// survive Render restarts/redeploys. If not set, falls back to the local file.
const upstashUrl = process.env.UPSTASH_REDIS_REST_URL || "";
const upstashToken = process.env.UPSTASH_REDIS_REST_TOKEN || "";
const usePersistentStore = Boolean(upstashUrl && upstashToken);
const manualRecordsKey = process.env.MANUAL_RECORDS_KEY || "manual-records";
let manualRecordsCache = [];

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
  ".docx": "a
