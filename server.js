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
const demographicsApiUrl = process.env.DEMOGRAPHICS_API_URL || "";
const maintenanceSecret = process.env.MAINTENANCE_SECRET || "";
const censusAcsYear = process.env.CENSUS_ACS_YEAR || "2024";
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
let censusPopulationCache = null;
const censusGeocodeCache = new Map();
const censusRingCache = new Map();
const placeGeocodeCache = new Map();

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

function maintenanceAuthorized(req) {
  if (!maintenanceSecret) return false;
  const supplied = req.headers["x-scout-maintenance-secret"] || "";
  return timingSafeEqualString(String(supplied), maintenanceSecret);
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

async function redisCommand(args) {
  const response = await fetch(upstashUrl, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${upstashToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(args),
  });
  if (!response.ok) {
    throw new Error(`Upstash ${response.status}: ${await response.text()}`);
  }
  const data = await response.json();
  return data.result;
}

function readManualRecordsFile() {
  try {
    ensureUploadRoot();
    const parsed = JSON.parse(fs.readFileSync(manualRecordsPath, "utf8"));
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

// Dedup key: prefer the stable BizBuySell listing id (?q=), then the full
// research url, then name|state. Keeps saves idempotent so retries/re-runs
// can never create duplicate listings.
function recordKey(r) {
  const url = String((r && r.research_url) || "").toLowerCase();
  const m = url.match(/[?&]q=(\d+)/);
  if (m) return "q:" + m[1];
  if (url) return "u:" + url;
  const name = String((r && r.name) || "").toLowerCase().replace(/[^a-z0-9]/g, "");
  const state = String((r && r.state) || "").toLowerCase();
  return "n:" + name + "|" + state;
}

function dedupeRecords(records) {
  const seen = new Set();
  const out = [];
  for (const r of Array.isArray(records) ? records : []) {
    const key = recordKey(r);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(r);
  }
  return out;
}

// Hydrate the in-memory cache once at startup (from Upstash if configured).
async function loadManualRecords() {
  let records = [];
  if (usePersistentStore) {
    try {
      const raw = await redisCommand(["GET", manualRecordsKey]);
      records = raw ? JSON.parse(raw) : [];
    } catch (error) {
      console.error("Upstash load failed, using local file:", error.message);
      records = readManualRecordsFile();
    }
  } else {
    records = readManualRecordsFile();
    console.log("Persistent store not configured - using local file (temporary).");
  }
  const deduped = dedupeRecords(records);
  manualRecordsCache = deduped;
  // One-time cleanup: if old duplicates exist, persist the deduped list back.
  if (usePersistentStore && deduped.length !== records.length) {
    try {
      await redisCommand(["SET", manualRecordsKey, JSON.stringify(deduped)]);
      console.log(`Cleaned ${records.length - deduped.length} duplicate record(s).`);
    } catch (error) {
      console.error("Dedup cleanup failed:", error.message);
    }
  }
  console.log(`Loaded ${deduped.length} manual record(s).`);
  return manualRecordsCache;
}

function readManualRecords() {
  return manualRecordsCache;
}

async function writeManualRecords(records) {
  const deduped = dedupeRecords(records);
  manualRecordsCache = deduped;
  // Keep a local file copy too (helps local dev; harmless on Render)
  try {
    ensureUploadRoot();
    fs.writeFileSync(manualRecordsPath, JSON.stringify(deduped, null, 2), "utf8");
  } catch {
    // ephemeral/read-only filesystem - fine when Upstash is the source of truth
  }
  if (usePersistentStore) {
    await redisCommand(["SET", manualRecordsKey, JSON.stringify(deduped)]);
  }
}

function cleanText(value, maxLength = 8000) {
  return String(value == null ? "" : value).replace(/\s+/g, " ").trim().slice(0, maxLength);
}

function isMissingValue(value) {
  const clean = cleanText(value, 240).toLowerCase();
  return (
    !clean ||
    clean === "-" ||
    clean === "n/a" ||
    clean === "na" ||
    clean === "none" ||
    clean === "unknown" ||
    clean === "not provided" ||
    clean === "not listed" ||
    clean === "not listed in file" ||
    clean === "not available" ||
    clean.includes("needs source")
  );
}

function hasCompleteDemographics(record) {
  return ["population_1_mile", "population_3_mile", "population_5_mile"].every((key) => !isMissingValue(record[key]));
}

function moneyToNumber(value) {
  const raw = cleanText(value, 120).toLowerCase().replace(/,/g, "");
  const match = raw.match(/([0-9]+(?:\.[0-9]+)?)\s*(mm|m|million|k|thousand)?/);
  if (!match) return 0;
  let number = Number(match[1]);
  if (!Number.isFinite(number)) return 0;
  const suffix = match[2] || "";
  if (["m", "mm", "million"].includes(suffix)) number *= 1_000_000;
  else if (["k", "thousand"].includes(suffix)) number *= 1_000;
  else if (raw.includes("$") && number < 1000 && /\.\d/.test(match[1])) number *= 1_000_000;
  return Math.round(number);
}

function numericValue(value) {
  const raw = cleanText(value, 120).replace(/,/g, "");
  const match = raw.match(/([0-9]+(?:\.[0-9]+)?)/);
  return match ? Number(match[1]) : 0;
}

function formatMoneyShort(value) {
  const number = typeof value === "number" ? value : moneyToNumber(value);
  if (!number) return "";
  if (number >= 1_000_000) return `$${(number / 1_000_000).toFixed(number >= 10_000_000 ? 0 : 1).replace(/\.0$/, "")}M`;
  if (number >= 1_000) return `$${Math.round(number / 1_000)}K`;
  return `$${Math.round(number).toLocaleString()}`;
}

function formatNumber(value) {
  const number = Math.round(Number(value) || 0);
  return number ? number.toLocaleString() : "";
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
    "uploaded_url",
    "maps_url",
    "latitude",
    "longitude",
    "traffic_count",
    "population_1_mile",
    "population_3_mile",
    "population_5_mile",
    "demographics_source",
    "note",
    "source",
    "full_text",
    "public_summary",
    "verification_status",
    "source_urls",
    "enrichment_status",
    "enrichment_note",
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

function mergeIfMissing(record, additions = {}) {
  Object.entries(additions).forEach(([key, value]) => {
    const clean = cleanText(value, key === "note" || key === "full_text" || key === "public_summary" ? 12000 : 1000);
    if (clean && isMissingValue(record[key])) record[key] = clean;
  });
}

function weakRecordName(record) {
  const name = String(record.name || "").trim();
  if (!name) return true;
  if (/^(screenshot|image|img|document|scan|new car wash listing|imported listing link)/i.test(name)) return true;
  return /\.(?:png|jpe?g|webp|pdf)$/i.test(name);
}

function extractState(value) {
  const match = String(value || "").match(/\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b/i);
  return match ? match[1].toUpperCase() : "";
}

function extractAddressCandidate(record) {
  const fields = [record.market, record.note, record.full_text, record.name].filter(Boolean);
  for (const field of fields) {
    const text = String(field || "");
    const address = text.match(/\b\d{2,6}\s+[A-Za-z0-9 .'-]+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Highway|Hwy|Pike|Parkway|Pkwy|Way|Court|Ct|Circle|Cir|Trail|Trl|Place|Pl|Terrace|Ter|Turnpike|Tpke)\b[^.\n]{0,90}/i);
    if (address) return cleanText(address[0].replace(/\s+/g, " "), 300);
  }
  return "";
}

function localUploadPath(uploadUrl) {
  const value = String(uploadUrl || "");
  if (!value.startsWith("/uploads/")) return "";
  const relative = decodeURIComponent(value.replace(/^\/uploads\/?/, ""));
  const resolved = path.resolve(uploadRoot, relative);
  return resolved.startsWith(uploadRoot) ? resolved : "";
}

function mimeForFile(filePath) {
  return mimeTypes[path.extname(filePath).toLowerCase()] || "application/octet-stream";
}

function parseJsonFromText(text) {
  const clean = String(text || "").trim();
  if (!clean) return {};
  try {
    return JSON.parse(clean);
  } catch {
    const match = clean.match(/\{[\s\S]*\}/);
    if (!match) return {};
    try {
      return JSON.parse(match[0]);
    } catch {
      return {};
    }
  }
}

function normalizePublicUrl(value) {
  const clean = cleanText(value, 2000);
  try {
    const parsed = new URL(clean);
    if (!["http:", "https:"].includes(parsed.protocol)) return "";
    return parsed.toString();
  } catch {
    return "";
  }
}

function decodeHtmlEntities(value) {
  return String(value || "")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">");
}

function stripHtmlToText(html) {
  return decodeHtmlEntities(
    String(html || "")
      .replace(/<script[\s\S]*?<\/script>/gi, " ")
      .replace(/<style[\s\S]*?<\/style>/gi, " ")
      .replace(/<noscript[\s\S]*?<\/noscript>/gi, " ")
      .replace(/<[^>]+>/g, " ")
      .replace(/\s+/g, " ")
  ).trim();
}

function htmlMeta(html, name) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const patterns = [
    new RegExp(`<meta[^>]+(?:name|property)=["']${escaped}["'][^>]+content=["']([^"']+)["'][^>]*>`, "i"),
    new RegExp(`<meta[^>]+content=["']([^"']+)["'][^>]+(?:name|property)=["']${escaped}["'][^>]*>`, "i"),
  ];
  for (const pattern of patterns) {
    const match = String(html || "").match(pattern);
    if (match) return decodeHtmlEntities(match[1]);
  }
  return "";
}

function htmlTitle(html) {
  const match = String(html || "").match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  return match ? cleanText(decodeHtmlEntities(match[1]), 240) : "";
}

function cleanListingTitle(value) {
  return cleanText(value, 240)
    .replace(/\s+\|\s+Listing$/i, "")
    .replace(/\s+\|\s+(LoopNet|BizBuySell|Crexi|BusinessesForSale|Google Maps).*$/i, "")
    .replace(/\s+-\s+(LoopNet|BizBuySell|Crexi|BusinessesForSale|Google Maps).*$/i, "")
    .replace(/\bBusinesses?\s+For\s+Sale\b.*$/i, "")
    .replace(/\bCommercial\s+Real\s+Estate\b.*$/i, "")
    .trim();
}

function firstMatch(text, pattern) {
  const match = String(text || "").match(pattern);
  return match ? cleanText(match[1] || match[0], 500) : "";
}

function normalizePopulationValue(value) {
  const clean = cleanText(value, 80).replace(/[^\d]/g, "");
  return clean ? Number(clean).toLocaleString() : "";
}

async function censusGeocode(address) {
  const cleanAddress = cleanText(address, 500);
  if (!cleanAddress) return null;
  if (censusGeocodeCache.has(cleanAddress)) return censusGeocodeCache.get(cleanAddress);
  const url = new URL("https://geocoding.geo.census.gov/geocoder/locations/onelineaddress");
  url.searchParams.set("address", cleanAddress);
  url.searchParams.set("benchmark", "Public_AR_Current");
  url.searchParams.set("format", "json");
  const response = await fetch(url, { headers: { "User-Agent": "ShullmanCarwashScout/1.0" } });
  if (!response.ok) throw new Error(`Census geocode failed (${response.status}).`);
  const match = (await response.json())?.result?.addressMatches?.[0];
  const coordinates = match?.coordinates;
  const geo = coordinates?.x && coordinates?.y ? { lat: Number(coordinates.y), lon: Number(coordinates.x) } : null;
  censusGeocodeCache.set(cleanAddress, geo);
  return geo;
}

async function placeCenterGeocode(place) {
  const cleanPlace = cleanText(place, 500);
  if (!cleanPlace) return null;
  if (placeGeocodeCache.has(cleanPlace)) return placeGeocodeCache.get(cleanPlace);
  const url = new URL("https://nominatim.openstreetmap.org/search");
  url.searchParams.set("q", cleanPlace);
  url.searchParams.set("format", "jsonv2");
  url.searchParams.set("limit", "1");
  url.searchParams.set("countrycodes", "us");
  const response = await fetch(url, {
    headers: {
      "User-Agent": "ShullmanCarwashScout/1.0 demographics maintenance",
      Accept: "application/json",
    },
  });
  if (!response.ok) throw new Error(`Place center geocode failed (${response.status}).`);
  const item = (await response.json())?.[0];
  const lat = Number(item?.lat);
  const lon = Number(item?.lon);
  const geo = Number.isFinite(lat) && Number.isFinite(lon) ? { lat, lon, approximate: true } : null;
  placeGeocodeCache.set(cleanPlace, geo);
  return geo;
}

async function censusPopulationMap() {
  if (censusPopulationCache) return censusPopulationCache;
  const url = `https://www2.census.gov/programs-surveys/acs/summary_file/${censusAcsYear}/table-based-SF/data/5YRData/acsdt5y${censusAcsYear}-b01003.dat`;
  const response = await fetch(url, { headers: { "User-Agent": "ShullmanCarwashScout/1.0" } });
  if (!response.ok) throw new Error(`ACS ${censusAcsYear} population table failed (${response.status}).`);
  const text = await response.text();
  const out = new Map();
  text.split(/\r?\n/).slice(1).forEach((line) => {
    const [geoid, pop] = line.split("|");
    if (!geoid || !geoid.startsWith("1500000US")) return;
    const value = Number(pop);
    if (Number.isFinite(value)) out.set(geoid.replace("1500000US", ""), value);
  });
  censusPopulationCache = out;
  return out;
}

async function censusBlockGroupsNear(lat, lon, miles) {
  const key = `${censusAcsYear}:${Number(lat).toFixed(6)},${Number(lon).toFixed(6)}:${miles}`;
  if (censusRingCache.has(key)) return censusRingCache.get(key);
  const meters = { 1: 1609.344, 3: 4828.032, 5: 8046.72 }[miles];
  const url = new URL(`https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS${censusAcsYear}/MapServer/10/query`);
  url.searchParams.set("f", "json");
  url.searchParams.set("geometry", `${lon},${lat}`);
  url.searchParams.set("geometryType", "esriGeometryPoint");
  url.searchParams.set("inSR", "4326");
  url.searchParams.set("spatialRel", "esriSpatialRelIntersects");
  url.searchParams.set("distance", String(meters));
  url.searchParams.set("units", "esriSRUnit_Meter");
  url.searchParams.set("outFields", "GEOID");
  url.searchParams.set("returnGeometry", "false");
  const response = await fetch(url, { headers: { "User-Agent": "ShullmanCarwashScout/1.0" } });
  if (!response.ok) throw new Error(`TIGERweb ${miles}-mile lookup failed (${response.status}).`);
  const features = (await response.json())?.features || [];
  const geoids = [...new Set(features.map((feature) => cleanText(feature?.attributes?.GEOID, 40)).filter(Boolean))];
  censusRingCache.set(key, geoids);
  return geoids;
}

async function lookupCensusDemographics(record) {
  if (hasCompleteDemographics(record)) return {};
  const exactAddress = extractAddressCandidate(record);
  const address = exactAddress || record.market;
  let lat = Number(record.latitude);
  let lon = Number(record.longitude);
  let approximate = !exactAddress;
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    let geo = exactAddress ? await censusGeocode(address) : null;
    if (!geo) geo = await placeCenterGeocode(address);
    if (!geo) return {};
    lat = geo.lat;
    lon = geo.lon;
    approximate = Boolean(geo.approximate || !exactAddress);
  }
  const populationByBlockGroup = await censusPopulationMap();
  const values = {};
  for (const miles of [1, 3, 5]) {
    const geoids = await censusBlockGroupsNear(lat, lon, miles);
    const total = geoids.reduce((sum, geoid) => sum + (populationByBlockGroup.get(geoid) || 0), 0);
    if (total) values[`population_${miles}_mile`] = Number(total).toLocaleString();
  }
  if (!Object.keys(values).length) return {};
  return {
    ...values,
    demographics_source: approximate
      ? `Estimated from Census ACS ${censusAcsYear} block groups around city/market center; street address needed for exact rings`
      : `Estimated from Census ACS ${censusAcsYear} block groups within radius`,
    latitude: String(lat),
    longitude: String(lon),
  };
}

function extractDemographicsFromText(text) {
  const value = String(text || "");
  const population1 = firstMatch(value, /\b1\s*[- ]?mile[^0-9]{0,80}([0-9][0-9,]{2,})/i);
  const population3 = firstMatch(value, /\b3\s*[- ]?mile[^0-9]{0,80}([0-9][0-9,]{2,})/i);
  const population5 = firstMatch(value, /\b5\s*[- ]?mile[^0-9]{0,80}([0-9][0-9,]{2,})/i);
  const extracted = {
    population_1_mile: normalizePopulationValue(population1),
    population_3_mile: normalizePopulationValue(population3),
    population_5_mile: normalizePopulationValue(population5),
  };
  if (extracted.population_1_mile || extracted.population_3_mile || extracted.population_5_mile) {
    extracted.demographics_source = "Imported demographic support page";
  }
  return extracted;
}

function extractMoneyNear(text, labelPattern) {
  const match = String(text || "").match(new RegExp(`(?:${labelPattern})[^$]{0,80}(\\$\\s?[0-9][0-9,.]*(?:\\s?(?:M|MM|K|million|thousand))?)`, "i"));
  return match ? cleanText(match[1].replace(/\s+/g, ""), 80).replace(/\$([0-9])/, "$$$1") : "";
}

function extractNumberNear(text, labelPattern) {
  const match = String(text || "").match(new RegExp(`(?:${labelPattern})[^0-9]{0,90}([0-9][0-9,]{2,})`, "i"));
  return match ? normalizePopulationValue(match[1]) : "";
}

function extractJsonLdText(html) {
  const chunks = [];
  const scripts = String(html || "").matchAll(/<script[^>]+type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi);
  function collect(value) {
    if (!value) return;
    if (typeof value === "string" || typeof value === "number") {
      chunks.push(String(value));
      return;
    }
    if (Array.isArray(value)) {
      value.forEach(collect);
      return;
    }
    if (typeof value === "object") {
      ["name", "description", "streetAddress", "addressLocality", "addressRegion", "postalCode", "telephone", "url"].forEach((key) => collect(value[key]));
      collect(value.address);
      collect(value.offers);
    }
  }
  for (const script of scripts) {
    try {
      collect(JSON.parse(decodeHtmlEntities(script[1])));
    } catch {
      // Listing pages often contain malformed tracking JSON. Ignore and continue.
    }
  }
  return cleanText(chunks.join(" "), 12000);
}

function inferRecordFromListingPage(url, html) {
  const title = htmlMeta(html, "og:title") || htmlTitle(html);
  const description = htmlMeta(html, "og:description") || htmlMeta(html, "description");
  const jsonLd = extractJsonLdText(html);
  const text = cleanText([title, description, jsonLd, stripHtmlToText(html)].filter(Boolean).join(" "), 50000);
  const address = firstMatch(
    text,
    /\b\d{2,6}\s+[A-Za-z0-9 .'-]+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Highway|Hwy|Pike|Parkway|Pkwy|Way|Court|Ct|Circle|Cir|Trail|Trl|Place|Pl|Terrace|Ter|Turnpike|Tpke)\b[^,.\n]{0,90}(?:,\s*[A-Za-z .'-]+)?(?:,\s*(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b)?(?:\s+\d{5})?/i
  );
  const name = cleanListingTitle(title) || firstMatch(text, /\b([A-Z][A-Za-z0-9 &'’-]{2,80}(?:Car Wash|Express Wash|Auto Spa|Wash Club|Wash Center))\b/i);
  const phone = firstMatch(text, /\(?\b\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/);
  const acres = firstMatch(text, /\b([0-9]+(?:\.[0-9]+)?)\s*(?:acre|acres)\b/i);
  const carsPerYear =
    firstMatch(text, /\b([0-9][0-9,]{2,})\s*(?:cars|vehicles|washes)\s*(?:\/|per)?\s*(?:yr|year|annually|annual)\b/i) ||
    extractNumberNear(text, "annual car count|annual wash count|annual wash volume|cars per year|washes per year|car count|wash volume");
  const trafficCount =
    firstMatch(text, /\b(?:traffic|AADT|ADT|vehicles per day|VPD|daily traffic|traffic count|traffic volume)[^0-9]{0,90}([0-9][0-9,]{2,})\b/i) ||
    firstMatch(text, /\b([0-9][0-9,]{2,})\s*(?:VPD|AADT|ADT|vehicles per day|cars per day|daily vehicles)\b/i);
  const state = extractState(address || text);
  const demographics = extractDemographicsFromText(text);
  return {
    name: name || "Imported car wash listing",
    market: address,
    state,
    asking_price: extractMoneyNear(text, "asking price|list price|price|sale price|asking") || "",
    sales: extractMoneyNear(text, "sales|revenue|gross sales|gross revenue") || "",
    ebitda: extractMoneyNear(text, "EBITDA|cash flow|SDE|owner benefit|owner earnings") || "",
    cars_per_year: carsPerYear,
    acres,
    phone,
    traffic_count: trafficCount,
    ...demographics,
    note: cleanText(description || `Listing imported from ${new URL(url).hostname}.`, 1200),
    full_text: text,
  };
}

function responseText(payload) {
  if (payload?.output_text) return payload.output_text;
  const chunks = [];
  (payload?.output || []).forEach((item) => {
    (item?.content || []).forEach((content) => {
      if (content?.text) chunks.push(content.text);
    });
  });
  return chunks.join("\n");
}

async function extractRecordFromImage(record) {
  if (!openaiApiKey || !record.uploaded_url) return {};
  const filePath = localUploadPath(record.uploaded_url);
  if (!filePath || !fs.existsSync(filePath)) return {};
  const mime = mimeForFile(filePath);
  if (!/^image\//i.test(mime)) return {};
  const dataUrl = `data:${mime};base64,${fs.readFileSync(filePath).toString("base64")}`;
  const response = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${openaiApiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: openaiVisionModel,
      input: [
        {
          role: "user",
          content: [
            {
              type: "input_text",
              text:
                "Read this car wash listing screenshot/photo. Return only JSON with these keys when visible: name, market, state, asking_price, sales, ebitda, cars_per_year, acres, phone, website, traffic_count, population_1_mile, population_3_mile, population_5_mile, demographics_source, note. Use null for missing fields. Do not guess financial numbers or demographics.",
            },
            {
              type: "input_image",
              image_url: dataUrl,
              detail: "high",
            },
          ],
        },
      ],
    }),
  });
  if (!response.ok) throw new Error(`Image analysis failed (${response.status}).`);
  const payload = await response.json();
  const parsed = parseJsonFromText(responseText(payload));
  const allowed = ["name", "market", "state", "asking_price", "sales", "ebitda", "cars_per_year", "acres", "phone", "website", "traffic_count", "population_1_mile", "population_3_mile", "population_5_mile", "demographics_source", "note"];
  return Object.fromEntries(allowed.map((key) => [key, parsed[key]]).filter(([, value]) => value));
}

async function extractRecordFromText(text, sourceUrl) {
  if (!openaiApiKey || !text) return {};
  const response = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${openaiApiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: openaiVisionModel,
      input: [
        {
          role: "user",
          content: [
            {
              type: "input_text",
              text:
                `Extract a car wash listing from this public listing page text. Source URL: ${sourceUrl}\n` +
                "Return only JSON with these keys when visible: name, market, state, asking_price, sales, ebitda, cars_per_year, acres, phone, website, traffic_count, population_1_mile, population_3_mile, population_5_mile, demographics_source, note. Use null for missing fields. Do not guess financial numbers or demographics.\n\n" +
                cleanText(text, 30000),
            },
          ],
        },
      ],
    }),
  });
  if (!response.ok) throw new Error(`Listing analysis failed (${response.status}).`);
  const parsed = parseJsonFromText(responseText(await response.json()));
  const allowed = ["name", "market", "state", "asking_price", "sales", "ebitda", "cars_per_year", "acres", "phone", "website", "traffic_count", "population_1_mile", "population_3_mile", "population_5_mile", "demographics_source", "note"];
  return Object.fromEntries(allowed.map((key) => [key, parsed[key]]).filter(([, value]) => value));
}

async function lookupGooglePlace(record) {
  if (!googlePlacesApiKey) return {};
  const address = extractAddressCandidate(record);
  const fallbackQuery = cleanText([record.name, record.market, record.state].filter(Boolean).join(" "), 500);
  const textQuery = address ? `${address} car wash` : fallbackQuery;
  if (!textQuery) return {};
  const response = await fetch("https://places.googleapis.com/v1/places:searchText", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Goog-Api-Key": googlePlacesApiKey,
      "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri,places.location,places.businessStatus,places.types",
    },
    body: JSON.stringify({
      textQuery,
      includedType: "car_wash",
    }),
  });
  if (!response.ok) throw new Error(`Google Places lookup failed (${response.status}).`);
  const payload = await response.json();
  const place = Array.isArray(payload.places) ? payload.places[0] : null;
  if (!place) return {};
  const displayName = place.displayName?.text || "";
  const formattedAddress = place.formattedAddress || "";
  const lat = place.location?.latitude;
  const lng = place.location?.longitude;
  return {
    name: weakRecordName(record) ? displayName : "",
    market: formattedAddress,
    state: extractState(formattedAddress),
    phone: place.nationalPhoneNumber || "",
    website: place.websiteUri || "",
    maps_url: place.googleMapsUri || "",
    latitude: lat == null ? "" : String(lat),
    longitude: lng == null ? "" : String(lng),
    public_summary: formattedAddress
      ? `${displayName || "Car wash"} matched by address at ${formattedAddress}. Public contact fields were added from Google Places when available.`
      : "",
    source_urls: place.googleMapsUri || "",
    verification_status: "Address contact lookup",
  };
}

async function lookupTrafficCount(record) {
  if (!trafficApiUrl || !isMissingValue(record.traffic_count)) return {};
  const address = record.market || extractAddressCandidate(record);
  const url = trafficApiUrl
    .replace(/\{lat\}/g, encodeURIComponent(record.latitude || ""))
    .replace(/\{lng\}/g, encodeURIComponent(record.longitude || ""))
    .replace(/\{address\}/g, encodeURIComponent(address || ""));
  if (!/^https?:\/\//i.test(url)) return {};
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Traffic lookup failed (${response.status}).`);
  const data = await response.json();
  const value = data.traffic_count || data.aadt || data.vpd || data.count || "";
  const source = data.source_url || data.source || "";
  return value
    ? {
        traffic_count: String(value),
        source_urls: [record.source_urls, source].filter(Boolean).join(" | "),
      }
    : {};
}

async function lookupDemographics(record) {
  if (hasCompleteDemographics(record)) return {};
  const address = record.market || extractAddressCandidate(record);
  if (demographicsApiUrl) {
    const url = demographicsApiUrl
      .replace(/\{lat\}/g, encodeURIComponent(record.latitude || ""))
      .replace(/\{lng\}/g, encodeURIComponent(record.longitude || ""))
      .replace(/\{address\}/g, encodeURIComponent(address || ""));
    if (/^https?:\/\//i.test(url)) {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Demographics lookup failed (${response.status}).`);
      const data = await response.json();
      const one = data.population_1_mile || data.pop_1_mile || data.one_mile_population || data["1_mile_population"] || "";
      const three = data.population_3_mile || data.pop_3_mile || data.three_mile_population || data["3_mile_population"] || "";
      const five = data.population_5_mile || data.pop_5_mile || data.five_mile_population || data["5_mile_population"] || "";
      const source = data.demographics_source || data.source_url || data.source || "";
      const values = {
        population_1_mile: normalizePopulationValue(one),
        population_3_mile: normalizePopulationValue(three),
        population_5_mile: normalizePopulationValue(five),
        demographics_source: source || "Demographics provider",
        source_urls: [record.source_urls, data.source_url].filter(Boolean).join(" | "),
      };
      if (values.population_1_mile || values.population_3_mile || values.population_5_mile) return values;
    }
  }
  return lookupCensusDemographics(record);
}

function needsListingRefresh(record) {
  return Boolean(
    normalizePublicUrl(record.research_url) &&
      (!extractAddressCandidate(record) ||
        isMissingValue(record.maps_url) ||
        isMissingValue(record.latitude) ||
        isMissingValue(record.longitude) ||
        isMissingValue(record.sales) ||
        isMissingValue(record.cars_per_year) ||
        isMissingValue(record.traffic_count) ||
        !hasCompleteDemographics(record))
  );
}

function operatingEstimateFields(record) {
  const additions = {};
  const ask = moneyToNumber(record.asking_price);
  const sales = moneyToNumber(record.sales);
  const ebitda = moneyToNumber(record.ebitda);
  const cars = numericValue(record.cars_per_year);
  const acres = numericValue(record.acres);
  const text = [record.name, record.market, record.full_text, record.note].filter(Boolean).join(" ").toLowerCase();

  if (isMissingValue(record.ebitda)) {
    let estimatedEbitda = 0;
    if (sales) estimatedEbitda = sales * 0.24;
    else if (ask) estimatedEbitda = ask / 6.5;
    else if (cars) estimatedEbitda = cars * 3.25;
    else if (/express|tunnel|conveyor|membership/.test(text)) estimatedEbitda = 360000;
    else if (/self[\s-]?serve|coin|hand wash|detail/.test(text)) estimatedEbitda = 140000;
    else if (acres >= 1.4) estimatedEbitda = 320000;
    if (estimatedEbitda) additions.ebitda = `Est. ${formatMoneyShort(estimatedEbitda)}`;
  }

  const resolvedEbitda = ebitda || moneyToNumber(additions.ebitda);
  if (isMissingValue(record.sales)) {
    let estimatedSales = 0;
    if (resolvedEbitda) estimatedSales = resolvedEbitda / 0.24;
    else if (ask) estimatedSales = ask * 0.42;
    if (estimatedSales) additions.sales = `Est. ${formatMoneyShort(estimatedSales)}`;
  }

  const resolvedSales = sales || moneyToNumber(additions.sales);
  if (isMissingValue(record.cars_per_year)) {
    let estimatedCars = 0;
    if (resolvedSales) estimatedCars = resolvedSales / 18;
    else if (resolvedEbitda) estimatedCars = resolvedEbitda / 3.25;
    else if (/express|tunnel|conveyor|membership/.test(text)) estimatedCars = 145000;
    else if (/self[\s-]?serve|coin|hand wash|detail/.test(text)) estimatedCars = 45000;
    if (estimatedCars) additions.cars_per_year = `Est. ${formatNumber(estimatedCars)}`;
  }

  if (isMissingValue(record.traffic_count)) {
    const resolvedCars = cars || numericValue(additions.cars_per_year);
    let estimatedTraffic = 0;
    if (resolvedCars) estimatedTraffic = Math.max(12000, Math.min(65000, (resolvedCars / 365) * 90));
    else if (/highway|hwy|interstate|freeway|turnpike|expressway/.test(text)) estimatedTraffic = 42000;
    else if (/boulevard|blvd|avenue|ave|road|rd|street|st/.test(text)) estimatedTraffic = 24000;
    if (estimatedTraffic) additions.traffic_count = `Est. ${formatNumber(estimatedTraffic)} VPD`;
  }

  if (Object.keys(additions).length) {
    additions.enrichment_note = [
      record.enrichment_note,
      "Some operating fields are Scout estimates from available listing/site signals; verify against seller financials, DOT traffic counts, and source documents.",
    ]
      .filter(Boolean)
      .join(" ");
  }
  return additions;
}

async function refreshRecordFromListingUrl(record) {
  const url = normalizePublicUrl(record.research_url);
  if (!url || !needsListingRefresh(record)) return {};
  const html = await fetchListingHtml(url);
  const inferred = inferRecordFromListingPage(url, html);
  const mergedText = [inferred.full_text, record.full_text].filter(Boolean).join("\n\n");
  let aiFields = {};
  try {
    aiFields = await extractRecordFromText(mergedText, url);
  } catch {
    aiFields = {};
  }
  return { ...inferred, ...aiFields };
}

async function enrichRecord(record) {
  const enriched = { ...record };
  const notes = [];
  try {
    const listingFields = await refreshRecordFromListingUrl(enriched);
    if (Object.keys(listingFields).length) {
      if (weakRecordName(enriched) && listingFields.name) enriched.name = cleanText(listingFields.name, 1000);
      if (listingFields.market && !extractAddressCandidate(enriched)) enriched.market = cleanText(listingFields.market, 1000);
      mergeIfMissing(enriched, listingFields);
      notes.push("listing refresh");
    }
  } catch (error) {
    notes.push(error.message);
  }

  try {
    const imageFields = await extractRecordFromImage(enriched);
    if (Object.keys(imageFields).length) {
      if (weakRecordName(enriched) && imageFields.name) enriched.name = cleanText(imageFields.name, 1000);
      mergeIfMissing(enriched, imageFields);
      notes.push("image read");
    }
  } catch (error) {
    notes.push(error.message);
  }

  try {
    const placeFields = await lookupGooglePlace(enriched);
    if (Object.keys(placeFields).length) {
      mergeIfMissing(enriched, placeFields);
      if (placeFields.market && !extractAddressCandidate(record)) enriched.market = cleanText(placeFields.market, 1000);
      notes.push("map/contact lookup");
    }
  } catch (error) {
    notes.push(error.message);
  }

  try {
    const trafficFields = await lookupTrafficCount(enriched);
    if (Object.keys(trafficFields).length) {
      mergeIfMissing(enriched, trafficFields);
      notes.push("traffic lookup");
    }
  } catch (error) {
    notes.push(error.message);
  }

  try {
    const demographicFields = await lookupDemographics(enriched);
    if (Object.keys(demographicFields).length) {
      mergeIfMissing(enriched, demographicFields);
      notes.push("demographics lookup");
    }
  } catch (error) {
    notes.push(error.message);
  }

  const estimateFields = operatingEstimateFields(enriched);
  if (Object.keys(estimateFields).length) {
    mergeIfMissing(enriched, estimateFields);
    notes.push("operating estimates");
  }

  enriched.enrichment_status = notes.length ? notes.join(" | ") : "saved without automatic enrichment";
  if (isMissingValue(enriched.traffic_count) && (enriched.latitude || enriched.market)) {
    enriched.enrichment_note = "Traffic count requires a configured traffic data source; Scout does not invent traffic counts.";
  }
  if (!hasCompleteDemographics(enriched) && (enriched.latitude || enriched.market)) {
    const demographicNote = "1/3/5-mile demographics require a configured demographic data source or an imported demographic support page.";
    enriched.enrichment_note = [enriched.enrichment_note, demographicNote].filter(Boolean).join(" ");
  }
  return enriched;
}

function needsMaintenance(record) {
  return (
    weakRecordName(record) ||
    isMissingValue(record.state) ||
    isMissingValue(record.maps_url) ||
    isMissingValue(record.latitude) ||
    isMissingValue(record.longitude) ||
    isMissingValue(record.phone) ||
    isMissingValue(record.website) ||
    isMissingValue(record.traffic_count) ||
    !hasCompleteDemographics(record)
  );
}

async function handleMaintenance(req, res) {
  if (req.method !== "POST") {
    sendJson(res, 405, { error: "Method not allowed" });
    return;
  }
  if (!maintenanceAuthorized(req)) {
    sendJson(res, 403, { error: "Maintenance secret is missing or incorrect." });
    return;
  }

  const records = readManualRecords();
  const maxRecords = Number(process.env.MAINTENANCE_MAX_RECORDS || records.length || 0);
  const recordsNeedingMaintenance = records.filter(needsMaintenance);
  let checked = 0;
  let updated = 0;
  const errors = [];
  const maintained = [];

  for (const record of recordsNeedingMaintenance) {
    if (checked >= maxRecords) break;
    checked += 1;
    try {
      const before = JSON.stringify(record);
      const enriched = await enrichRecord(record);
      Object.assign(record, enriched, {
        last_maintenance_at: new Date().toISOString(),
      });
      if (JSON.stringify(record) !== before) updated += 1;
      maintained.push({ id: record.id, name: record.name, market: record.market });
    } catch (error) {
      errors.push({ id: record.id, name: record.name, error: error.message || "maintenance failed" });
    }
  }

  if (checked || updated) await writeManualRecords(records);
  sendJson(res, 200, {
    total_manual_records: records.length,
    needing_maintenance: recordsNeedingMaintenance.length,
    checked,
    updated,
    skipped_complete: records.length - recordsNeedingMaintenance.length,
    deferred_by_limit: Math.max(recordsNeedingMaintenance.length - checked, 0),
    maintained,
    errors,
  });
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
    Promise.all(cleaned.map(enrichRecord))
      .then(
        (enriched) => {
          enriched.reverse();
          return { items: enriched, warning: "" };
        },
        (enrichError) => {
          cleaned.forEach((record) => {
            record.enrichment_status = enrichError.message || "Automatic enrichment failed.";
          });
          cleaned.reverse();
          return { items: cleaned, warning: enrichError.message || "Automatic enrichment failed." };
        }
      )
      .then(({ items, warning }) => {
        const records = readManualRecords();
        items.forEach((record) => records.unshift(record));
        return writeManualRecords(records).then(() => {
          const body = { records: items, total: records.length };
          if (warning) body.warning = warning;
          sendJson(res, 201, body);
        });
      })
      .catch((writeError) => {
        sendJson(res, 500, { error: `Could not save listing: ${writeError.message}` });
      });
  });
}

async function fetchListingHtml(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(url, {
      redirect: "follow",
      signal: controller.signal,
      headers: {
        "User-Agent": "Mozilla/5.0 (compatible; ShullmanCarwashScout/1.0; +https://render.com)",
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      },
    });
    if (!response.ok) throw new Error(`Listing page returned ${response.status}.`);
    const contentType = response.headers.get("content-type") || "";
    if (!/text\/html|application\/xhtml\+xml|text\/plain/i.test(contentType)) {
      throw new Error("That link is not a readable web page.");
    }
    const buffer = Buffer.from(await response.arrayBuffer());
    const maxBytes = 2 * 1024 * 1024;
    return buffer.subarray(0, maxBytes).toString("utf8");
  } finally {
    clearTimeout(timeout);
  }
}

function handleLinkRecords(req, res) {
  if (req.method !== "POST") {
    sendJson(res, 405, { error: "Method not allowed" });
    return;
  }

  readJsonBody(req, 256 * 1024, async (error, payload) => {
    if (error) {
      sendJson(res, 400, { error: error.message });
      return;
    }

    const url = normalizePublicUrl(payload?.url);
    const note = cleanText(payload?.note || "", 2000);
    if (!url) {
      sendJson(res, 400, { error: "Paste a full public link that starts with http or https." });
      return;
    }

    const baseRecord = cleanRecordPayload({
      name: "Imported listing link",
      research_url: url,
      note: [note, "Listing link imported from Admin."].filter(Boolean).join(" "),
      source: "Listing Link",
    });
    let record = baseRecord;
    let warning = "";

    try {
      const html = await fetchListingHtml(url);
      const inferred = inferRecordFromListingPage(url, html);
      if (weakRecordName(record) && inferred.name) record.name = cleanText(inferred.name, 1000);
      mergeIfMissing(record, inferred);

      try {
        const aiFields = await extractRecordFromText(record.full_text, url);
        if (weakRecordName(record) && aiFields.name) record.name = cleanText(aiFields.name, 1000);
        mergeIfMissing(record, aiFields);
      } catch (aiError) {
        warning = aiError.message || "";
      }

      record = await enrichRecord(record);
    } catch (fetchError) {
      warning = `${fetchError.message || "The listing page could not be read automatically."} Saved the link for review.`;
      record.enrichment_status = "link saved; page not readable from server";
      record.enrichment_note = "If the listing page blocks server reading, upload a screenshot or PDF of the listing and Scout can process that file instead.";
    }

    const records = readManualRecords();
    records.unshift(record);
    writeManualRecords(records);
    sendJson(res, 201, { records: [record], total: records.length, warning });
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
  if (!authorized(req) && !((req.url || "").startsWith("/api/maintenance") && maintenanceAuthorized(req))) {
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

  if ((req.url || "").startsWith("/api/link-records")) {
    handleLinkRecords(req, res);
    return;
  }

  if ((req.url || "").startsWith("/api/maintenance/enrich")) {
    handleMaintenance(req, res);
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

loadManualRecords()
  .catch((error) => console.error("Initial records load failed:", error.message))
  .finally(() => {
    server.listen(port, host, () => {
      console.log(`Carwash Scout running on ${host}:${port}`);
    });
  });
