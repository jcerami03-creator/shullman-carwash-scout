import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "/Users/josephcerami/Documents/LLM For Shullman Paperwork";
const generatedPath = path.join(root, "generated", "carwash_records.js");
const outputDir = path.join(root, "outputs");
const outputPath = path.join(outputDir, "carwash_scout_locations.xlsx");

function loadRecords() {
  return fs.readFile(generatedPath, "utf8").then((text) => {
    const payload = text.slice(text.indexOf("["), text.lastIndexOf("]") + 1);
    return JSON.parse(payload);
  });
}

function clean(value) {
  return String(value ?? "").trim();
}

function cityFromMarket(market) {
  const parts = clean(market).split(",").map((part) => part.trim()).filter(Boolean);
  if (parts.length >= 3) return parts[1];
  if (parts.length === 2 && !/^[A-Z]{2}(?:\s+\d{5})?$/.test(parts[1])) return parts[1];
  return "";
}

function moneyNumber(value) {
  const raw = clean(value).toLowerCase();
  const match = raw.replace(/[$,]/g, "").match(/\d+(\.\d+)?/);
  if (!match) return 0;
  let number = Number(match[0]);
  if (/million|\d(\.\d+)?\s*m\b/i.test(raw)) number *= 1_000_000;
  else if (/\d(\.\d+)?\s*k\b/i.test(raw)) number *= 1_000;
  return Math.round(number);
}

function firstNumber(value) {
  const match = clean(value).replace(/,/g, "").match(/\d+(\.\d+)?/);
  return match ? Number(match[0]) : 0;
}

function mapsUrl(record) {
  if (clean(record.maps_url)) return clean(record.maps_url);
  if (clean(record.latitude) && clean(record.longitude)) {
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${record.latitude},${record.longitude}`)}`;
  }
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(clean(record.market))}`;
}

function sourceType(record) {
  return clean(record.id).startsWith("public-map-") ? "Public coverage" : "Scanned paperwork";
}

function sourceName(record) {
  return clean(record.source).split("|")[0].trim();
}

function trafficNumeric(value) {
  return firstNumber(value);
}

function sortRecords(records) {
  return [...records].sort((a, b) => {
    const left = [clean(a.state), cityFromMarket(a.market), clean(a.name)].join("|");
    const right = [clean(b.state), cityFromMarket(b.market), clean(b.name)].join("|");
    return left.localeCompare(right);
  });
}

function styleHeader(range) {
  range.format = {
    fill: "#17604D",
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
  };
}

function styleTitle(range) {
  range.format = {
    fill: "#E6EFEA",
    font: { bold: true, color: "#17221F", size: 16 },
  };
}

function addTable(sheet, address, name) {
  const table = sheet.tables.add(address, true, name);
  table.style = "TableStyleMedium4";
  table.showFilterButton = true;
  return table;
}

function col(index) {
  let n = index + 1;
  let s = "";
  while (n > 0) {
    const r = (n - 1) % 26;
    s = String.fromCharCode(65 + r) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
}

function setWidths(sheet, widths) {
  widths.forEach((width, index) => {
    sheet.getRange(`${col(index)}:${col(index)}`).format.columnWidthPx = width;
  });
}

const records = sortRecords(await loadRecords());
const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const locations = workbook.worksheets.add("Scout Website Export");
const traffic = workbook.worksheets.add("Traffic Counts");
const update = workbook.worksheets.add("Update Instructions");

for (const sheet of [summary, locations, traffic, update]) {
  sheet.showGridLines = false;
}

const stateMap = new Map();
const cityMap = new Map();
for (const record of records) {
  const state = clean(record.state);
  const city = cityFromMarket(record.market);
  stateMap.set(state, (stateMap.get(state) || 0) + 1);
  const cityKey = `${state}|${city}`;
  const existing = cityMap.get(cityKey) || { state, city, locations: 0, traffic: 0 };
  existing.locations += 1;
  if (clean(record.traffic_count)) existing.traffic += 1;
  cityMap.set(cityKey, existing);
}

const trafficRecords = records.filter((record) => clean(record.traffic_count));
const scannedCount = records.filter((record) => sourceType(record) === "Scanned paperwork").length;
const publicCount = records.length - scannedCount;

summary.getRange("A1:H1").merge();
summary.getRange("A1").values = [["Carwash Scout Location Workbook"]];
styleTitle(summary.getRange("A1:H1"));
summary.getRange("A3:H4").values = [
  ["Total Locations", "States", "Cities", "Traffic Counts", "Scanned Records", "Public Coverage", "Avg Ask", "Avg EBITDA"],
  [
    records.length,
    stateMap.size,
    cityMap.size,
    trafficRecords.length,
    scannedCount,
    publicCount,
    records.reduce((sum, record) => sum + moneyNumber(record.asking_price), 0) / records.length,
    records.reduce((sum, record) => sum + moneyNumber(record.ebitda), 0) / records.length,
  ],
];
styleHeader(summary.getRange("A3:H3"));
summary.getRange("A4:F4").format.numberFormat = "#,##0";
summary.getRange("G4:H4").format.numberFormat = "$#,##0";

const stateRows = [...stateMap.entries()]
  .sort((a, b) => a[0].localeCompare(b[0]))
  .map(([state, count]) => {
    const trafficCount = records.filter((record) => clean(record.state) === state && clean(record.traffic_count)).length;
    return [state, count, trafficCount];
  });
summary.getRange("A7:C7").values = [["State", "Locations", "With Traffic Count"]];
summary.getRangeByIndexes(7, 0, stateRows.length, 3).values = stateRows;
styleHeader(summary.getRange("A7:C7"));
addTable(summary, `A7:C${7 + stateRows.length}`, "StateSummary");

const cityRows = [...cityMap.values()]
  .sort((a, b) => `${a.state}|${a.city}`.localeCompare(`${b.state}|${b.city}`))
  .map((row) => [row.state, row.city, row.locations, row.traffic]);
summary.getRange("E7:H7").values = [["State", "City", "Locations", "With Traffic Count"]];
summary.getRangeByIndexes(7, 4, cityRows.length, 4).values = cityRows;
styleHeader(summary.getRange("E7:H7"));
addTable(summary, `E7:H${7 + cityRows.length}`, "CitySummary");

const headers = [
  "State / City Group",
  "State",
  "City",
  "Name",
  "Address",
  "Year",
  "Asking Price",
  "Sales",
  "EBITDA",
  "Cars/Yr",
  "Traffic Count",
  "Traffic Number",
  "Acres",
  "Phone",
  "Website",
  "Google Maps",
  "Source Type",
  "Source",
  "Notes",
];

const locationRows = records.map((record) => [
  [clean(record.state), cityFromMarket(record.market)].filter(Boolean).join(" / "),
  clean(record.state),
  cityFromMarket(record.market),
  clean(record.name),
  clean(record.market),
  clean(record.year),
  clean(record.asking_price),
  clean(record.sales),
  clean(record.ebitda),
  clean(record.cars_per_year),
  clean(record.traffic_count),
  trafficNumeric(record.traffic_count) || "",
  clean(record.acres),
  clean(record.phone),
  clean(record.website),
  mapsUrl(record),
  sourceType(record),
  sourceName(record),
  clean(record.note),
]);

locations.getRange("A1:S1").values = [headers];
locations.getRangeByIndexes(1, 0, locationRows.length, headers.length).values = locationRows;
styleHeader(locations.getRange("A1:S1"));
addTable(locations, `A1:S${locationRows.length + 1}`, "ScoutWebsiteExport");
locations.freezePanes.freezeRows(1);
setWidths(locations, [150, 55, 120, 230, 290, 70, 105, 105, 105, 105, 165, 95, 80, 125, 175, 260, 120, 160, 420]);
locations.getRange("S:S").format.wrapText = true;

const trafficRows = trafficRecords.map((record) => [
  clean(record.state),
  cityFromMarket(record.market),
  clean(record.name),
  clean(record.market),
  clean(record.traffic_count),
  trafficNumeric(record.traffic_count) || "",
  clean(record.asking_price),
  clean(record.ebitda),
  clean(record.acres),
  mapsUrl(record),
  sourceType(record),
  sourceName(record),
]);
traffic.getRange("A1:L1").values = [[
  "State",
  "City",
  "Name",
  "Address",
  "Traffic Count",
  "Traffic Number",
  "Asking Price",
  "EBITDA",
  "Acres",
  "Google Maps",
  "Source Type",
  "Source",
]];
if (trafficRows.length) {
  traffic.getRangeByIndexes(1, 0, trafficRows.length, 12).values = trafficRows;
}
styleHeader(traffic.getRange("A1:L1"));
addTable(traffic, `A1:L${Math.max(trafficRows.length + 1, 2)}`, "TrafficCounts");
traffic.freezePanes.freezeRows(1);
setWidths(traffic, [55, 120, 230, 300, 165, 95, 105, 105, 80, 260, 120, 160]);

update.getRange("A1:F1").merge();
update.getRange("A1").values = [["How Future Scans Auto-Add to the Scout and Workbook"]];
styleTitle(update.getRange("A1:F1"));
update.getRange("A3:F9").values = [
  ["Step", "What to do", "Command / Rule", "Output", "Notes", "Status"],
  ["1", "Put new scanned PDFs in the PDF folder", "/Users/josephcerami/PDF FOR CAR WASH SCOUt", "PDF file is available to the OCR pipeline", "Epson OCR scans can be used directly.", "Ready"],
  ["2", "Run the update command", "tools/update_carwash_scout.sh", "OCR text, Scout data, audit, and spreadsheet update", "This is the one command to use later.", "Ready"],
  ["3", "Open the site", "http://localhost:8080", "Updated Scout search", "Restart local server if needed.", "Ready"],
  ["4", "Open the workbook", "outputs/carwash_scout_locations.xlsx", "Scout Website Export tab contains all site records grouped by state/city plus traffic counts", "Workbook is regenerated from the same records as the site.", "Ready"],
  ["", "", "", "", "", ""],
  ["Quality checks", "Must stay clean", "0 duplicate addresses; 48 states; no audit flags", "tools/audit_carwash_records.py", "Run automatically by update command.", "Ready"],
];
styleHeader(update.getRange("A3:F3"));
setWidths(update, [70, 240, 320, 260, 320, 90]);
update.getRange("A3:F9").format.wrapText = true;

summary.getRange("A:H").format.autofitColumns();
summary.freezePanes.freezeRows(7);

await fs.mkdir(outputDir, { recursive: true });
await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "formula error scan",
});
await workbook.render({ sheetName: "Summary", autoCrop: "all", scale: 1, format: "png" });
await workbook.render({ sheetName: "Scout Website Export", range: "A1:S45", scale: 1, format: "png" });
await workbook.render({ sheetName: "Traffic Counts", range: "A1:L45", scale: 1, format: "png" });
await workbook.render({ sheetName: "Update Instructions", autoCrop: "all", scale: 1, format: "png" });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({ outputPath, records: records.length, trafficRecords: trafficRecords.length, states: stateMap.size }));
