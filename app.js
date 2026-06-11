const STORAGE_KEY = "shullmanCarWashKnowledge:v20";
const importedRows = Array.isArray(window.CARWASH_IMPORTED_RECORDS) ? window.CARWASH_IMPORTED_RECORDS : [];
const documentLibrary = Array.isArray(window.CARWASH_DOCUMENT_LIBRARY) ? window.CARWASH_DOCUMENT_LIBRARY : [];
const STATE_NAME_TO_CODE = {
  alabama: "AL",
  alaska: "AK",
  arizona: "AZ",
  arkansas: "AR",
  california: "CA",
  colorado: "CO",
  connecticut: "CT",
  delaware: "DE",
  "district of columbia": "DC",
  dc: "DC",
  florida: "FL",
  georgia: "GA",
  hawaii: "HI",
  idaho: "ID",
  illinois: "IL",
  indiana: "IN",
  iowa: "IA",
  kansas: "KS",
  kentucky: "KY",
  louisiana: "LA",
  maine: "ME",
  maryland: "MD",
  massachusetts: "MA",
  michigan: "MI",
  minnesota: "MN",
  mississippi: "MS",
  missouri: "MO",
  montana: "MT",
  nebraska: "NE",
  nevada: "NV",
  newhampshire: "NH",
  newjersey: "NJ",
  newmexico: "NM",
  newyork: "NY",
  northcarolina: "NC",
  northdakota: "ND",
  ohio: "OH",
  oklahoma: "OK",
  oregon: "OR",
  pennsylvania: "PA",
  rhodeisland: "RI",
  southcarolina: "SC",
  southdakota: "SD",
  tennessee: "TN",
  texas: "TX",
  utah: "UT",
  vermont: "VT",
  virginia: "VA",
  washington: "WA",
  westvirginia: "WV",
  wisconsin: "WI",
  wyoming: "WY",
};
const STATE_CODES = new Set(Object.values(STATE_NAME_TO_CODE));
const STATE_OPTIONS = [
  ["AL", "Alabama"],
  ["AZ", "Arizona"],
  ["AR", "Arkansas"],
  ["CA", "California"],
  ["CO", "Colorado"],
  ["CT", "Connecticut"],
  ["DE", "Delaware"],
  ["FL", "Florida"],
  ["GA", "Georgia"],
  ["ID", "Idaho"],
  ["IL", "Illinois"],
  ["IN", "Indiana"],
  ["IA", "Iowa"],
  ["KS", "Kansas"],
  ["KY", "Kentucky"],
  ["LA", "Louisiana"],
  ["ME", "Maine"],
  ["MD", "Maryland"],
  ["MA", "Massachusetts"],
  ["MI", "Michigan"],
  ["MN", "Minnesota"],
  ["MS", "Mississippi"],
  ["MO", "Missouri"],
  ["MT", "Montana"],
  ["NE", "Nebraska"],
  ["NV", "Nevada"],
  ["NH", "New Hampshire"],
  ["NJ", "New Jersey"],
  ["NM", "New Mexico"],
  ["NY", "New York"],
  ["NC", "North Carolina"],
  ["ND", "North Dakota"],
  ["OH", "Ohio"],
  ["OK", "Oklahoma"],
  ["OR", "Oregon"],
  ["PA", "Pennsylvania"],
  ["RI", "Rhode Island"],
  ["SC", "South Carolina"],
  ["SD", "South Dakota"],
  ["TN", "Tennessee"],
  ["TX", "Texas"],
  ["UT", "Utah"],
  ["VT", "Vermont"],
  ["VA", "Virginia"],
  ["WA", "Washington"],
  ["WV", "West Virginia"],
  ["WI", "Wisconsin"],
  ["WY", "Wyoming"],
];

const sampleRows = [
  {
    year: "1991",
    market: "South Florida",
    asking_price: "$1.2M",
    sales: "$620K",
    ebitda: "$185K",
    cars_wk: "78,000",
    acres: "0.80",
    note: "Early operator with loyal repeat customers. Good acquisition only if real estate control is clean.",
    wisdom_layer: "A good wash was not just volume. Mike cared whether the volume could survive a new competitor, a road change, or a lazy operator.",
    data_layer: "Sales and EBITDA were modest, but the customer habit was durable.",
    decision_layer: "Watch lease terms before trusting the cash flow.",
    mistake_layer: "Do not pay full price for sales that depend on one owner being present every day.",
    mental_model: "Durable habit beats temporary traffic.",
    source: "Wisdom_Layer_1990s.pdf",
  },
  {
    year: "1994",
    market: "New Jersey",
    asking_price: "$2.4M",
    sales: "$1.1M",
    ebitda: "$360K",
    cars_wk: "95,000",
    acres: "1.10",
    note: "Strong road frontage, but new zoning made expansion hard. Scarcity became part of the moat.",
    wisdom_layer: "The best car wash real estate was often valuable because it could not easily be recreated.",
    data_layer: "High annual car count and limited nearby parcels supported a premium multiple.",
    decision_layer: "Pay more only when the location has defensible scarcity.",
    mistake_layer: "Do not confuse a busy road with a protected trade area.",
    mental_model: "Zoning scarcity can be a moat.",
    source: "Wisdom_Layer_1990s.pdf",
  },
  {
    year: "1998",
    market: "Atlanta",
    asking_price: "$3.1M",
    sales: "$1.6M",
    ebitda: "$520K",
    cars_wk: "108,000",
    acres: "1.35",
    note: "Operator reinvested every year. Equipment was not new, but the site was loved and well maintained.",
    wisdom_layer: "Great operators created trust before software existed. Cleanliness, speed, and consistency were the membership program.",
    data_layer: "EBITDA over $500K with strong yearly car volume indicated durable local demand.",
    decision_layer: "This is the kind of operator record worth studying and copying.",
    mistake_layer: "Do not overfocus on equipment age if maintenance culture is excellent.",
    mental_model: "Operating culture compounds quietly.",
    source: "Operator_AskingPrice_KeyMetric.pdf",
  },
  {
    year: "2001",
    market: "Dallas",
    asking_price: "$4.8M",
    sales: "$2.2M",
    ebitda: "$740K",
    cars_wk: "132,000",
    acres: "1.70",
    note: "Fast-growing suburb. High sales, but competition beginning to chase the same rooftops.",
    wisdom_layer: "Growth markets can hide future margin pressure. The question is not whether the town is growing, but who else noticed.",
    data_layer: "Large sales and EBITDA supported the price, but competition risk was rising.",
    decision_layer: "Buy only with a plan to defend the customer base.",
    mistake_layer: "Mistaking population growth for protection.",
    mental_model: "Growth attracts capital and capital destroys lazy moats.",
    source: "Operator_AskingPrice_KeyMetric.pdf",
  },
  {
    year: "2004",
    market: "Phoenix",
    asking_price: "$5.2M",
    sales: "$2.7M",
    ebitda: "$820K",
    cars_wk: "151,000",
    acres: "1.55",
    note: "High volume express-style site. Water reclaim and heat-season operations mattered more than normal underwriting.",
    wisdom_layer: "Every market had a hidden operating variable. In desert markets, water, shade, speed, and equipment uptime mattered.",
    data_layer: "Strong throughput and EBITDA, with market-specific operating diligence required.",
    decision_layer: "Good deal if maintenance and water systems are excellent.",
    mistake_layer: "Using a generic checklist in a market with special operating constraints.",
    mental_model: "Local constraints decide the real multiple.",
    source: "Operator_AskingPrice_KeyMetric.pdf",
  },
  {
    year: "2007",
    market: "Florida",
    asking_price: "$5.2M",
    sales: "$2.0M",
    ebitda: "$610K",
    cars_wk: "120,000",
    acres: "1.05",
    note: "Asking price felt stretched. Seller emphasized land value and future upside more than current cash flow.",
    wisdom_layer: "A seller's story is not cash flow. Future-proofing required separating proof from hope.",
    data_layer: "Price was high relative to EBITDA compared with cleaner operator records.",
    decision_layer: "Keep in the file, but do not chase without a lower basis.",
    mistake_layer: "Paying for the seller's upside twice.",
    mental_model: "Price is a fact. Upside is a hypothesis.",
    source: "2007_FL_ExpressWash_$5.2M_120kCars.pdf",
  },
  {
    year: "2010",
    market: "Chicago",
    asking_price: "$3.7M",
    sales: "$1.8M",
    ebitda: "$430K",
    cars_wk: "88,000",
    acres: "0.95",
    note: "Older tunnel on strong corner. Winter salt demand created steady repeat traffic.",
    wisdom_layer: "The best thing your kids may inherit is not a wash. It is the rule for judging whether the wash deserves capital.",
    data_layer: "Moderate EBITDA, good seasonal demand, and a strategic corner location.",
    decision_layer: "Renovation could work if acquisition basis stays disciplined.",
    mistake_layer: "Letting nostalgia for an old asset become a reason to overinvest.",
    mental_model: "Separate the asset from the rule.",
    source: "Wisdom_Layer_2010s.pdf",
  },
  {
    year: "2013",
    market: "Charlotte",
    asking_price: "$4.4M",
    sales: "$2.3M",
    ebitda: "$690K",
    cars_wk: "126,000",
    acres: "1.40",
    note: "Population growth plus limited nearby express competition. Good candidate for recurring revenue program.",
    wisdom_layer: "A membership model works best when the location already has trust. Software should harvest loyalty, not invent it.",
    data_layer: "Strong EBITDA, healthy throughput, and room for subscription conversion.",
    decision_layer: "Attractive if customer data confirms repeat behavior.",
    mistake_layer: "Installing a membership program before earning customer trust.",
    mental_model: "Technology amplifies trust. It does not replace it.",
    source: "Wisdom_Layer_2010s.pdf",
  },
  {
    year: "2016",
    market: "Denver",
    asking_price: "$6.8M",
    sales: "$3.0M",
    ebitda: "$910K",
    cars_wk: "141,000",
    acres: "1.80",
    note: "Excellent site, but three private-equity-backed operators entered nearby submarkets.",
    wisdom_layer: "Moats get destroyed when capital finds the same simple story. The harder question is what remains after competition copies the visible parts.",
    data_layer: "Attractive trailing numbers with clear competitive pressure.",
    decision_layer: "Only buy with conservative assumptions and a defensive plan.",
    mistake_layer: "Using yesterday's EBITDA as if the market stayed frozen.",
    mental_model: "Visible moats invite imitation.",
    source: "Moats_Destroyed_Examples.pdf",
  },
  {
    year: "2019",
    market: "Nashville",
    asking_price: "$7.4M",
    sales: "$3.4M",
    ebitda: "$1.05M",
    cars_wk: "158,000",
    acres: "1.60",
    note: "Strong operator with clean systems, high traffic, and clear monthly plan opportunity.",
    wisdom_layer: "Great acquisitions had three proofs: current cash flow, defensible demand, and a management habit that could survive transition.",
    data_layer: "The strongest EBITDA record in the demo set with healthy car count.",
    decision_layer: "High-priority study record.",
    mistake_layer: "Assuming a smooth transition without preserving the operating routines.",
    mental_model: "Cash flow, demand, and transferability.",
    source: "Future_Proof_Operator_Notes.pdf",
  },
  {
    year: "2021",
    market: "Austin",
    asking_price: "$8.6M",
    sales: "$3.7M",
    ebitda: "$980K",
    cars_wk: "149,000",
    acres: "1.25",
    note: "Excellent demographic story, but asking price assumed continued multiple expansion.",
    wisdom_layer: "When everyone believes the same growth story, the deal must be judged by what goes wrong, not what goes right.",
    data_layer: "High sales and EBITDA, but asking price was aggressive.",
    decision_layer: "Good business, maybe not a good buy.",
    mistake_layer: "Confusing a great asset with a great acquisition.",
    mental_model: "Asset quality and purchase quality are different.",
    source: "Future_Proof_Operator_Notes.pdf",
  },
  {
    year: "2024",
    market: "Raleigh",
    asking_price: "$6.1M",
    sales: "$2.8M",
    ebitda: "$760K",
    cars_wk: "119,000",
    acres: "1.50",
    note: "Balanced deal profile. Good local demand, room for operational improvement, and no obvious single-point dependency.",
    wisdom_layer: "The cleanest deals are not always the loudest. A boring file with no fatal flaw can be better than a spectacular file with one hidden dependency.",
    data_layer: "Healthy EBITDA, reasonable throughput, and adequate land.",
    decision_layer: "Worth deeper diligence.",
    mistake_layer: "Ignoring quiet, durable deals because flashier markets look more exciting.",
    mental_model: "No fatal flaw is underrated.",
    source: "Future_Proof_Operator_Notes.pdf",
  },
];

let records = [];
let activeRecordId = null;

const els = {
  fileInput: document.getElementById("fileInput"),
  loadSampleBtn: document.getElementById("loadSampleBtn"),
  clearDataBtn: document.getElementById("clearDataBtn"),
  yearInput: document.getElementById("yearInput"),
  marketInput: document.getElementById("marketInput"),
  askingPriceInput: document.getElementById("askingPriceInput"),
  salesInput: document.getElementById("salesInput"),
  ebitdaInput: document.getElementById("ebitdaInput"),
  carsInput: document.getElementById("carsInput"),
  acresInput: document.getElementById("acresInput"),
  noteInput: document.getElementById("noteInput"),
  voiceBtn: document.getElementById("voiceBtn"),
  searchBtn: document.getElementById("searchBtn"),
  recordCount: document.getElementById("recordCount"),
  marketCount: document.getElementById("marketCount"),
  stateCount: document.getElementById("stateCount"),
  acreageCount: document.getElementById("acreageCount"),
  ebitdaCount: document.getElementById("ebitdaCount"),
  sourceList: document.getElementById("sourceList"),
  agentReadout: document.getElementById("agentReadout"),
  resultCount: document.getElementById("resultCount"),
  results: document.getElementById("results"),
  detailContent: document.getElementById("detailContent"),
  recordModal: document.getElementById("recordModal"),
  modalTitle: document.getElementById("modalTitle"),
  closeModalBtn: document.getElementById("closeModalBtn"),
  modalBackdrop: document.getElementById("modalBackdrop"),
  documentLibraryBtn: document.getElementById("documentLibraryBtn"),
  libraryModal: document.getElementById("libraryModal"),
  libraryBackdrop: document.getElementById("libraryBackdrop"),
  closeLibraryBtn: document.getElementById("closeLibraryBtn"),
  libraryContent: document.getElementById("libraryContent"),
  voiceStatus: document.getElementById("voiceStatus"),
};

function normalizeKey(key) {
  return String(key || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
}

function titleCase(value) {
  return String(value || "")
    .replace(/_/g, " ")
    .replace(/\w\S*/g, (word) => word[0].toUpperCase() + word.slice(1).toLowerCase());
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"' && inQuotes && next === '"') {
      cell += '"';
      i += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      row.push(cell);
      cell = "";
    } else if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && next === "\n") i += 1;
      row.push(cell);
      if (row.some((part) => part.trim())) rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += char;
    }
  }

  row.push(cell);
  if (row.some((part) => part.trim())) rows.push(row);
  if (!rows.length) return [];

  const headers = rows[0].map(normalizeKey);
  return rows.slice(1).map((values) => {
    const item = {};
    headers.forEach((header, index) => {
      item[header || `field_${index + 1}`] = values[index] ? values[index].trim() : "";
    });
    return item;
  });
}

function parseTxt(text) {
  return text
    .split(/\n\s*\n/g)
    .map((block, index) => block.trim())
    .filter(Boolean)
    .map((block, index) => ({
      market: firstMeaningfulLine(block) || `OCR note ${index + 1}`,
      note: block,
      wisdom_layer: block,
    }));
}

function firstMeaningfulLine(block) {
  return block
    .split(/\n/g)
    .map((line) => line.trim())
    .find((line) => line.length > 2);
}

function parseJson(text) {
  const parsed = JSON.parse(text);
  if (Array.isArray(parsed)) return parsed;
  if (Array.isArray(parsed.records)) return parsed.records;
  if (Array.isArray(parsed.carwashes)) return parsed.carwashes;
  return [parsed];
}

function pick(obj, keys) {
  for (const key of keys) {
    if (obj[key]) return obj[key];
  }
  return "";
}

function standardizeRecord(raw, source, index) {
  const normalized = {};
  Object.entries(raw || {}).forEach(([key, value]) => {
    normalized[normalizeKey(key)] = value == null ? "" : String(value).trim();
  });

  const year = pick(normalized, ["year", "date", "decade"]);
  const market = pick(normalized, ["market", "location", "city", "state", "region"]) || `Record ${index + 1}`;
  const state = normalizeState(pick(normalized, ["state", "state_code"])) || inferStateFromLocation(market);
  const askingPrice = pick(normalized, ["asking_price", "ask", "price", "estimated_asking_price"]);
  const sales = pick(normalized, ["sales", "revenue", "gross_sales", "annual_sales"]);
  const listedEbitda = pick(normalized, ["ebitda", "cash_flow", "earnings"]);
  const carsWk = pick(normalized, ["cars_per_year", "cars_year", "annual_cars", "cars_yr", "cars_wk", "cars_week", "cars_per_week", "cars"]);
  const name = pick(normalized, ["name", "title", "deal", "operator"]) || `${year || "Undated"} ${market}`;
  const listedAcres = pick(normalized, ["acres", "acreage", "lot_size_acres"]);
  const acreageProfile = acreageRead(listedAcres, normalized, {
    name,
    market,
    state,
    source,
  });
  const acres = acreageProfile.value;
  const ebitdaProfile = ebitdaRead(listedEbitda, {
    askingPrice,
    sales,
    carsWk,
    acres,
    name,
    market,
    state,
  });
  const ebitda = ebitdaProfile.value;
  const note = pick(normalized, ["note", "notes", "memo", "comments", "details", "description"]);
  const wisdom = pick(normalized, ["wisdom_layer", "wisdom", "lesson", "insight"]) || note;
  const decision = pick(normalized, ["decision_layer", "decision", "takeaway"]);
  const mistake = pick(normalized, ["mistake_layer", "mistake", "risk"]);
  const mentalModel = pick(normalized, ["mental_model", "model"]);
  const page = pick(normalized, ["page", "page_number"]);
  const fullText = pick(normalized, ["full_text", "ocr_text", "text"]);
  const excerpt = pick(normalized, ["excerpt", "source_excerpt"]);
  const externalResearch = pick(normalized, ["external_research", "research_note"]);
  const researchUrl = pick(normalized, ["research_url", "external_url", "url"]);
  const verificationStatus = pick(normalized, ["verification_status", "verification"]);
  const publicSummary = pick(normalized, ["public_summary", "verified_summary", "public_check"]);
  const website = pick(normalized, ["website", "site"]);
  const phone = pick(normalized, ["phone", "telephone"]);
  const sourceUrls = pick(normalized, ["source_urls", "public_sources"]);
  const trafficCount = pick(normalized, ["traffic_count", "traffic", "vpd", "aadt"]);
  const mapsUrl = pick(normalized, ["maps_url", "google_maps_url", "maps"]);
  const latitude = pick(normalized, ["latitude", "lat"]);
  const longitude = pick(normalized, ["longitude", "lon", "lng"]);

  const rawWithCanonical = {
    ...normalized,
    year,
    market,
    state,
    asking_price: askingPrice,
    sales,
    ebitda,
    ebitda_status: ebitdaProfile.status,
    cars_wk: carsWk,
    acres,
    acreage_status: acreageProfile.status,
    note,
    wisdom_layer: wisdom,
    decision_layer: decision,
    mistake_layer: mistake,
    mental_model: mentalModel,
    page,
    excerpt,
    external_research: externalResearch,
    research_url: researchUrl,
    verification_status: verificationStatus,
    public_summary: publicSummary,
    website,
    phone,
    source_urls: sourceUrls,
    traffic_count: trafficCount,
    maps_url: mapsUrl,
    latitude,
    longitude,
    full_text: fullText,
  };

  return {
    id: `${source}-${Date.now()}-${index}-${Math.random().toString(16).slice(2)}`,
    name,
    year,
    market,
    state,
    askingPrice,
    sales,
    ebitda,
    ebitdaStatus: ebitdaProfile.status,
    carsWk,
    acres,
    acreageStatus: acreageProfile.status,
    note,
    wisdom,
    decision,
    mistake,
    mentalModel,
    source,
    page,
    fullText,
    excerpt,
    externalResearch,
    researchUrl,
    verificationStatus,
    publicSummary,
    website,
    phone,
    sourceUrls,
    trafficCount,
    mapsUrl,
    latitude,
    longitude,
    raw: rawWithCanonical,
    searchText: Object.values(rawWithCanonical).join(" ").toLowerCase(),
  };
}

function acreageRead(value, normalized, context = {}) {
  const clean = String(value || "").trim();
  if (clean && !/^not listed/i.test(clean) && clean !== "-") {
    return {
      value: clean,
      status: /est|approx|~|range/i.test(clean) ? "Estimated site size" : "Listed site size",
    };
  }

  const text = [
    context.name,
    context.market,
    context.state,
    context.source,
    normalized.note,
    normalized.public_summary,
    normalized.full_text,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  let estimate = "Est. 0.8-1.6";
  if (/self[\s-]?serve|self service|coin|detail|hand wash/.test(text)) estimate = "Est. 0.3-0.9";
  else if (/gas|fuel|station|c-store|convenience/.test(text)) estimate = "Est. 0.4-1.2";
  else if (/express|tunnel|conveyor|membership|vacuum/.test(text)) estimate = "Est. 0.9-1.8";
  else if (/portfolio|multi[-\s]?site|three[-\s]?site|package/.test(text)) estimate = "Est. varies by site";

  return {
    value: estimate,
    status: "Estimated from car wash format; verify parcel acreage",
  };
}

function ebitdaRead(value, context = {}) {
  const clean = String(value || "").trim();
  if (clean && !/^not listed/i.test(clean) && clean !== "-") {
    return {
      value: clean,
      status: /est|approx|~|range/i.test(clean) ? "Estimated EBITDA" : "Listed EBITDA",
    };
  }

  const ask = moneyToNumber(context.askingPrice);
  const sales = moneyToNumber(context.sales);
  const cars = numericValue(context.carsWk);
  const acres = numericValue(context.acres);
  const text = [context.name, context.market, context.state].filter(Boolean).join(" ").toLowerCase();
  let estimate = 0;

  if (sales) estimate = sales * 0.24;
  else if (ask) estimate = ask / 6.5;
  else if (cars) estimate = cars * 3.25;
  else if (/express|tunnel|conveyor|membership/.test(text)) estimate = 360000;
  else if (/self[\s-]?serve|coin|hand wash|detail/.test(text)) estimate = 140000;
  else if (acres >= 1.4) estimate = 320000;
  else estimate = 240000;

  return {
    value: `Est. ${formatMoneyShort(String(Math.round(estimate)))}`,
    status: "Estimated EBITDA; verify against seller financials",
  };
}

function isVerified(record) {
  return String(record.verificationStatus || "").toLowerCase().includes("verified");
}

function displayValue(value, fallback = "Not listed") {
  return value ? value : fallback;
}

function normalizeState(value) {
  const compact = String(value || "").trim().toLowerCase().replace(/[^a-z]/g, "");
  if (!compact) return "";
  if (compact.length === 2 && STATE_CODES.has(compact.toUpperCase())) return compact.toUpperCase();
  return STATE_NAME_TO_CODE[compact] || "";
}

function inferStateFromLocation(location) {
  const text = String(location || "");
  const codeMatch = text.match(/\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)\b/);
  if (codeMatch) return codeMatch[1];
  return normalizeState(text);
}

function moneyToNumber(value) {
  const raw = String(value || "").toLowerCase();
  const text = raw.replace(/[$,\s]/g, "");
  const match = text.match(/(\d+(\.\d+)?)/);
  if (!match) return 0;
  const number = Number(match[1]);
  if (/\d(?:\.\d+)?\s*(m|million)\b/i.test(raw)) return number * 1000000;
  if (/\d(?:\.\d+)?\s*k\b/i.test(raw)) return number * 1000;
  return number;
}

function numericValue(value) {
  const match = String(value || "").replace(/,/g, "").match(/\d+(\.\d+)?/);
  return match ? Number(match[0]) : 0;
}

function formatMoneyShort(value) {
  const number = moneyToNumber(value);
  if (!number) return value || "-";
  if (number >= 1000000) return `$${(number / 1000000).toFixed(number % 1000000 ? 1 : 0)}M`;
  if (number >= 1000) return `$${Math.round(number / 1000)}K`;
  return `$${number}`;
}

function metricValue(value, type = "text") {
  if (!value || value === "-") return "Not provided";
  if (type === "money" && /est|approx|~/i.test(String(value))) return `Est. ${formatMoneyShort(value)}`;
  const formatted = type === "money" ? formatMoneyShort(value) : value;
  return formatted && formatted !== "-" ? formatted : "Not provided";
}

function tokenize(text) {
  return String(text || "")
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((token) => token.length > 1);
}

function scoreRecord(record, queryTokens, selectedMarket, selectedYear, maxAskingPrice, criteria = {}) {
  const stateQuery = normalizeState(selectedMarket);
  if (stateQuery && record.state !== stateQuery) return null;
  if (selectedMarket && !stateQuery && !fieldMatches(record.market, selectedMarket) && !fieldMatches(record.name, selectedMarket)) return null;
  if (selectedYear && !fieldMatches(record.year, selectedYear)) return null;
  if (maxAskingPrice && moneyToNumber(record.askingPrice) > maxAskingPrice) return null;
  if (!moneyMatches(record.askingPrice, criteria.askingPrice)) return null;
  if (!moneyMatches(record.sales, criteria.sales)) return null;
  if (!moneyMatches(record.ebitda, criteria.ebitda)) return null;
  if (!numberMatches(record.carsWk, criteria.carsWk)) return null;
  if (!numberMatches(record.acres, criteria.acres)) return null;

  const noteText = [record.name, record.market, record.state, record.note, record.wisdom, record.decision, record.mistake, record.mentalModel, record.publicSummary].join(" ");
  if (criteria.note && !tokenMatches(noteText, criteria.note)) return null;

  let score = 0;
  const haystack = record.searchText;

  queryTokens.forEach((token) => {
    if (String(record.name).toLowerCase().includes(token)) score += 8;
    if (String(record.market).toLowerCase().includes(token)) score += 8;
    if (String(record.state).toLowerCase() === token) score += 8;
    if (String(record.year).includes(token)) score += 5;
    if (String(record.name).toLowerCase().includes(token)) score += 5;
    if (haystack.includes(token)) score += 2;
  });

  if (!queryTokens.length) score = recordQualityScore(record);
  if (moneyToNumber(record.ebitda) >= 500000) score += 2;
  if (numericValue(record.carsWk) >= 10000) score += 2;
  if (record.wisdom) score += 1;

  return { record, score };
}

function inferYearFromQuery(query) {
  const text = String(query || "");
  const exact = text.match(/\b(19|20)\d{2}\b/);
  if (exact) return exact[0];
  const decade = text.match(/\b(1990s|2000s|2010s|2020s)\b/i);
  if (!decade) return "";
  const prefix = decade[1].slice(0, 3);
  return records.find((record) => String(record.year).startsWith(prefix))?.year || "";
}

function inferMarketFromQuery(query) {
  const lower = String(query || "").toLowerCase();
  const stateQuery = normalizeState(lower);
  if (stateQuery) return stateQuery;
  return records.find((record) => lower.includes(String(record.market).toLowerCase()))?.market || "";
}

function getSearchCriteria() {
  return {
    year: els.yearInput.value.trim(),
    market: els.marketInput.value.trim(),
    askingPrice: els.askingPriceInput.value.trim(),
    sales: els.salesInput.value.trim(),
    ebitda: els.ebitdaInput.value.trim(),
    carsWk: els.carsInput.value.trim(),
    acres: els.acresInput.value.trim(),
    note: els.noteInput.value.trim(),
  };
}

function fieldMatches(value, query) {
  if (!query) return true;
  return String(value || "").toLowerCase().includes(query.toLowerCase());
}

function tokenMatches(value, query) {
  const tokens = tokenize(query);
  if (!tokens.length) return true;
  const text = String(value || "").toLowerCase();
  return tokens.every((token) => text.includes(token));
}

function moneyMatches(value, query) {
  if (!query) return true;
  if (fieldMatches(value, query)) return true;
  const valueNumber = moneyToNumber(value);
  const queryNumber = moneyToNumber(query);
  if (!valueNumber || !queryNumber) return false;
  return valueNumber <= queryNumber || Math.abs(valueNumber - queryNumber) / Math.max(valueNumber, queryNumber) < 0.08;
}

function numberMatches(value, query) {
  if (!query) return true;
  if (fieldMatches(value, query)) return true;
  const valueNumber = numericValue(value);
  const queryNumber = numericValue(query);
  if (!valueNumber || !queryNumber) return false;
  return valueNumber >= queryNumber || Math.abs(valueNumber - queryNumber) / Math.max(valueNumber, queryNumber) < 0.08;
}

function recordQualityScore(record) {
  let score = 1;
  if (record.state) score += 8;
  if (record.market && !/^record \d+$/i.test(record.market)) score += 8;
  if (hasExactStreetAddress(record.market)) score += 8;
  if (record.phone) score += 8;
  if (usableWebsiteUrl(record)) score += 8;
  if (record.sourceUrls || record.researchUrl) score += 3;
  if (moneyToNumber(record.askingPrice) >= 100000) score += 7;
  if (moneyToNumber(record.sales) >= 100000) score += 4;
  if (moneyToNumber(record.ebitda) >= 100000) score += 4;
  if (numericValue(record.acres)) score += 3;
  if (numericValue(record.carsWk)) score += 3;
  if (record.externalResearch) score += 6;
  if (isVerified(record)) score += 5;
  if (/opportunity|specialty for sale|available/i.test(record.name || "")) score -= 2;
  if (/lead|opportunity/i.test(record.name || "") && !record.phone && !usableWebsiteUrl(record)) score -= 10;
  if (!record.market) score -= 6;
  return score;
}

function combinedSearchText(criteria) {
  return Object.values(criteria).filter(Boolean).join(" ");
}

function runSearch() {
  const criteria = getSearchCriteria();
  const query = combinedSearchText(criteria);
  const selectedMarket = criteria.market || inferMarketFromQuery(query);
  const selectedYear = criteria.year || inferYearFromQuery(query);
  const limit = 10;
  const queryTokens = tokenize(query).filter(
    (token) => !["find", "show", "what", "which", "did", "the", "and", "with", "car", "wash", "washes"].includes(token)
  );

  const matches = records
    .map((record) => scoreRecord(record, queryTokens, selectedMarket, selectedYear, 0, criteria))
    .filter(Boolean)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);

  renderResults(matches);
  renderReadout(matches, query, selectedMarket, selectedYear, 0);
}

function renderResults(matches) {
  try {
    renderResultsUnsafe(matches);
  } catch (error) {
    els.resultCount.textContent = `${matches.length} shown`;
    els.results.innerHTML = `<div class="empty-state">Results are loaded. Display error: ${escapeHtml(error.message || String(error))}</div>`;
  }
}

function renderResultsUnsafe(matches) {
  els.resultCount.textContent = `${matches.length} shown`;
  els.results.innerHTML = "";

  if (!records.length) {
    els.results.innerHTML = `<div class="empty-state">Upload car wash files or load the demo knowledge base.</div>`;
    return;
  }

  if (!matches.length) {
    els.results.innerHTML = `<div class="empty-state">No matches found. Try a broader prompt or remove filters.</div>`;
    return;
  }

  els.results.innerHTML = matches
    .map(({ record, score }) => resultCardHtml(record, score))
    .join("");
  els.results.querySelectorAll(".result-card").forEach((card) => {
    card.addEventListener("click", () => selectRecord(card.dataset.id));
  });
}

function renderReadout(matches, query, market, year, maxAskingPrice) {
  if (!els.agentReadout) return;

  if (!records.length) {
    els.agentReadout.textContent = "No records are loaded yet. Once the car wash data is loaded, Scout will rank opportunities from that private dataset.";
    return;
  }

  if (!query && !market && !year && !maxAskingPrice) {
    els.agentReadout.textContent =
      `${records.length.toLocaleString()} screened records are loaded. Use the table filters or speak an acquisition thesis, then press Search.`;
    return;
  }

  if (!matches.length) {
    els.agentReadout.textContent = "No screened records matched that filter combination. Broaden the state, year, price, or note field.";
    return;
  }

  const top = matches[0].record;
  const filters = [
    market ? `market ${market}` : "",
    year ? `year ${year}` : "",
    maxAskingPrice ? `asking price under ${formatMoneyShort(String(maxAskingPrice))}` : "",
  ].filter(Boolean);

  els.agentReadout.textContent = `Top screen: ${top.name || "Car wash record"} at ${top.market}. ${investmentReadout(top)}${filters.length ? ` Filtered by ${filters.join(", ")}.` : ""}`;
}

function selectRecord(id, rerender = true) {
  activeRecordId = id;
  const record = records.find((item) => item.id === id);
  if (!record) return;

  const detailFields = [
    ["Year", metricValue(record.year)],
    ["Address", metricValue(record.market)],
    ["Asking Price", metricValue(record.askingPrice, "money")],
    ["Sales", metricValue(record.sales, "money")],
    ["EBITDA", metricValue(record.ebitda, "money")],
    ["Cars/Yr", metricValue(record.carsWk)],
    ["Traffic", metricValue(record.trafficCount)],
    ["Acres", metricValue(record.acres)],
    ["Note", record.publicSummary || record.note || "Review the address, contact fields, and seller-provided record before outreach."],
  ]
    .map(
      ([label, value]) => `
        <div class="detail-field${label === "Note" ? " is-note" : ""}">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value || "Not provided")}</strong>
        </div>
      `
    )
    .join("");
  const scoutInsight = buildScoutInsight(record);
  const executiveRead = buildExecutiveRead(record);
  const contactActions = contactActionsHtml(record);
  const sourceActions = sourceActionsHtml(record);
  const websiteUrl = usableWebsiteUrl(record);
  const mapsUrl = mapsSearchUrl(record);
  const contactHeadline = record.phone || (websiteUrl ? cleanUrlLabel(websiteUrl) : "") || (mapsUrl ? "Exact map ready" : "Contact not listed");
  const sourceLabel = recordSourceLabel(record);
  const confidence = confidenceLabel(record);
  const tier = investmentTier(record, recordQualityScore(record));
  const contactFields = [
    ["Address", displayValue(record.market)],
    record.phone ? ["Phone", `<a href="tel:${escapeHtml(phoneHref(record.phone))}">${escapeHtml(record.phone)}</a>`, true] : null,
    websiteUrl ? ["Website", `<a href="${escapeHtml(websiteUrl)}" target="_blank" rel="noreferrer">${escapeHtml(cleanUrlLabel(websiteUrl))}</a>`, true] : null,
    record.trafficCount ? ["Traffic", escapeHtml(record.trafficCount), true] : null,
  ]
    .filter(Boolean)
    .map(([label, value, isHtml]) => `<div><span>${escapeHtml(label)}</span><strong>${isHtml ? value : escapeHtml(value)}</strong></div>`)
    .join("");

  els.modalTitle.textContent = record.name || `${record.year || "Undated"} ${record.market}`;
  els.detailContent.className = "detail-content";
  els.detailContent.innerHTML = `
    <div class="detail-hero">
      <div>
        <div class="memo-strip">
          <span>${escapeHtml(tier)}</span>
          <span>${escapeHtml(sourceLabel)}</span>
          <span>${escapeHtml(confidence)}</span>
        </div>
        <div class="detail-title">${escapeHtml(record.name || "Car Wash Opportunity")}</div>
        <p>${escapeHtml([record.market, record.state, record.year || "Undated"].filter(Boolean).join(" | ") || "Location needs verification")}</p>
      </div>
      ${record.askingPrice ? `<div class="price-box"><span>Asking</span><strong>${escapeHtml(formatMoneyShort(record.askingPrice))}</strong></div>` : ""}
    </div>
    <div class="detail-layout">
      <div class="deal-report">
        <section class="executive-read">
          <div class="exec-card">
            <span>Data Grade</span>
            <strong>${escapeHtml(executiveRead.dataGrade)}</strong>
            <p>${escapeHtml(executiveRead.dataNote)}</p>
          </div>
          <div class="exec-card">
            <span>Location Grade</span>
            <strong>${escapeHtml(executiveRead.locationGrade)}</strong>
            <p>${escapeHtml(executiveRead.locationNote)}</p>
          </div>
          <div class="exec-card">
            <span>Valuation Read</span>
            <strong>${escapeHtml(executiveRead.valuationHeadline)}</strong>
            <p>${escapeHtml(executiveRead.valuationNote)}</p>
          </div>
          <div class="exec-card">
            <span>Diligence Gap</span>
            <strong>${escapeHtml(executiveRead.diligenceHeadline)}</strong>
            <p>${escapeHtml(executiveRead.diligenceNote)}</p>
          </div>
        </section>
        <div class="detail-field-grid">${detailFields}</div>
        <section class="verified-info">
          <div class="verified-info-head">
            <span>Contact & Location</span>
            <strong>${escapeHtml(contactHeadline)}</strong>
          </div>
          <div class="verified-info-grid">
            ${contactFields}
          </div>
          <div class="contact-actions">${contactActions}</div>
          <p>${escapeHtml(record.publicSummary || record.externalResearch || professionalRecordSummary(record))}</p>
          ${sourceActions ? `<div class="source-actions">${sourceActions}</div>` : ""}
        </section>
        <div class="layer-grid">
          <section><span>Decision Read</span><p>${escapeHtml(scoutInsight.decision)}</p></section>
          <section><span>Risk Read</span><p>${escapeHtml(scoutInsight.risk)}</p></section>
          <section><span>Next Check</span><p>${escapeHtml(scoutInsight.nextCheck)}</p></section>
        </div>
      </div>
      <aside class="scout-bot" aria-label="Scout AI location insight">
        <div class="bot-header">
          <span>Scout AI</span>
          <strong>Location Read</strong>
        </div>
        <div class="bot-message">
          <p>${escapeHtml(scoutInsight.location)}</p>
        </div>
        <div class="bot-message is-answer">
          <p>${escapeHtml(scoutInsight.answer)}</p>
        </div>
        <div class="bot-facts">
          ${scoutInsight.facts.map((fact) => `<span>${escapeHtml(fact)}</span>`).join("")}
        </div>
      </aside>
    </div>
  `;
  els.recordModal.hidden = false;
  document.body.classList.add("modal-open");

  if (rerender) runSearch();
}

function buildScoutInsight(record) {
  const facts = [];
  if (record.market) facts.push(record.market);
  if (record.state) facts.push(`State: ${record.state}`);
  if (record.phone) facts.push(`Phone: ${record.phone}`);
  const websiteUrl = usableWebsiteUrl(record);
  if (websiteUrl) facts.push(cleanUrlLabel(websiteUrl));
  if (record.askingPrice) facts.push(`Ask: ${formatMoneyShort(record.askingPrice)}`);
  if (record.sales) facts.push(`Sales: ${formatMoneyShort(record.sales)}`);
  if (record.ebitda) facts.push(`EBITDA: ${metricValue(record.ebitda, "money")}`);
  if (record.ebitdaStatus) facts.push(record.ebitdaStatus);
  if (record.acres) facts.push(`Site: ${record.acres} acres`);
  if (record.acreageStatus) facts.push(record.acreageStatus);
  if (record.carsWk) facts.push(`Cars/Yr: ${record.carsWk}`);
  if (record.trafficCount) facts.push(record.trafficCount);

  const location = record.publicSummary
    ? record.publicSummary
    : record.market
    ? `${record.market} looks like the core location to evaluate. I would judge it by visibility, traffic flow, nearby competition, access, and whether the car wash sits in the normal daily path of local customers.`
    : "The scan did not give a clean location. I would treat this as incomplete until the address or market is confirmed.";

  const positiveSignals = [];
  if (moneyToNumber(record.askingPrice) >= 1000000) positiveSignals.push("meaningful sale price");
  if (moneyToNumber(record.sales) >= 500000) positiveSignals.push("reported revenue");
  if (moneyToNumber(record.ebitda) >= 100000) positiveSignals.push("cash-flow detail");
  if (numericValue(record.carsWk)) positiveSignals.push("car count or traffic signal");
  if (numericValue(record.acres)) positiveSignals.push("site-size detail");

  const answer = positiveSignals.length
    ? `This record has usable deal signals: ${positiveSignals.join(", ")}. It is worth keeping in the Scout because those facts help compare price, demand, and location quality.`
    : "This record is useful mainly as a lead. The scan does not show enough clean numbers yet, so I would verify price, revenue, traffic, and operator notes before treating it as a serious comp.";

  const decision = isVerified(record)
    ? "Stronger record because the location was checked against a public source."
    : "Useful lead. Confirm the important numbers against the original file or a public listing before relying on it.";

  const risk = record.state && record.market
    ? "Main risk is scan accuracy on financials and whether the address/title still matches the current operator."
    : "Main risk is incomplete location data.";

  const nextCheck = record.askingPrice || record.sales || record.ebitda
    ? "Compare asking price to sales, EBITDA, site size, and local competition."
    : "Find asking price, revenue, traffic count, and current operator status.";

  return {
    location,
    answer,
    decision,
    risk,
    nextCheck,
    facts: facts.slice(0, 7),
  };
}

function buildExecutiveRead(record) {
  const hasAddress = hasExactStreetAddress(record.market);
  const hasContact = Boolean(record.phone || usableWebsiteUrl(record) || mapsSearchUrl(record));
  const hasFinancials = Boolean(moneyToNumber(record.askingPrice) || moneyToNumber(record.sales) || moneyToNumber(record.ebitda));
  const hasOperating = Boolean(numericValue(record.carsWk) || record.trafficCount);
  const hasListedAcres = record.acreageStatus === "Listed site size";
  const hasListedEbitda = record.ebitdaStatus === "Listed EBITDA";
  const acreageEstimated = /estimated/i.test(record.acreageStatus || record.acres || "");

  let dataPoints = 0;
  if (hasAddress) dataPoints += 2;
  if (hasContact) dataPoints += 2;
  if (moneyToNumber(record.askingPrice)) dataPoints += 2;
  if (moneyToNumber(record.sales)) dataPoints += 1;
  if (moneyToNumber(record.ebitda)) dataPoints += hasListedEbitda ? 2 : 1;
  if (hasListedAcres) dataPoints += 2;
  else if (record.acres) dataPoints += 1;
  if (hasOperating) dataPoints += 1;

  const dataGrade = dataPoints >= 9 ? "A" : dataPoints >= 7 ? "B+" : dataPoints >= 5 ? "B" : dataPoints >= 3 ? "C" : "Lead";
  const dataNote = hasFinancials
    ? "Usable underwriting fields are present. Confirm scanned figures before using this as a final comp."
    : "Location lead with limited financial detail. Use it for market coverage, not valuation by itself.";

  let locationPoints = 0;
  if (hasAddress) locationPoints += 3;
  if (mapsSearchUrl(record)) locationPoints += 2;
  if (record.phone || usableWebsiteUrl(record)) locationPoints += 2;
  if (record.trafficCount) locationPoints += 1;
  if (numericValue(record.acres)) locationPoints += 1;
  const locationGrade = locationPoints >= 8 ? "Prime" : locationPoints >= 6 ? "Strong" : locationPoints >= 4 ? "Review" : "Unverified";
  const locationNote = hasAddress
    ? `${record.market} is map-ready. Judge visibility, ingress/egress, traffic generators, and nearby competition.`
    : "Needs a street address before it belongs in a serious investment screen.";

  const ask = moneyToNumber(record.askingPrice);
  const ebitda = moneyToNumber(record.ebitda);
  const sales = moneyToNumber(record.sales);
  const acres = numericValue(record.acres);
  const ebitdaMultiple = ask && ebitda ? ask / ebitda : 0;
  const salesMultiple = ask && sales ? ask / sales : 0;
  const pricePerAcre = ask && acres ? ask / acres : 0;
  let valuationHeadline = "Needs numbers";
  let valuationNote = "Find asking price, sales, EBITDA, and confirmed parcel acreage before making a valuation call.";
  if (ebitdaMultiple) {
    valuationHeadline = `${ebitdaMultiple.toFixed(1)}x EBITDA`;
    valuationNote = `Asking price implies roughly ${ebitdaMultiple.toFixed(1)}x ${hasListedEbitda ? "listed" : "estimated"} EBITDA${pricePerAcre ? ` and ${formatMoneyShort(String(pricePerAcre))}/acre` : ""}. Compare to local operator quality and capex needs.`;
  } else if (salesMultiple) {
    valuationHeadline = `${salesMultiple.toFixed(1)}x sales`;
    valuationNote = `EBITDA is missing, so this is a revenue-based read only. Confirm margins, labor, utilities, and membership mix.`;
  } else if (pricePerAcre) {
    valuationHeadline = `${formatMoneyShort(String(pricePerAcre))}/acre`;
    valuationNote = `Price-per-acre is a rough land/site signal. It is not enough without revenue or EBITDA.`;
  }

  const gaps = [];
  if (!moneyToNumber(record.ebitda)) gaps.push("EBITDA");
  else if (!hasListedEbitda) gaps.push("seller EBITDA confirmation");
  if (!moneyToNumber(record.sales)) gaps.push("sales");
  if (!moneyToNumber(record.askingPrice)) gaps.push("asking price");
  if (!hasListedAcres) gaps.push(acreageEstimated ? "parcel acreage verification" : "acres");
  if (!record.trafficCount && !numericValue(record.carsWk)) gaps.push("traffic/wash volume");
  if (!hasContact) gaps.push("public contact");
  const diligenceHeadline = gaps.length ? `${gaps.length} checks` : "Tight record";
  const diligenceNote = gaps.length ? `Next diligence: ${gaps.slice(0, 5).join(", ")}.` : "Enough core fields exist for a first-pass investor conversation.";

  return {
    dataGrade,
    dataNote,
    locationGrade,
    locationNote,
    valuationHeadline,
    valuationNote,
    diligenceHeadline,
    diligenceNote,
  };
}

function cleanUrlLabel(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function phoneHref(phone) {
  return String(phone || "").replace(/[^0-9+]/g, "");
}

function usableWebsiteUrl(record) {
  const url = String(record.website || "").trim();
  if (!/^https?:\/\//i.test(url)) return "";
  try {
    const parsed = new URL(url);
    const hostname = parsed.hostname.replace(/^www\./, "").toLowerCase();
    const normalizedUrl = `${parsed.protocol}//${hostname}${parsed.pathname}`.replace(/\/$/, "").toLowerCase();
    const nonContactDomains = [
      "cbre.us",
      "crexi.com",
      "loopnet.com",
      "showcase.com",
      "whereorg.com",
      "mapquest.com",
      "loc8nearme.com",
      "manta.com",
      "bizbuysell.com",
    ];
    if (nonContactDomains.some((domain) => hostname === domain || hostname.endsWith(`.${domain}`))) return "";
    const failedAuditUrls = [
      "http://hightidecarwash.com",
      "http://hemetcarwash.com",
      "https://palmdalespeedwash.com",
      "https://www.palmdalespeedwash.com",
      "https://sierrawash.com/locations/kietzke-ln",
      "https://allamericanexpresscarwash.com/chino-spectrum",
    ];
    if (failedAuditUrls.includes(normalizedUrl)) return "";
    const failedAuditHosts = ["hightidecarwash.com", "hemetcarwash.com"];
    if (failedAuditHosts.includes(hostname)) return "";
    return url;
  } catch {
    return "";
  }
}

function hasExactStreetAddress(value) {
  const text = String(value || "");
  return /\b\d{2,6}\s+[A-Za-z0-9 .'-]{2,}\b/.test(text) && /\b[A-Z]{2}\s*\d{0,5}\b/.test(text);
}

function mapsSearchUrl(record) {
  if (record.mapsUrl && /^https?:\/\//i.test(record.mapsUrl)) return record.mapsUrl;
  if (record.latitude && record.longitude) {
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${record.latitude},${record.longitude}`)}`;
  }
  if (!hasExactStreetAddress(record.market)) return "";
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(record.market)}`;
}

function contactSummary(record) {
  const parts = [];
  if (record.phone) parts.push(record.phone);
  const websiteUrl = usableWebsiteUrl(record);
  if (websiteUrl) parts.push(cleanUrlLabel(websiteUrl));
  if (mapsSearchUrl(record)) parts.push("Exact Maps");
  return parts.length ? parts.join(" | ") : "Contact not listed";
}

function compactRecordText(record, score) {
  return [
    record.name || "Car Wash Opportunity",
    [record.market, record.state, record.year || "Undated"].filter(Boolean).join(" | "),
    contactSummary(record),
    `Fit ${score}`,
    `Ask ${metricValue(record.askingPrice, "money")} | Sales ${metricValue(record.sales, "money")} | EBITDA ${metricValue(record.ebitda, "money")} | Cars/Yr ${metricValue(record.carsWk)} | Acres ${metricValue(record.acres)}`,
    record.publicSummary || record.note || record.wisdom || "Open record for details.",
  ]
    .filter(Boolean)
    .join("\n");
}

function recordSourceLabel(record) {
  if (String(record.id || "").startsWith("public-map-")) return "Public support";
  if (/scanned|ocr|document|bin/i.test(record.source || "")) return "Scanned paperwork";
  return "Imported record";
}

function confidenceLabel(record) {
  const hasContact = Boolean(record.phone || usableWebsiteUrl(record) || mapsSearchUrl(record));
  const hasFinancials = Boolean(moneyToNumber(record.askingPrice) || moneyToNumber(record.sales) || moneyToNumber(record.ebitda));
  const hasListedNumbers = record.ebitdaStatus === "Listed EBITDA" || record.acreageStatus === "Listed site size";
  if (hasContact && hasFinancials && hasListedNumbers) return "Verified Fields";
  if (hasContact && hasFinancials) return "Diligence Ready";
  if (hasContact || hasFinancials) return "Verify Before Outreach";
  return "Lead only";
}

function investmentTier(record, score) {
  const executiveRead = buildExecutiveRead(record);
  const hasFinancials = Boolean(moneyToNumber(record.askingPrice) || moneyToNumber(record.sales) || moneyToNumber(record.ebitda));
  if (score >= 70 && hasFinancials && executiveRead.locationGrade !== "Unverified") return "Priority Screen";
  if (score >= 55 && executiveRead.locationGrade !== "Unverified") return "Review Queue";
  if (String(record.id || "").startsWith("public-map-")) return "Market Coverage";
  return "Location Lead";
}

function investmentReadout(record) {
  const parts = [];
  if (moneyToNumber(record.askingPrice)) parts.push(`ask ${formatMoneyShort(record.askingPrice)}`);
  if (moneyToNumber(record.ebitda)) parts.push(`EBITDA ${metricValue(record.ebitda, "money")}`);
  if (numericValue(record.acres)) parts.push(`${metricValue(record.acres)} acres`);
  const source = recordSourceLabel(record).toLowerCase();
  return parts.length
    ? `${parts.join(", ")}. Source: ${source}; verify seller numbers before underwriting.`
    : `Source: ${source}. Treat as a location lead until seller financials are confirmed.`;
}

function resultCardHtml(record, score) {
  const location = [record.market, record.state, record.year || "Undated"].filter(Boolean).join(" | ") || "Location lookup ready";
  const note = record.publicSummary || record.note || record.wisdom || "Open record for details.";
  const executiveRead = buildExecutiveRead(record);
  const acreageClass = /estimated/i.test(record.acreageStatus || "") ? " is-estimated" : "";
  const tier = investmentTier(record, score);
  const sourceLabel = recordSourceLabel(record);
  const confidence = confidenceLabel(record);
  return `
    <button type="button" class="result-card${record.id === activeRecordId ? " is-active" : ""}" data-id="${escapeHtml(record.id)}">
      <div class="opportunity-bar">
        <span>${escapeHtml(tier)}</span>
        <span>${escapeHtml(sourceLabel)}</span>
        <span>${escapeHtml(confidence)}</span>
      </div>
      <div class="result-title">
        <span>
          <strong>${escapeHtml(record.name || "Car Wash Opportunity")}</strong>
          <small>${escapeHtml(location)}</small>
          <small class="contact-line">${escapeHtml(contactSummary(record))}</small>
        </span>
        <span class="score-pill">Fit ${escapeHtml(score)}</span>
      </div>
      <div class="signal-row">
        <span>Data ${escapeHtml(executiveRead.dataGrade)}</span>
        <span>${escapeHtml(executiveRead.locationGrade)} Location</span>
        <span class="${acreageClass}">${escapeHtml(acreageBadge(record))}</span>
      </div>
      <div class="deal-grid">
        <span><b>Ask</b>${escapeHtml(metricValue(record.askingPrice, "money"))}</span>
        <span><b>Sales</b>${escapeHtml(metricValue(record.sales, "money"))}</span>
        <span><b>EBITDA</b>${escapeHtml(metricValue(record.ebitda, "money"))}</span>
        <span><b>Cars/Yr</b>${escapeHtml(metricValue(record.carsWk))}</span>
        <span><b>Traffic</b>${escapeHtml(metricValue(record.trafficCount))}</span>
        <span><b>Acres</b>${escapeHtml(metricValue(record.acres))}</span>
      </div>
      <p class="record-note">${escapeHtml(note)}</p>
    </button>
  `;
}

function acreageBadge(record) {
  return /estimated/i.test(record.acreageStatus || record.acres || "") ? "Estimated acreage" : "Listed acreage";
}

function contactActionsHtml(record) {
  const actions = [];
  const websiteUrl = usableWebsiteUrl(record);
  const mapsUrl = mapsSearchUrl(record);
  if (record.phone) {
    actions.push(`<a href="tel:${escapeHtml(phoneHref(record.phone))}">Call</a>`);
  }
  if (websiteUrl) {
    actions.push(`<a href="${escapeHtml(websiteUrl)}" target="_blank" rel="noreferrer">Website</a>`);
  }
  if (mapsUrl) {
    actions.push(`<a href="${escapeHtml(mapsUrl)}" target="_blank" rel="noreferrer">Open Maps</a>`);
  }
  return actions.length ? actions.join("") : `<span class="contact-empty">Contact not listed</span>`;
}

function professionalRecordSummary(record) {
  const location = record.market || "this location";
  const facts = [
    record.askingPrice ? `asking price ${formatMoneyShort(record.askingPrice)}` : "",
    record.sales ? `sales ${formatMoneyShort(record.sales)}` : "",
    record.ebitda ? `EBITDA ${formatMoneyShort(record.ebitda)}` : "",
    record.acres ? `${record.acres} acres` : "",
  ].filter(Boolean);
  return `${record.name || "Car wash record"} in ${location}${facts.length ? ` with ${facts.join(", ")}` : ""}. Use exact contact links only when a street address, phone, website, or map coordinate is listed.`;
}

function closeModal() {
  els.recordModal.hidden = true;
  if (!els.libraryModal || els.libraryModal.hidden) document.body.classList.remove("modal-open");
}

function documentForSource(source) {
  const cleanSource = String(source || "").split("|")[0].trim();
  if (!cleanSource) return null;
  const pdfName = cleanSource.replace(/\.txt$/i, ".pdf").replace(/_ocr\.pdf$/i, ".pdf");
  return documentLibrary.find((doc) => doc.file_name === pdfName || doc.title === pdfName.replace(/\.pdf$/i, "") || String(doc.text_url || "").endsWith(`/${cleanSource}`)) || null;
}

function recordPageNumber(record) {
  const match = String(record.page || "").match(/\d+/);
  return match ? match[0] : "";
}

function sourceActionsHtml(record) {
  const doc = documentForSource(record.source);
  if (!doc || !doc.pdf_url) return "";
  const page = recordPageNumber(record);
  const pdfHref = encodeURI(doc.pdf_url);
  const pageHref = page ? `${pdfHref}#page=${encodeURIComponent(page)}` : pdfHref;
  const textHref = doc.text_url ? encodeURI(doc.text_url) : "";
  return [
    `<a class="source-link" href="${escapeHtml(pageHref)}" target="_blank" rel="noreferrer">Open Source Page</a>`,
    `<a class="source-link ghost-link" href="${escapeHtml(pdfHref)}" target="_blank" rel="noreferrer">Open Full PDF</a>`,
    textHref ? `<a class="source-link ghost-link" href="${escapeHtml(textHref)}" target="_blank" rel="noreferrer">OCR Text</a>` : "",
  ]
    .filter(Boolean)
    .join("");
}

function openLibrary() {
  renderDocumentLibrary();
  els.libraryModal.hidden = false;
  document.body.classList.add("modal-open");
}

function closeLibrary() {
  els.libraryModal.hidden = true;
  if (!els.recordModal || els.recordModal.hidden) document.body.classList.remove("modal-open");
}

function renderDocumentLibrary(filter = "") {
  if (!els.libraryContent) return;
  const query = String(filter || "").trim().toLowerCase();
  const docs = normalizedDocumentLibrary().filter((doc) => documentMatchesQuery(doc, query));
  const totalPages = documentLibrary.reduce((sum, doc) => sum + Number(doc.page_count || 0), 0);
  const evidencePages = documentLibrary.reduce((sum, doc) => sum + Number(doc.evidence_page_count || 0), 0);
  const evidenceRows = documentLibrary.reduce((sum, doc) => sum + Number(doc.evidence_row_count || 0), 0);
  const galleryPages = documentLibrary.reduce((sum, doc) => sum + (Array.isArray(doc.gallery_images) ? doc.gallery_images.length : 0), 0);

  els.libraryContent.innerHTML = `
    <div class="library-tools">
      <div class="library-stats">
        <span><b>${documentLibrary.length.toLocaleString()}</b> PDFs</span>
        <span><b>${totalPages.toLocaleString()}</b> pages</span>
        <span><b>${evidencePages.toLocaleString()}</b> evidence pages</span>
        <span><b>${evidenceRows.toLocaleString()}</b> portfolio rows</span>
        <span><b>${galleryPages.toLocaleString()}</b> image pages</span>
      </div>
      <label>
        <span>Search documents</span>
        <input id="librarySearchInput" type="search" value="${escapeHtml(filter)}" placeholder="Search documents, locations, traffic, EBITDA, photos..." autocomplete="off" />
      </label>
    </div>
    <div id="libraryResults" class="library-list">${renderDocumentResults(docs)}</div>
  `;
  const searchInput = document.getElementById("librarySearchInput");
  if (searchInput) {
    searchInput.addEventListener("input", updateDocumentLibraryResults);
  }
}

function updateDocumentLibraryResults(event) {
  const query = String(event.target.value || "").trim().toLowerCase();
  const results = document.getElementById("libraryResults");
  if (!results) return;
  const docs = normalizedDocumentLibrary().filter((doc) => documentMatchesQuery(doc, query));
  results.innerHTML = renderDocumentResults(docs);
}

function normalizedDocumentLibrary() {
  return documentLibrary.map((doc) => ({
    ...doc,
    category: doc.category || (Array.isArray(doc.gallery_images) && doc.gallery_images.length ? "Image Scans" : "Deal Records"),
    group: doc.group || doc.category || "Supporting Source PDFs",
    pages: Array.isArray(doc.pages) ? doc.pages : [],
    evidence_rows: Array.isArray(doc.evidence_rows) ? doc.evidence_rows : [],
    gallery_images: Array.isArray(doc.gallery_images) ? doc.gallery_images : [],
  }));
}

function documentMatchesQuery(doc, query) {
  if (!query) return true;
  const haystack = [
    doc.title,
    doc.file_name,
    doc.category,
    doc.group,
    ...doc.pages.map((page) => page.summary),
    ...doc.pages.flatMap((page) => page.addresses || []),
    ...doc.evidence_rows.map((row) => `${row.type} ${row.name} ${row.location} ${row.status} ${row.note}`),
    ...doc.gallery_images.map((image) => `image scan photo page ${image.page} ${image.group || ""} ${image.interpretation || ""}`),
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(query);
}

function renderDocumentResults(docs) {
  if (!docs.length) return `<div class="empty-state">No document pages matched that search.</div>`;
  const groups = [
    ["Image Scans", "Photo-heavy scan packets shown as full visual galleries with every page preview.", docs.filter((doc) => doc.category === "Image Scans")],
    ["Recent Traffic & Site Packet", "The most recent scanned packet with traffic, site, and portfolio evidence pulled forward first.", docs.filter((doc) => doc.group === "Recent Traffic & Site Packet")],
    ["Scanned Deal Bins", "Bin scans grouped together for quick review of older deal files and source paperwork.", docs.filter((doc) => doc.group === "Scanned Deal Bins")],
    ["Dated Source PDFs", "Date-stamped scanned source files organized separately from the bin packets.", docs.filter((doc) => doc.group === "Dated Source PDFs")],
    ["Supporting Source PDFs", "Additional imported source documents that support the Scout records.", docs.filter((doc) => doc.group === "Supporting Source PDFs")],
  ];
  return groups
    .map(([title, summary, groupDocs]) => renderDocumentSection(title, summary, groupDocs))
    .filter(Boolean)
    .join("");
}

function renderDocumentSection(title, summary, docs) {
  if (!docs.length) return "";
  return `
    <section class="document-section">
      <div class="document-section-head">
        <div>
          <h3>${escapeHtml(title)}</h3>
          <p>${escapeHtml(summary)}</p>
        </div>
        <span>${docs.length.toLocaleString()} file${docs.length === 1 ? "" : "s"}</span>
      </div>
      <div class="document-section-list">
        ${docs.map((doc) => renderDocumentCard(doc)).join("")}
      </div>
    </section>
  `;
}

function renderDocumentCard(doc) {
  const pdfHref = encodeURI(doc.pdf_url || "");
  const isImageScan = doc.category === "Image Scans";
  const textHref = !isImageScan && doc.text_url ? encodeURI(doc.text_url) : "";
  const evidenceRows = doc.evidence_rows.slice(0, 14);
  const pages = doc.pages.slice(0, 8);
  const galleryImages = doc.gallery_images;
  return `
    <article class="document-card${isImageScan ? " image-scan-card" : ""}">
      <div class="document-card-head">
        <div>
          <h3>${escapeHtml(doc.title)}</h3>
          <p>${isImageScan ? `${galleryImages.length.toLocaleString()} preview pages grouped by interpretation` : `${Number(doc.page_count || 0).toLocaleString()} pages • ${Number(doc.evidence_page_count || 0).toLocaleString()} evidence pages • ${Number(doc.evidence_row_count || 0).toLocaleString()} structured rows`}</p>
        </div>
        <div class="document-actions">
          ${pdfHref ? `<a class="source-link" href="${escapeHtml(pdfHref)}" target="_blank" rel="noreferrer">Open PDF</a>` : ""}
          ${textHref ? `<a class="source-link ghost-link" href="${escapeHtml(textHref)}" target="_blank" rel="noreferrer">OCR Text</a>` : ""}
        </div>
      </div>
      ${
        evidenceRows.length
          ? `<div class="evidence-table">
              <div class="evidence-row evidence-head"><span>Type</span><span>Name</span><span>Location</span><span>Traffic</span><span>EBITDA</span></div>
              ${evidenceRows
                .map(
                  (row) => `
                    <a class="evidence-row" href="${escapeHtml(`${pdfHref}#page=${encodeURIComponent(row.page || "1")}`)}" target="_blank" rel="noreferrer">
                      <span>${escapeHtml(row.type)}</span>
                      <span>${escapeHtml(row.name)}</span>
                      <span>${escapeHtml(row.location)}</span>
                      <span>${escapeHtml(row.traffic_count)}</span>
                      <span>${escapeHtml(row.ebitda)}</span>
                    </a>
                  `
                )
                .join("")}
            </div>`
          : ""
      }
      ${
        galleryImages.length
          ? renderImageGalleryGroups(doc, galleryImages, pdfHref)
          : ""
      }
      ${pages.length ? renderPageEvidenceList(pages, pdfHref) : ""}
    </article>
  `;
}

function renderPageEvidenceList(pages, pdfHref) {
  return `
    <div class="page-chip-list">
      ${pages
        .map(
          (page) => `
            <a href="${escapeHtml(`${pdfHref}#page=${encodeURIComponent(page.page)}`)}" target="_blank" rel="noreferrer">
              <b>Page ${escapeHtml(page.page)}</b>
              <span>${escapeHtml(page.summary)}</span>
            </a>
          `
        )
        .join("")}
    </div>
  `;
}

function renderImageGalleryGroups(doc, galleryImages, pdfHref) {
  const groups = new Map();
  galleryImages.forEach((image) => {
    const group = image.group || "General Image Evidence";
    if (!groups.has(group)) groups.set(group, []);
    groups.get(group).push(image);
  });

  return [...groups.entries()]
    .map(([group, images]) => {
      const interpretation = images.find((image) => image.interpretation)?.interpretation || "Visual pages from the scanned PDF.";
      return `
        <section class="image-gallery-group">
          <div class="image-gallery-head">
            <div>
              <h4>${escapeHtml(group)}</h4>
              <p>${escapeHtml(interpretation)}</p>
            </div>
            <span>${images.length.toLocaleString()} page${images.length === 1 ? "" : "s"}</span>
          </div>
          <div class="image-gallery-grid">
            ${images
              .map(
                (image) => `
                  <a href="${escapeHtml(image.pdf_page_url || pdfHref)}" target="_blank" rel="noreferrer">
                    <img src="${escapeHtml(image.image_url)}" alt="${escapeHtml(`${doc.title} page ${image.page}`)}" loading="lazy" />
                    <span>Page ${escapeHtml(image.page)}</span>
                  </a>
                `
              )
              .join("")}
          </div>
        </section>
      `;
    })
    .join("");
}

function clearSearchInputs() {
  [els.yearInput, els.marketInput, els.askingPriceInput, els.salesInput, els.ebitdaInput, els.carsInput, els.acresInput, els.noteInput].forEach((input) => {
    input.value = "";
  });
}

function updateStats() {
  const markets = new Set(records.map((record) => record.market).filter(Boolean));
  const states = new Set(records.map((record) => record.state).filter(Boolean));
  const acreageRecords = records.filter((record) => record.acres && !/^not listed/i.test(record.acres));
  const ebitdaRecords = records.filter((record) => moneyToNumber(record.ebitda));

  if (els.recordCount) els.recordCount.textContent = records.length.toLocaleString();
  if (els.marketCount) els.marketCount.textContent = markets.size.toLocaleString();
  if (els.stateCount) els.stateCount.textContent = states.size.toLocaleString();
  if (els.acreageCount) els.acreageCount.textContent = acreageRecords.length.toLocaleString();
  if (els.ebitdaCount) els.ebitdaCount.textContent = ebitdaRecords.length.toLocaleString();

  if (els.sourceList) {
    const sources = [...new Set(records.map((record) => record.source))];
    els.sourceList.innerHTML = sources.length
      ? sources.map((source) => `<li>${escapeHtml(source)}</li>`).join("")
      : `<li>No files loaded yet.</li>`;
  }
}

function setupFilterOptions() {
  if (els.marketInput && els.marketInput.tagName === "SELECT") {
    const selected = els.marketInput.value;
    els.marketInput.innerHTML = [
      `<option value="">Any</option>`,
      ...STATE_OPTIONS.map(([code, name]) => `<option value="${escapeHtml(code)}">${escapeHtml(name)}</option>`),
    ].join("");
    els.marketInput.value = selected && STATE_OPTIONS.some(([code]) => code === selected) ? selected : "";
  }

  if (els.yearInput && els.yearInput.tagName === "SELECT") {
    const selected = els.yearInput.value;
    const years = [...new Set(records.map((record) => String(record.year || "").trim()).filter((year) => /^(19|20)\d{2}$/.test(year)))]
      .sort((a, b) => Number(b) - Number(a));
    els.yearInput.innerHTML = [
      `<option value="">Any</option>`,
      ...years.map((year) => `<option value="${escapeHtml(year)}">${escapeHtml(year)}</option>`),
    ].join("");
    els.yearInput.value = years.includes(selected) ? selected : "";
  }
}

function saveRecords() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
  } catch {
    // Some private/browser-preview contexts block local storage. The app still works from the generated data.
  }
}

function loadRecords() {
  if (importedRows.length) {
    records = importedRows.map((item, index) => standardizeRecord(item, item.source || "ocr-output scanned PDFs", index));
    saveRecords();
  } else {
    try {
      records = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    } catch {
      records = [];
    }
    if (!records.length) {
      records = sampleRows.map((item, index) => standardizeRecord(item, item.source || "shullman_demo_knowledge_base.csv", index));
      saveRecords();
    }
  }
  setupFilterOptions();
  updateStats();
  runSearch();
}

async function handleFiles(files) {
  const loaded = [];

  for (const file of files) {
    const text = await file.text();
    const name = file.name;
    let parsed = [];

    try {
      if (name.toLowerCase().endsWith(".csv")) parsed = parseCsv(text);
      else if (name.toLowerCase().endsWith(".json")) parsed = parseJson(text);
      else parsed = parseTxt(text);
    } catch (error) {
      if (els.agentReadout) els.agentReadout.textContent = `Could not read ${name}: ${error.message}`;
      continue;
    }

    parsed.forEach((item, index) => loaded.push(standardizeRecord(item, name, index)));
  }

  records = [...records, ...loaded];
  activeRecordId = null;
  setupFilterOptions();
  saveRecords();
  updateStats();
  runSearch();
}

function clearData() {
  records = [];
  activeRecordId = null;
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Storage may be unavailable in private/browser-preview contexts.
  }
  clearSearchInputs();
  closeModal();
  setupFilterOptions();
  updateStats();
  runSearch();
}

function loadSample() {
  const seedRows = importedRows.length ? importedRows : sampleRows;
  const seedSource = importedRows.length ? "ocr-output scanned PDFs" : "shullman_demo_knowledge_base.csv";
  records = seedRows.map((item, index) => standardizeRecord(item, item.source || seedSource, index));
  activeRecordId = null;
  setupFilterOptions();
  clearSearchInputs();
  saveRecords();
  updateStats();
  runSearch();
}

function setupVoice() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    els.voiceStatus.textContent = "Voice unavailable";
    els.voiceBtn.disabled = true;
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  let isListening = false;

  recognition.addEventListener("start", () => {
    isListening = true;
    els.voiceStatus.textContent = "Listening";
    els.voiceBtn.textContent = "Stop";
    els.voiceBtn.classList.add("is-recording");
  });

  recognition.addEventListener("end", () => {
    const shouldSearch = isListening;
    isListening = false;
    els.voiceStatus.textContent = "Voice ready";
    els.voiceBtn.textContent = "Speak";
    els.voiceBtn.classList.remove("is-recording");
    if (shouldSearch) runSearch();
  });

  recognition.addEventListener("result", (event) => {
    els.noteInput.value = event.results[0][0].transcript;
  });

  els.voiceBtn.addEventListener("click", () => {
    if (isListening) recognition.stop();
    else recognition.start();
  });
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

if (els.fileInput) els.fileInput.addEventListener("change", (event) => handleFiles(event.target.files));
if (els.loadSampleBtn) els.loadSampleBtn.addEventListener("click", loadSample);
if (els.clearDataBtn) els.clearDataBtn.addEventListener("click", clearData);
els.searchBtn.addEventListener("click", runSearch);
if (els.documentLibraryBtn) els.documentLibraryBtn.addEventListener("click", openLibrary);
[els.yearInput, els.marketInput, els.askingPriceInput, els.salesInput, els.ebitdaInput, els.carsInput, els.acresInput, els.noteInput].forEach((input) => {
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && input !== els.noteInput) runSearch();
  });
});
els.closeModalBtn.addEventListener("click", closeModal);
els.modalBackdrop.addEventListener("click", closeModal);
if (els.closeLibraryBtn) els.closeLibraryBtn.addEventListener("click", closeLibrary);
if (els.libraryBackdrop) els.libraryBackdrop.addEventListener("click", closeLibrary);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !els.recordModal.hidden) closeModal();
  if (event.key === "Escape" && els.libraryModal && !els.libraryModal.hidden) closeLibrary();
});

setupVoice();
loadRecords();
