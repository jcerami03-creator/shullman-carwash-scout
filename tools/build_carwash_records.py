from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path("/Users/josephcerami/Documents/LLM For Shullman Paperwork")
OCR_DIR = ROOT / "ocr-output"
OUT = ROOT / "generated" / "carwash_records.js"
PUBLIC_RESEARCH_PATH = ROOT / "data" / "public_research.json"
PUBLIC_CARWASH_PATH = ROOT / "data" / "public_carwashes.json"

STATE_RE = re.compile(r"\b([A-Z][a-zA-Z .'-]+,\s*(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)(?:\s+\d{5})?)\b")
ADDRESS_RE = re.compile(
    r"\b\d{1,6}(?:-\d{1,6})?\s+[A-Za-z0-9][A-Za-z0-9 .'/#-]{1,70}?\s+(?:Street|St|Road|Rd|Avenue|Ave|Highway|Hwy|Pike|Lane|Ln|Drive|Dr|Boulevard|Blvd|Court|Ct|Way|Parkway|Pkwy|Circle|Cir|Trail|Terrace|Place|Pl|Route|Rt|Expressway|Expy|Square|Sq)\b",
    re.I,
)
MONEY_RE = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?\s?(?:million|m|k)?", re.I)
YEAR_RE = re.compile(r"\b(19[8-9]\d|20[0-2]\d|2026)\b")
ACRES_RE = re.compile(r"(?<!\d)(\d+(?:\.\d+)?|\.\d+)\s*(?:acres?|ac\b)\b", re.I)
CAR_COUNT_RE = re.compile(
    r"\b(?:over\s+|approx(?:imately)?\s+)?(\d{2,3}(?:,\d{3})+|\d{5,6})\+?\s+(?:cars\s+washed|washes|wash(?:es)?\s+per\s+year|annual\s+washes|annual\s+volume)\b"
    r"|\b(?:estimated\s+wash\s+volume|wash\s+volume|total\s+volume)\D{0,40}(\d{2,3}(?:,\d{3})+|\d{5,6})\b",
    re.I,
)
TRAFFIC_COUNT_RE = re.compile(
    r"\b(?:traffic\s+count|traffic\s+volume|annual\s+average\s+daily\s+traffic|average\s+daily\s+traffic|AADT|ADT|VPD)\D{0,50}(\d{1,3}(?:,\d{3})+|\d{4,6})\b"
    r"|\b(\d{1,3}(?:,\d{3})+|\d{4,6})\+?\s*(?:VPD|AADT|ADT|vehicles\s+per\s+day|daily\s+traffic)\b",
    re.I,
)
EBITDA_RE = re.compile(r"\bEBITDA\b[^$\d]*(\$\s?\d[\d,]*(?:\.\d+)?\s?(?:m|k|million)?)", re.I)
SALES_RE = re.compile(r"\b(?:sales|revenue|gross operating income|total revenue)\b[^$\d]*(\$\s?\d[\d,]*(?:\.\d+)?\s?(?:m|k|million)?)", re.I)
BAD_LINE_TERMS = [
    "loopnet",
    "bizbuysell",
    "craigslist",
    "google map",
    "terms and conditions",
    "become a free member",
    "login",
    "sales comps",
    "property records",
    "add listing",
    "contact listing broker",
    "request additional information",
    "back to search",
    "attached documents",
    "detailed information",
    "learn more here",
    "click here",
    "need funding",
    "get pre-qualified",
    "business listed by",
    "memberships",
    "certifications",
    "page ",
    "http",
    "www.",
    "©",
    "view larger map",
    "map data",
    "available inventory",
]
TITLE_TERMS = [
    "car wash",
    "carwash",
    "auto spa",
    "wash barn",
    "suds n soda",
    "mister car wash",
    "express tunnel",
    "blue wave express",
    "full service",
    "gas station",
    "detail center",
    "site location",
    "offering memorandum",
    "investment summary",
    "financial analysis",
]
STATE_NAMES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA", "colorado": "CO",
    "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS", "kentucky": "KY", "louisiana": "LA",
    "maine": "ME", "maryland": "MD", "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
    "new mexico": "NM", "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
}
STATE_CODES = set(STATE_NAMES.values())
EXCLUDED_STATES = {"AK", "HI"}
LOWER_48_STATE_CODES = STATE_CODES - EXCLUDED_STATES
TARGET_RECORD_COUNT = 1200
MIN_PUBLIC_RECORDS_PER_STATE = 7
STATE_CODE_PATTERN = r"(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)"
GENERIC_TITLES = {
    "car wash",
    "car wash facility",
    "car wash opportunity",
    "specialty for sale",
    "available for lease",
    "for sale",
    "financial analysis",
    "investment summary",
    "executive summary",
}
OCR_REPLACEMENTS = [
    (r"\bFuctloning\b", "Functioning"),
    (r"\bFuctioning\b", "Functioning"),
    (r"\bBullding\b", "Building"),
    (r"\bSttong\b", "Strong"),
    (r"\bDEVLEOPMENT\b", "Development"),
    (r"\bDEVLEOP\b", "Develop"),
    (r"\bDevleopment\b", "Development"),
    (r"\bARASOTA\b", "Sarasota"),
    (r"\bNavies\b", "Naples"),
    (r"\bGoogie\b", "Google"),
    (r"\bGooge\b", "Google"),
    (r"\bSellmawr\b", "Bellmawr"),
    (r"\bBelimawr\b", "Bellmawr"),
    (r"\bBeilmawr\b", "Bellmawr"),
    (r"\bBellmawc\b", "Bellmawr"),
    (r"\bCarwash\b", "Car Wash"),
    (r"\bAutoSpa\b", "Auto Spa"),
    (r"\bFuctloning\b", "Functioning"),
    (r"\bProfitable Car Wash, Low Labor Biz\b", "Profitable Low-Labor Car Wash"),
]
BAD_TITLE_PHRASES = [
    "profit centers include",
    "most busiest",
    "competition:",
    "to check this car wash",
    "this location is",
    "property sub-type",
    "privacy policy",
    "get financing",
    "asking prices retail",
    "google local",
    "available on",
    "contact",
    "phone",
    "email",
    "business type:",
    "cap rate",
    "very recently upgraded",
    "se to growing car wash",
    "joday@",
    "presented by",
    "business listed by",
    "loopnet",
    "by having",
    "owner/user",
]


def load_public_research() -> list[dict[str, str]]:
    if not PUBLIC_RESEARCH_PATH.exists():
        return []
    return json.loads(PUBLIC_RESEARCH_PATH.read_text(encoding="utf-8"))


def load_public_carwashes() -> dict[str, list[dict[str, str]]]:
    if not PUBLIC_CARWASH_PATH.exists():
        return {}
    return json.loads(PUBLIC_CARWASH_PATH.read_text(encoding="utf-8"))


PUBLIC_RESEARCH = load_public_research()
PUBLIC_CARWASHES = load_public_carwashes()


def clean_text(text: str) -> str:
    text = text.replace("\r", "\n")
    for pattern, replacement in OCR_REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.I)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_line(line: str) -> str:
    line = re.sub(r"\s+", " ", line).strip(" -_|•·:;,\t")
    line = line.replace("Ca ash", "Car Wash")
    for pattern, replacement in OCR_REPLACEMENTS:
        line = re.sub(pattern, replacement, line, flags=re.I)
    line = line.replace("Setlists", "").replace("te LoopNet", "")
    line = line.replace(">", " ")
    return line.strip()


def useful_lines(page: str) -> list[str]:
    lines = []
    for raw in page.splitlines():
        line = clean_line(raw)
        if len(line) < 4:
            continue
        lower = line.lower()
        if any(term in lower for term in BAD_LINE_TERMS):
            continue
        if len(re.sub(r"[A-Za-z0-9 $,.#&/()-]", "", line)) > 5:
            continue
        if sum(char.isalpha() for char in line) < 3:
            continue
        lines.append(line)
    return lines


def source_year(path: Path) -> str:
    match = re.search(r"Document_(\d{4})", path.name)
    return match.group(1) if match else ""


def money_to_number(value: str) -> float:
    text = value.lower().replace("$", "").replace(",", "").strip()
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return 0
    number = float(match.group(0))
    if "million" in text or re.search(r"\d(?:\.\d+)?\s*m\b", text):
        number *= 1_000_000
    elif re.search(r"\d(?:\.\d+)?\s*k\b", text):
        number *= 1_000
    return number


def likely_price(page: str) -> str:
    values = MONEY_RE.findall(page)
    candidates = [value.strip() for value in values if 100_000 <= money_to_number(value) <= 50_000_000]

    labeled = re.search(r"(?:offered for sale at|purchase price|min\.? offer price|price:|asking price|total price|list price|for sale\s*[-:]?)\s*(\$\s?\d[\d,]*(?:\.\d+)?\s?(?:million|m|k)?)", page, re.I)
    if labeled:
        labeled_value = labeled.group(1).strip()
        if money_to_number(labeled_value) >= 100_000 or not candidates:
            return labeled_value
        return max(candidates, key=money_to_number)
    if not values:
        return ""

    if candidates:
        return max(candidates, key=money_to_number)
    return ""


def normalized_money(value: str) -> int:
    return round(money_to_number(value))


def format_money_short(number: float) -> str:
    if number >= 1_000_000:
        value = number / 1_000_000
        return f"${value:.1f}M".replace(".0M", "M")
    if number >= 1_000:
        return f"${round(number / 1_000)}K"
    return f"${round(number):,}"


def numeric_value(value: str) -> float:
    match = re.search(r"\d+(?:\.\d+)?", str(value or "").replace(",", ""))
    return float(match.group(0)) if match else 0


def estimated_acres(record: dict[str, str]) -> str:
    acres = clean_line(str(record.get("acres", "")))
    if acres and not acres.lower().startswith(("not listed", "not provided")):
        return acres
    text = " ".join(str(record.get(key, "")) for key in ["name", "market", "note"]).lower()
    if any(term in text for term in ["truck", "full service", "auto spa", "detail"]):
        return "Est. 1.45"
    if any(term in text for term in ["express", "tunnel", "membership", "zips", "tommy", "mister", "kaady", "washman"]):
        return "Est. 1.10"
    return "Est. 0.85"


def estimated_ebitda(record: dict[str, str]) -> str:
    ebitda = clean_line(str(record.get("ebitda", "")))
    if ebitda:
        return ebitda
    sales = money_to_number(str(record.get("sales", "")))
    asking = money_to_number(str(record.get("asking_price", "")))
    cars = numeric_value(str(record.get("cars_per_year", "")))
    acres = numeric_value(str(record.get("acres", "")))
    text = " ".join(str(record.get(key, "")) for key in ["name", "market", "note"]).lower()
    if sales:
        estimate = sales * 0.24
    elif asking:
        estimate = asking / 6.5
    elif cars:
        estimate = cars * 3.25
    elif "truck" in text:
        estimate = 220_000
    elif any(term in text for term in ["express", "tunnel", "membership", "zips", "tommy", "mister", "kaady", "washman"]):
        estimate = 360_000
    elif any(term in text for term in ["self", "coin", "hand wash", "detail"]):
        estimate = 140_000
    elif acres >= 1.4:
        estimate = 320_000
    else:
        estimate = 240_000
    return f"Est. {format_money_short(estimate)}"


def estimated_sales(record: dict[str, str]) -> str:
    sales = clean_line(str(record.get("sales", "")))
    if sales and not sales.lower().startswith("not listed"):
        return sales
    ebitda = money_to_number(str(record.get("ebitda", "")))
    asking = money_to_number(str(record.get("asking_price", "")))
    cars = numeric_value(str(record.get("cars_per_year", "")))
    text = " ".join(str(record.get(key, "")) for key in ["name", "market", "note"]).lower()
    if ebitda:
        estimate = ebitda / 0.24
    elif asking:
        estimate = asking * 0.55
    elif cars:
        estimate = cars * 12.5
    elif any(term in text for term in ["express", "tunnel", "membership", "zips", "tommy", "mister", "kaady", "washman"]):
        estimate = 1_350_000
    elif any(term in text for term in ["self", "coin", "hand wash", "detail"]):
        estimate = 525_000
    else:
        estimate = 900_000
    return f"Est. {format_money_short(estimate)}"


def estimated_cars_per_year(record: dict[str, str]) -> str:
    cars = clean_line(str(record.get("cars_per_year", "")))
    if cars and not cars.lower().startswith("not listed"):
        return cars
    ebitda = money_to_number(str(record.get("ebitda", "")))
    sales = money_to_number(str(record.get("sales", "")))
    text = " ".join(str(record.get(key, "")) for key in ["name", "market", "note"]).lower()
    if sales:
        estimate = sales / 12.5
    elif ebitda:
        estimate = ebitda / 3.25
    elif any(term in text for term in ["express", "tunnel", "membership", "zips", "tommy", "mister", "kaady", "washman"]):
        estimate = 105_000
    elif any(term in text for term in ["self", "coin", "hand wash", "detail"]):
        estimate = 42_000
    else:
        estimate = 72_000
    return f"Est. {round(estimate / 1000) * 1000:,.0f}"


def estimated_asking_price(record: dict[str, str]) -> str:
    asking = clean_line(str(record.get("asking_price", "")))
    if asking and not asking.lower().startswith(("not listed", "not provided", "call")):
        return asking
    ebitda = money_to_number(str(record.get("ebitda", "")))
    sales = money_to_number(str(record.get("sales", "")))
    acres = numeric_value(str(record.get("acres", "")))
    if ebitda:
        estimate = ebitda * 6.5
    elif sales:
        estimate = sales * 2.4
    elif acres:
        estimate = 1_250_000 + acres * 950_000
    else:
        estimate = 2_400_000
    return f"Est. {format_money_short(estimate)}"


def professional_public_summary(summary: str) -> str:
    summary = clean_line(summary)
    summary = re.sub(r"\bLoopNet confirms\b", "Historical listing record identifies", summary, flags=re.I)
    summary = re.sub(r"\bLoopNet\b", "historical listing source", summary, flags=re.I)
    return summary


def market_key(value: str) -> str:
    text = clean_line(value).lower()
    text = re.sub(r"\b\d{5}(?:-\d{4})?\b", "", text)
    replacements = {
        "street": "st",
        "road": "rd",
        "avenue": "ave",
        "boulevard": "blvd",
        "drive": "dr",
        "lane": "ln",
        "parkway": "pkwy",
        "highway": "hwy",
        "circle": "cir",
        "court": "ct",
        "route": "rt",
    }
    for long, short in replacements.items():
        text = re.sub(rf"\b{long}\b", short, text)
    return re.sub(r"\W+", "", text)


def canonical_location_key(value: str) -> str:
    text = clean_line(value)
    state = state_from_text(text)
    address_match = ADDRESS_RE.search(text)
    if not address_match:
        return market_key(text)
    address = address_match.group(0).lower()
    address = re.sub(r"\b\d{5}(?:-\d{4})?\b", "", address)
    replacements = {
        "street": "st",
        "road": "rd",
        "avenue": "ave",
        "boulevard": "blvd",
        "drive": "dr",
        "lane": "ln",
        "parkway": "pkwy",
        "highway": "hwy",
        "circle": "cir",
        "court": "ct",
        "route": "rt",
        "terrace": "ter",
        "place": "pl",
    }
    for long, short in replacements.items():
        address = re.sub(rf"\b{long}\b", short, address)
    address = re.sub(r"\b(?:north|south|east|west)\b", lambda match: match.group(0)[0], address)
    return re.sub(r"[^a-z0-9]+", "", f"{address} {state}")


def money_value_or_blank(value: str) -> str:
    value = clean_line(value)
    value = re.sub(r"\$(\d{1,2})\.(\d{3}),(\d{3})", r"$\1,\2,\3", value)
    if not value or value.lower() in {"n/a", "na", "call", "not available"}:
        return ""
    match = MONEY_RE.search(value)
    if not match:
        return ""
    money = match.group(0).strip()
    if money_to_number(money) <= 0:
        return ""
    broken_millions = re.match(r"\$\s?(\d{1,2}),(\d{6})$", money)
    if broken_millions:
        digits = broken_millions.group(1) + broken_millions.group(2)
        return "$" + f"{int(digits):,}"
    trailing_ocr_digit = re.match(r"(\$\s?\d{1,3},\d{3})\d$", money)
    if trailing_ocr_digit:
        return trailing_ocr_digit.group(1)
    return money


def cleaned_page_lines(page: str) -> list[str]:
    return [clean_line(raw) for raw in page.splitlines() if clean_line(raw)]


def extract_labeled_financials(page: str) -> dict[str, str]:
    """Read listing tables where labels are stacked, then values are stacked below."""
    lines = cleaned_page_lines(page)
    lowered = [line.lower().rstrip(":") for line in lines]
    labels = [
        ("asking_price", "asking"),
        ("asking_price", "asking price"),
        ("asking_price", "list price"),
        ("sales", "gross"),
        ("cash_flow", "cash flow"),
        ("sales", "gross revenue"),
        ("sales", "sales revenue"),
        ("sales", "annual gross sales"),
        ("ebitda", "net profit"),
        ("ebitda", "ebitda"),
        ("ff&e", "ff&e"),
        ("inventory", "inventory"),
        ("real_estate", "real estate"),
        ("established", "established"),
    ]

    label_positions: list[tuple[int, str]] = []
    for index, line in enumerate(lowered):
        for key, label in labels:
            if line == label:
                label_positions.append((index, key))
                break
    if len(label_positions) >= 3:
        first_label = min(pos for pos, _ in label_positions)
        last_label = max(pos for pos, _ in label_positions)
        end = next((i for i in range(last_label + 1, len(lines)) if lowered[i].startswith("business description")), len(lines))
        label_block_has_values = any(MONEY_RE.search(line) for line in lines[first_label:last_label + 1])
        if not label_block_has_values:
            values = []
            for line in lines[last_label + 1:end]:
                if MONEY_RE.search(line) or line.lower() in {"n/a", "na", "call"} or re.fullmatch(r"(?:19|20)\d{2}", line):
                    values.append(line)
            if len(values) >= len(label_positions):
                mapped = {key: money_value_or_blank(values[offset]) for offset, (_, key) in enumerate(label_positions)}
                return {
                    "asking_price": mapped.get("asking_price", ""),
                    "sales": mapped.get("sales", ""),
                    "ebitda": mapped.get("ebitda", "") or mapped.get("cash_flow", ""),
                }

    financials: dict[str, str] = {}
    label_aliases = {
        "asking_price": [r"asking price", r"asking", r"list price"],
        "sales": [r"gross revenue", r"sales revenue", r"annual gross sales", r"gross"],
        "ebitda": [r"cash flow\s*/\s*net profit", r"cash flow", r"net profit", r"ebitda"],
    }
    for key, aliases in label_aliases.items():
        for alias in aliases:
            value = money_near_label(lines, alias)
            if value:
                financials[key] = value
                break
    monthly_sales = re.search(r"Gross Sales per Month\s*:?\s*(\$\s?\d[\d,]*(?:\.\d+)?\s?(?:m|k|million)?)\s*\((\$\s?\d[\d,.]*(?:m|k|million)?/yr)\)", page, re.I)
    if monthly_sales:
        financials["sales"] = monthly_sales.group(2).strip()
    revenue = re.search(r"\bRevenue\s*:\s*(\$\s?\d[\d,]*(?:\.\d+)?\s?(?:m|k|million)?)", page, re.I)
    if revenue:
        financials["sales"] = revenue.group(1).strip()
    net_income = re.search(r"Net Income per Month\s*:?\s*(\$\s?\d[\d,]*(?:\.\d+)?\s?(?:m|k|million)?)\s*\((\$\s?\d[\d,.]*(?:m|k|million)?/yr)\)", page, re.I)
    if net_income:
        financials["ebitda"] = net_income.group(2).strip()
    purchase_price = re.search(r"\bPurchase Price\s*:\s*(\$\s?\d[\d,]*(?:\.\d+)?\s?(?:m|k|million)?)", page, re.I)
    if purchase_price:
        financials["asking_price"] = purchase_price.group(1).strip()
    list_price = re.search(r"\bS?(\d[\d,]{5,})\s+LIST PRICE\b", page, re.I)
    if list_price and not financials.get("asking_price"):
        digits = re.sub(r"\D", "", list_price.group(1))
        financials["asking_price"] = "$" + f"{int(digits):,}"
    return financials


def money_near_label(lines: list[str], label_pattern: str) -> str:
    label_re = re.compile(rf"^\s*{label_pattern}\b\s*:?", re.I)
    for index, line in enumerate(lines):
        if not label_re.search(line):
            continue
        same_line = money_value_or_blank(line)
        if same_line:
            return same_line
        previous_value = ""
        next_value = ""
        if index > 0 and not is_financial_label_line(lines[index - 1]):
            previous_value = money_value_or_blank(lines[index - 1])
        if index + 1 < len(lines) and not is_financial_label_line(lines[index + 1]):
            next_value = money_value_or_blank(lines[index + 1])
        if re.match(r"asking(?: price)?", label_pattern, re.I):
            return previous_value or next_value
        return next_value or previous_value
    return ""


def is_financial_label_line(line: str) -> bool:
    return bool(re.match(r"^\s*(?:asking|asking price|gross|gross revenue|sales revenue|annual gross sales|cash flow|net profit|ebitda|ff&e|inventory|real estate)\b", line, re.I))


def has_immediate_labeled_value(page: str, label_pattern: str, value: str) -> bool:
    if not value:
        return False
    escaped = re.escape(value).replace("\\ ", r"\s*")
    return bool(re.search(rf"\b(?:{label_pattern})\b[^\n]{{0,90}}{escaped}", page, re.I))


def first_match(pattern: re.Pattern[str], page: str) -> str:
    match = pattern.search(page)
    if not match:
        return ""
    if match.lastindex:
        for group in match.groups():
            if group:
                return group.strip()
    return match.group(0).strip()


def traffic_count_from_text(text: str) -> str:
    match = TRAFFIC_COUNT_RE.search(text)
    if not match:
        return ""
    value = next((group for group in match.groups() if group), "")
    if not value:
        return clean_line(match.group(0))
    context = clean_line(match.group(0))
    if re.search(r"\bAADT\b|annual average daily traffic|average daily traffic", context, re.I):
        return f"{value} AADT"
    if re.search(r"\bADT\b", context, re.I):
        return f"{value} ADT"
    if re.search(r"\bVPD\b|vehicles per day", context, re.I):
        return f"{value} VPD"
    return f"{value} traffic count"


def sanitize_traffic_count(record: dict[str, str]) -> str:
    traffic = clean_line(str(record.get("traffic_count", "")))
    if not traffic or traffic.lower().startswith(("not listed", "not provided")):
        return ""
    number_match = re.search(r"\b(\d{4,6})\b", traffic.replace(",", ""))
    if number_match:
        number = number_match.group(1)
        zip_codes = re.findall(r"\b\d{5}\b", str(record.get("market", "")))
        if number in zip_codes and not re.search(r"\b(?:traffic|vpd|aadt|adt|vehicles)\b", traffic, re.I):
            return ""
    return traffic


def estimated_traffic_count(record: dict[str, str]) -> str:
    traffic = sanitize_traffic_count(record)
    if traffic:
        return traffic

    cars = numeric_value(str(record.get("cars_per_year", "")))
    acres = numeric_value(str(record.get("acres", "")))
    text = " ".join(str(record.get(key, "")) for key in ["name", "market", "note"]).lower()

    if cars >= 180_000:
        estimate = 38_000
    elif cars >= 120_000:
        estimate = 30_000
    elif cars >= 80_000:
        estimate = 22_000
    elif cars >= 45_000:
        estimate = 16_000
    else:
        estimate = 12_500

    if any(term in text for term in ["express", "tunnel", "membership", "mister", "tommy", "zips", "super star", "quick quack"]):
        estimate += 5_000
    if re.search(r"\b(?:highway|hwy|route|us-|i-\d+|interstate|parkway|pkwy|boulevard|blvd|avenue|ave)\b", text):
        estimate += 4_000
    if any(term in text for term in ["self serve", "self-service", "coin", "hand wash", "detail"]):
        estimate -= 3_000
    if acres >= 1.4:
        estimate += 2_000

    estimate = max(8_000, min(65_000, estimate))
    rounded = round(estimate / 500) * 500
    return f"Est. {rounded:,.0f} VPD"


def title_quality(line: str) -> int:
    lower = line.lower()
    if any(phrase in lower for phrase in BAD_TITLE_PHRASES):
        return -30
    if re.search(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b", line):
        return -25
    if lower.strip(" .:-") in GENERIC_TITLES:
        return -20
    score = 0
    if any(term in lower for term in TITLE_TERMS):
        score += 20
    if "for sale" in lower or "available" in lower:
        score += 6
    if ADDRESS_RE.search(line):
        score -= 5
    if MONEY_RE.search(line):
        score -= 4
    if len(line) <= 75:
        score += 4
    if len(line) > 110:
        score -= 10
    if any(term in lower for term in BAD_LINE_TERMS):
        score -= 30
    return score


def has_title_term(title: str) -> bool:
    lower = title.lower()
    return any(term in lower for term in TITLE_TERMS)


def is_weak_title(title: str) -> bool:
    lower = title.lower().strip(" .:-|>")
    if not lower or lower in GENERIC_TITLES:
        return True
    if any(phrase in lower for phrase in BAD_TITLE_PHRASES):
        return True
    if len(title) > 82:
        return True
    if re.search(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b", title):
        return True
    if lower.startswith(("this ", "the ", "a car wash tunnel", "property ", "complex:", "training available")):
        return True
    if sum(char.isalpha() for char in title) < 5:
        return True
    return False


def title_from_page(page: str, fallback: str) -> str:
    lines = useful_lines(page)
    candidates = [line for line in lines[:28] if 5 <= len(line) <= 120]
    candidates.sort(key=title_quality, reverse=True)
    if candidates and title_quality(candidates[0]) >= 10:
        return clean_title(candidates[0])
    return fallback


def clean_title(title: str) -> str:
    title = clean_line(title)
    title = re.sub(r"^Subject[:.]?\s*", "", title, flags=re.I)
    title = re.sub(r"^\d{1,2}/\d{1,2}/\d{2,4}\s*", "", title)
    title = re.sub(r"^(for sale\s*>\s*)", "", title, flags=re.I)
    title = re.sub(r"\s+Page\s+\d+.*$", "", title, flags=re.I)
    title = re.sub(r"\s+Get Financing\b.*$", "", title, flags=re.I)
    title = re.sub(r"\s+\$\d[\d,]*(?:\.\d+)?\s?(?:m|k|million)?\b.*$", "", title, flags=re.I)
    title = re.sub(r"^[^A-Za-z0-9]+", "", title)
    title = re.sub(r"^[a-z]\)\s*", "", title, flags=re.I)
    title = title.strip(" >—-=._|")
    title = re.sub(r"\s{2,}", " ", title)
    title = re.sub(r"^0\s+", "", title)
    title = re.sub(r"\s+-\s+full service car wash.*$", "", title, flags=re.I)
    title = re.sub(r"\s+-\s+.*(?:for sale|available|opportunity).*$", "", title, flags=re.I)
    title = re.sub(r"\s+in\s+[A-Z][A-Za-z .'-]+,\s*[A-Z]{2}$", "", title)
    title = re.sub(r"\s+ae\s*$", "", title, flags=re.I)
    title = re.sub(r"\s+for\s+br\s+\d+\??.*$", "", title, flags=re.I)
    if re.search(r"car wash with land for sale", title, re.I):
        return "Car Wash with Land for Sale"
    if "franktown corners" in title.lower():
        return "Franktown Corners"
    if title.lower().strip() == "offering memorandum":
        return "Car Wash Opportunity"
    if "offering memorandum" in title.lower():
        title = re.split(r"\||offering memorandum", title, flags=re.I)[0].strip()
        if title:
            return professional_title_case(title)
    if "main street car wash plat" in title.lower():
        return "Main Street Car Wash"
    if title.lower().startswith(("vx ", "roperty", "ere ", "ae)", "oi ", "ull servi", "wilding ")):
        return "Car Wash Opportunity"
    lower = title.lower()
    if "fully functioning car wash" in lower:
        return "Fully Functioning Car Wash & Building"
    if re.search(r"\bandy'?s\b", lower) and "car wash" in lower:
        return "Andy's Car Wash"
    if "full service tunnel car wash for sale in a growing" in lower:
        return "Full Service Tunnel Car Wash"
    if "round rock car wash" in lower:
        return "Round Rock Car Wash"
    if "ril l:ohne" in lower:
        return "Tunnel Car Wash for Sale"
    if "whittier car wash" in lower:
        return "Whittier Car Wash"
    if lower.startswith("great car wash in a growing area"):
        return "Great Car Wash in Growing Area"
    if lower.startswith("car wash car wash"):
        return "Car Wash Opportunity"
    if any(phrase in title.lower() for phrase in BAD_TITLE_PHRASES):
        return "Car Wash Opportunity"
    title = professional_title_case(title)
    return title[:90].strip(" -|>")


def clean_city_from_address(address: str, city: str) -> str:
    city = clean_line(city)
    address_words = [re.sub(r"[^a-z0-9]", "", word.lower()) for word in address.split()]
    city_words = city.split()
    while city_words:
        first = re.sub(r"[^a-z0-9]", "", city_words[0].lower())
        if first in {"st", "street", "rd", "road", "ave", "avenue", "blvd", "boulevard", "dr", "drive", "pkwy", "parkway", "hwy", "highway", "ln", "lane"}:
            city_words.pop(0)
            continue
        if first and first in set(address_words[-4:]):
            city_words.pop(0)
            continue
        break
    city = " ".join(city_words)
    city = re.sub(r"^(?:N|S|E|W|NE|NW|SE|SW)\s+", "", city)
    return clean_line(city)


def professional_title_case(title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip()
    if not title:
        return title
    title = title.title()
    small_words = {"And", "Or", "The", "Of", "For", "In", "With", "At", "On", "To", "A"}
    words = []
    for index, word in enumerate(title.split(" ")):
        clean_word = word.strip("(),")
        if index > 0 and clean_word in small_words:
            words.append(word.replace(clean_word, clean_word.lower()))
        elif clean_word.upper() in {"EBITDA", "ROI", "NOI", "SF", "TX", "CA", "FL", "AZ", "CO", "NY", "NJ", "PA", "GA", "TN", "IL", "OH", "MI", "NC", "SC", "UT", "VA", "MD", "DE", "RI", "IA", "MO", "NV", "OR", "WA", "OK", "IN", "WI", "AL", "AR", "MS", "SW", "SE", "NW", "NE"}:
            words.append(word.upper())
        else:
            words.append(word)
    title = " ".join(words)
    title = title.replace("Carwash", "Car Wash").replace("Car Washs", "Car Washes")
    title = re.sub(r"'S\b", "'s", title)
    title = title.replace("Auto Spa", "Auto Spa")
    title = title.replace(" W/ ", " w/ ")
    title = title.replace("In A ", "in a ")
    title = re.sub(r"\b(\d+)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), title)
    return title


def state_from_text(text: str) -> str:
    matches = re.findall(r",\s*(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)\b", text)
    if matches:
        return matches[-1]
    matches = re.findall(r"\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)\s+\d{5}\b", text)
    if matches:
        return matches[-1]
    short_text = len(text) < 160
    if short_text:
        matches = re.findall(r"\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)\s*$", text.strip())
        if matches:
            return matches[-1]
    lower = text.lower()
    if short_text:
        for name, code in STATE_NAMES.items():
            if re.search(rf"\b{name}\b", lower):
                return code
    return ""


def market_from_page(page: str, title: str) -> str:
    address = first_match(ADDRESS_RE, page)
    city_state = first_match(STATE_RE, page)
    loose_city_state = re.search(rf"\b([A-Z][A-Za-z .'-]+)\s+({STATE_CODE_PATTERN})\s+(\d{{5}})\b", page, re.I)
    title_location = re.search(r"\bin\s+([A-Z][A-Za-z .'-]+),\s*([A-Z]{2})\b", page.replace("\n", " "))
    if title_location and not address:
        return f"{title_location.group(1)}, {title_location.group(2)}"
    if address and city_state:
        return f"{address}, {city_state}"
    if address and loose_city_state:
        return f"{address}, {loose_city_state.group(1)}, {loose_city_state.group(2).upper()} {loose_city_state.group(3)}"
    if city_state:
        return city_state
    if address:
        return address
    return ""


def location_label(market: str, state: str) -> str:
    if market:
        return market
    return state or ""


def clean_market(market: str) -> str:
    market = clean_line(market)
    if not market:
        return ""
    market = re.sub(r"\s+", " ", market)
    market = re.sub(r"^(?:19|20)\d{2}\s+(?=\d{2,6}\s)", "", market)
    market = re.sub(r"^0+\s+(?=\d{2,6}\s)", "", market)
    market = re.sub(r"^\d{1,3}\s+(?=\d{2,6}\s+[A-Za-z])", "", market)
    market = market.replace(" I ", " ")
    market = re.sub(r",\s*(?:Cap Rate|Owner Resides|User Car Wash Opportunity|Please See.*?|N Santiago Blvd|Rosemead Blvd|Mexico Road St)\s+in\s+", ", ", market, flags=re.I)
    market = re.sub(r",\s*Cassandra Chandler Birmingham,\s*AL\b", ", Birmingham, AL", market, flags=re.I)
    market = re.sub(r",\s*N Santiago Blvd\s+Orange\b", ", Orange", market, flags=re.I)
    market = re.sub(r",\s*Rosemead Blvd\s+South El Monte\b", ", South El Monte", market, flags=re.I)
    market = re.sub(r"\bUser Car Wash Opportunity\s+", "", market, flags=re.I)
    market = re.sub(r",\s*([A-Za-z0-9 .'-]+)\s+\1\b", r", \1", market, flags=re.I)
    market = re.sub(r"\b([A-Za-z .'-]+),\s*\1,\s*", r"\1, ", market, flags=re.I)
    market = professional_title_case(market)
    for state_name, code in STATE_NAMES.items():
        market = re.sub(rf",\s*{re.escape(state_name.title())}\b", f", {code}", market)
        if market.strip().lower() == state_name:
            market = code
    market = re.sub(rf"\b({STATE_CODE_PATTERN}),\s*\1\b", r"\1", market)
    for code in STATE_CODES:
        market = re.sub(rf"\b{code.title()}\b", code, market)
        market = re.sub(rf",\s*{code.lower()}\b", f", {code}", market)
    return market.strip(" ,")


def special_record_fields(page: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    lines = cleaned_page_lines(page)
    text = "\n".join(lines)

    overview_index = next((i for i, line in enumerate(lines) if line.lower() == "business overview"), -1)
    if overview_index >= 0:
        title = next((candidate for candidate in lines[overview_index + 1:overview_index + 8] if re.search(r"car\s*wash|carwash|lube|detail", candidate, re.I) and not re.search(r"details|overview|for sale details", candidate, re.I)), "")
        market = next((candidate for candidate in lines[overview_index + 1:overview_index + 10] if re.search(r"\b[A-Z][A-Za-z .'-]+,\s*[A-Z]{2}\b", candidate)), "")
        if title:
            fields["name"] = clean_title(title)
        if market:
            fields["market"] = clean_market(market)
            fields["state"] = state_from_text(fields["market"])

    if "Business Name & Address" in text:
        for index, line in enumerate(lines):
            if line.lower() == "business name & address":
                name = next((candidate for candidate in lines[index + 1:index + 6] if not ADDRESS_RE.search(candidate) and "map" not in candidate.lower()), "")
                address = next((candidate for candidate in lines[index + 1:index + 8] if ADDRESS_RE.search(candidate)), "")
                city_state = next((candidate for candidate in lines[index + 1:index + 10] if STATE_RE.search(candidate)), "")
                if name:
                    fields["name"] = clean_title(name)
                if address and city_state:
                    fields["market"] = clean_market(f"{address}, {city_state}")
                    fields["state"] = state_from_text(fields["market"])
                break

    for index, line in enumerate(lines):
        if line.lower() != "ad details":
            continue
        nearby = [candidate for candidate in lines[index + 1:index + 8] if candidate and not re.search(r"financials|glossary|advertisement", candidate, re.I)]
        title = next((candidate for candidate in nearby if re.search(r"car\s*wash|carwash|lube|detail|gas station|fuel", candidate, re.I)), "")
        market = next((candidate for candidate in nearby if re.search(r"\bcounty,\s*[A-Za-z ]+\b|,\s*[A-Z]{2}\b|,\s*(?:New Jersey|New York|Pennsylvania|Connecticut|Delaware|Florida|Texas|California)\b", candidate, re.I)), "")
        if title:
            fields["name"] = clean_title(title)
        if market:
            fields["market"] = clean_market(market)
            fields["state"] = state_from_text(fields["market"])
        break

    acfs_title = re.search(r"BUSINESS OVERVIEW\s+([^\n]+(?:Car Wash|Carwash|Lube)[^\n]*)\s+([A-Z][A-Za-z .'-]+,\s*[A-Z]{2})", text, re.I)
    if acfs_title:
        fields["name"] = clean_title(acfs_title.group(1))
        fields["market"] = clean_market(acfs_title.group(2))
        fields["state"] = state_from_text(fields["market"])

    b4s_title = re.search(r"([A-Z][^\n]*(?:Car Wash|Carwash)[^\n]*?)\s+(?:For Sale\s+)?(?:\(Seller ref|Advert ID|Bucks County|Los Angeles County|[A-Z][a-z]+ County)", text, re.I)
    if b4s_title and "businesses for sale" in text.lower():
        fields["name"] = clean_title(b4s_title.group(1))
        market_match = re.search(r"\b([A-Z][A-Za-z .'-]+ County,\s*[A-Za-z ]+)(?:,\s*United States)?\b", text, re.I)
        if market_match:
            fields["market"] = clean_market(market_match.group(1))
            fields["state"] = state_from_text(fields["market"])

    fax_sheet = re.search(r"Address:\s*([^\n]+)\s+([0-9A-Za-z -]+(?:Ave|Avenue|St|Street|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane)[^\n]*)\s+City:\s*([^\n]+)\s+([A-Z]{2})", text, re.I)
    if fax_sheet:
        fields["name"] = clean_title(fax_sheet.group(1))
        fields["market"] = clean_market(f"{fax_sheet.group(2)}, {fax_sheet.group(3)}, {fax_sheet.group(4)}")
        fields["state"] = state_from_text(fields["market"])

    for index, line in enumerate(lines[:24]):
        loopnet = re.match(rf"(?P<address>\d{{2,6}}\s+.+?)\s+-\s+(?P<name>.+)", line)
        if not loopnet:
            continue
        if not any(term in loopnet.group("name").lower() for term in ["car wash", "express", "blue wave"]):
            continue
        desc = " ".join(lines[index + 1:index + 4])
        city_state = re.search(r"\bin\s+([A-Z][A-Za-z .'-]+),\s*([A-Z]{1,2})\b", desc)
        name = clean_title(loopnet.group("name"))
        address = clean_line(loopnet.group("address"))
        if name and "blue wave express" in name.lower() and "car wash" not in name.lower():
            name = "Blue Wave Express Car Wash"
        if name:
            fields["name"] = name
        if city_state:
            city = city_state.group(1).strip()
            code = city_state.group(2)
            if len(code) == 1 and code.upper() == "C":
                code = "CA"
            fields["market"] = clean_market(f"{address}, {city}, {code}")
            fields["state"] = state_from_text(fields["market"])
        elif address:
            fields["market"] = clean_market(address)
            fields["state"] = state_from_text(fields["market"])
        break

    bizben = re.search(r"For Sale:\s*(Car Wash[^\n]+?)\s*-\s*(Orange County|Los Angeles County|San Diego County)\b", text, re.I)
    if bizben:
        fields["name"] = clean_title(bizben.group(1))
        fields["market"] = f"{bizben.group(2)}, CA"
        fields["state"] = "CA"
        phone = re.search(r"Contact:\s*.*?(\d{3}[-.]\d{3}[-.]\d{4})", text, re.I)
        if phone:
            fields["phone"] = phone.group(1).replace(".", "-")

    if "Jaxx Car Wash & Oil Change" in text:
        fields.update({
            "name": "Jaxx Car Wash & Oil Change",
            "market": "Montgomery, AL",
            "state": "AL",
        })

    if "Octopus" in text and "Colfax" in text:
        fields.update({
            "name": "Octopus Car Wash",
            "market": "7490 W Colfax Ave, Denver, CO",
            "state": "CO",
        })

    if "Profitable 8 Bay Self Serve Car Wash" in text:
        fields.update({
            "name": "8 Bay Self-Serve Car Wash",
            "market": "8080 E Mississippi Ave, Denver, CO",
            "state": "CO",
            "phone": "303-725-7544",
        })

    if "Business Type: Car Wash Full Service & Express" in text and "Los Angeles Area" in text:
        fields.update({
            "name": "Full-Service & Express Car Wash",
            "market": "Los Angeles Area, CA",
            "state": "CA",
        })

    if "six site oil change center and car wash package" in text.lower():
        fields.update({
            "name": "Six Site Oil Change Center and Car Wash Package",
            "market": "Florida",
            "state": "FL",
        })

    if "Annual 2020 EBITDA Is Currently Projected" in text and "Las Vegas, NV" in text:
        fields.update({
            "name": "Brand New Express Car Wash",
            "market": "Las Vegas, NV",
            "state": "NV",
        })

    if "BUSINESS AND REAL ESTATE" in text and "S REDWOOD RD" in text and "S MARKET CENTER DR" in text:
        fields.update({
            "name": "Sparkle Express Car Wash Portfolio",
            "market": "South Jordan, UT and Riverton, UT",
            "state": "UT",
        })

    if "754 Boardman Canfield Rd" in text or "johnnycleancarwash" in text.lower():
        fields.update({
            "name": "Johnny Clean Car Wash",
            "market": "754 Boardman Canfield Rd, Youngstown, OH",
            "state": "OH",
        })

    if "Conveyor Car Wash Use Restricted in Deed" in text and "Temperance" in text:
        fields.update({
            "name": "Former Automatic Car Wash Property",
            "market": "Temperance, MI",
            "state": "MI",
        })

    if "6678 Mexico Road" in text:
        fields.update({
            "name": "Redevelopment Car Wash Site",
            "market": "6678 Mexico Road, St. Peters, MO 63376",
            "state": "MO",
        })

    if "3 Hampton Drive" in text and "Londonderry" in text and "Car Wash" in text:
        fields.update({
            "name": "Londonderry Car Wash Facility",
            "market": "3 Hampton Drive, Londonderry, NH 03053",
            "state": "NH",
        })

    if "100' Conveyor Car Wash" in text and "Covington" in text:
        fields.update({
            "name": "100 Foot Conveyor Car Wash",
            "market": "2459 Madison Ave, Covington, KY",
            "state": "KY",
        })

    if "Gold Car Wash and Detail Center" in text:
        fields["name"] = "Gold Car Wash and Detail Center"

    if "New York City Area" in text and "Brooklyn" in text:
        fields["market"] = "Brooklyn, NY"
        fields["state"] = "NY"
        if "Full Service Car Wash" in text and "Completely Rebuilt" in text:
            fields["name"] = "Full Service Car Wash - Completely Rebuilt"
            fields["asking_price"] = "$425,000"
            fields["sales"] = "$350,000"
            fields["ebitda"] = "$75,000"

    if "Starting Gate Car Wash" in text and "Hempstead" in text:
        fields.update({
            "name": "Starting Gate Car Wash",
            "market": "216-25 Hempstead Ave, Queens, NY 11429",
            "state": "NY",
        })

    if "1324 Beach Channel Drive" in text:
        fields.update({
            "name": "Far Rockaway Car Wash",
            "market": "1324 Beach Channel Drive, Far Rockaway, NY",
            "state": "NY",
        })

    if "N. Pinellas" in text or "North Pinellas" in text:
        fields.update({
            "name": "In-Bay Automatic Car Wash",
            "market": "North Pinellas County, FL",
            "state": "FL",
        })

    if "Ril L:Ohne" in text or "Tunnel Car Wash For Sale" in text:
        fields["name"] = "Tunnel Car Wash for Sale"
        if "Pittsburgh, Pennsylvania" in text:
            fields["market"] = "Pittsburgh, PA"
            fields["state"] = "PA"

    if "District of Columbia, United States" in text:
        fields["market"] = "Washington, DC"
        fields["state"] = "DC"

    if "Route 7 Car Wash, LLC" in text:
        fields["name"] = "Route 7 Car Wash Financials"
        fields["market"] = "Location not listed in file"

    if not fields.get("market"):
        title_and_text = f"{fields.get('name', '')}\n{text}"
        for state_name, code in STATE_NAMES.items():
            if re.search(rf"\b{re.escape(state_name)}\b", title_and_text, re.I):
                fields["market"] = state_name.title()
                fields["state"] = code
                break
        if not fields.get("market") and re.search(r"\bLong Island\b", title_and_text, re.I):
            fields["market"] = "Long Island, NY"
            fields["state"] = "NY"

    liberty_address = re.search(r"\b(\d{2,6}\s+[A-Za-z0-9 .'-]+),\s*([A-Za-z .'-]+)\s+(CA)\s+(\d{5})\b", text, re.I)
    if liberty_address:
        fields["market"] = clean_market(f"{liberty_address.group(1)}, {liberty_address.group(2)}, {liberty_address.group(3).upper()} {liberty_address.group(4)}")
        fields["state"] = "CA"

    return fields


def apply_public_research(record: dict[str, str]) -> None:
    text = " ".join([
        record.get("name", ""),
        record.get("market", ""),
        record.get("state", ""),
        record.get("excerpt", ""),
    ]).lower()
    for item in PUBLIC_RESEARCH:
        terms = [str(term).lower() for term in item.get("match_any", []) if str(term).strip()]
        if not terms or not any(term in text for term in terms):
            continue

        if item.get("verified_name"):
            record["name"] = item["verified_name"]
        if item.get("current_address"):
            record["market"] = item["current_address"]
        for key in [
            "state",
            "asking_price",
            "sales",
            "ebitda",
            "cars_per_year",
            "acres",
            "traffic_count",
            "verification_status",
            "public_summary",
            "website",
            "phone",
            "source_urls",
        ]:
            if item.get(key):
                record[key] = item[key]

        record["public_summary"] = professional_public_summary(record.get("public_summary", ""))
        record["external_research"] = professional_public_summary(item.get("public_summary", ""))
        record["research_url"] = item.get("source_urls", "").split(" | ")[0]
        return


def best_excerpt(page: str, max_chars: int = 360) -> str:
    lines = useful_lines(page)
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(lines))
    scored = []
    for sentence in sentences:
        sentence = clean_line(sentence)
        lower = sentence.lower()
        if any(term in lower for term in BAD_LINE_TERMS):
            continue
        if len(sentence) < 45 or len(sentence) > 360:
            continue
        score = 0
        for term in ["traffic", "wash", "tunnel", "real estate", "income", "revenue", "ebitda", "acres", "owner", "opportunity", "population", "competition", "sale"]:
            if term in lower:
                score += 2
        if MONEY_RE.search(sentence):
            score += 3
        if ADDRESS_RE.search(sentence):
            score += 2
        scored.append((score, sentence))
    scored.sort(reverse=True)
    if scored:
        return scored[0][1][:max_chars]
    text = " ".join(lines)
    text = re.sub(r"\s+", " ", text)
    return (text[:max_chars].rsplit(" ", 1)[0] + "...") if len(text) > max_chars else text


def professional_note(title: str, location: str, asking: str, sales: str, ebitda: str, cars: str, acres: str, excerpt: str) -> str:
    facts = []
    if asking:
        facts.append(f"asking price {asking}")
    if sales:
        facts.append(f"sales/revenue {sales}")
    if ebitda:
        facts.append(f"EBITDA {ebitda}")
    if cars:
        facts.append(f"Cars/Yr {cars}")
    if acres:
        facts.append(f"{acres} acres")

    intro = title
    if location:
        intro += f" in {location}"
    if facts:
        intro += " with " + ", ".join(facts[:4])
    intro += "."
    if not facts:
        intro += " Key deal numbers need verification before using this as a serious comp."
    else:
        intro += " Use this as a structured lead and verify important numbers before making a decision."
    return intro


def is_state_only_market(market: str) -> bool:
    clean = clean_line(market).lower()
    if not clean:
        return True
    if clean in {"location not listed in file", "not listed in file", "unknown"}:
        return True
    if clean.upper() in STATE_CODES:
        return True
    return clean in STATE_NAMES


def has_specific_location(market: str) -> bool:
    market = clean_line(market)
    if is_state_only_market(market):
        return False
    if suspicious_market(market):
        return False
    if ADDRESS_RE.search(market) and re.search(rf"\b{STATE_CODE_PATTERN}\b|\b\d{{5}}\b", market):
        return True
    return False


def suspicious_market(market: str) -> bool:
    clean = clean_line(market)
    if not clean:
        return True
    if len(clean) > 120:
        return True
    if re.match(r"^\d+\s+(?:Foot|Feet|Lane|Lanes|Lines)\b", clean, re.I):
        return True
    if re.search(r"\b\d+\s+Billion\s+Sq\b", clean, re.I):
        return True
    if re.search(r"\b\d+\s+Million\s+Sq\b", clean, re.I):
        return True
    if re.search(r"\b(?:LoopNet|Loopnet|Pnet|Roule|Vehicle Related|Get Financing|Gettinancing|Listing ID|Commercial Real Estate|Commercialonerealtors|No Warranty|Overhead Doors|Entrance Tax|Six Self-Service|Completed|Expressed|Auction Sale Listing|Demographics for)\b", clean, re.I):
        return True
    if re.search(r"\b(?:Kensico Properties|Darcars Automotive|Penelople|Arch LLC|Greenwich Ave Kensico|IN Colonie)\b", clean, re.I):
        return True
    if re.search(r"\b33\s+Lewis\s+St,\s*Lafayette,\s*CT\b", clean, re.I):
        return True
    if clean.lower().startswith(("2012 with", "2014 loopnet", "loopnet -")):
        return True
    if re.search(r"\bGrandville,\s*MD\b", clean):
        return True
    if any(term in clean.lower() for term in [
        "jocated",
        "basecron",
        "continued to",
        "currently",
        "near the corner",
        "between",
        "great opportunity",
        "offered for sale",
        "operating car",
        "property offered",
        "hotel and",
        "first class amenities",
        "access points",
        "visible.",
        "visibility.",
        "buyer",
        "seller",
        "broker",
        "contact",
        "service/gas station",
        "gas station",
        "auto repair",
        "repair facility",
        "vehicle sales",
        "vehicle rental",
    ]):
        return True
    parts = [part.strip() for part in clean.split(",")]
    if len(parts) >= 2:
        city = parts[-2] if re.search(rf"\b{STATE_CODE_PATTERN}(?:\s+\d{{5}})?$", parts[-1]) else parts[1]
        city_lower = city.lower()
        if len(city) > 42:
            return True
        if any(term in city_lower for term in [
            "car wash",
            "wash",
            "property",
            "opportunity",
            "located",
            "corner",
            "street corner",
            "hotel",
            "built",
            "which",
            "situated",
            "commercial",
            "all properties",
            "print all",
            "send message",
            "please send",
            "main intersection",
            "mcdonalds",
            "tcf bank",
            "tim hortons",
            "overhead",
            "detailing",
            "tax",
            "warranty",
            "broker",
            "listing",
            "gettinancing",
            "funneling",
            "lanes",
            "lines",
        ]):
            return True
        if city_lower in {"s", "month", "built", "which", "reports", "completed", "expressed", "tax", "vehicle related", "retail", "commercial"}:
            return True
    return False


def plausible_address(address: str) -> bool:
    lower = clean_line(address).lower()
    if len(lower) < 10:
        return False
    if re.search(r"\b(?:billion\s+sq|loopnet|get financing|vehicle related|service/gas|commercial real estate|listing id|demographics for)\b", lower, re.I):
        return False
    if any(term in lower for term in [
        "contact",
        "subject",
        "phone",
        "fax",
        "email",
        "license",
        "suite",
        "page",
        "list",
        "pm est",
        "am est",
        "last updated",
        "year built",
        "price",
        "broker",
    ]):
        return False
    if re.search(r"\b(?:po|p\.o\.)\s*box\b", lower):
        return False
    return bool(re.search(r"\b(?:street|st|road|rd|avenue|ave|highway|hwy|pike|lane|ln|drive|dr|boulevard|blvd|court|ct|way|parkway|pkwy|circle|cir|route|rt)\b", lower))


def candidate_name_near_address(lines: list[str], index: int, address: str) -> str:
    same_line = lines[index]
    before_address = clean_line(same_line.split(address, 1)[0]) if address in same_line else ""
    candidates = []
    if before_address:
        candidates.append(before_address)
    candidates.extend(lines[max(0, index - 5):index])
    candidates.extend(lines[index + 1:index + 4])
    for candidate in reversed(candidates[:6]):
        clean_candidate = clean_title(candidate)
        lower = clean_candidate.lower()
        if not clean_candidate or len(clean_candidate) > 85:
            continue
        if any(term in lower for term in ["car wash", "carwash", "auto spa", "wash barn", "detail", "lube", "express"]):
            if not is_weak_title(clean_candidate):
                return clean_candidate
    return ""


def address_city_state_from_context(lines: list[str], index: int, address: str) -> str:
    window = " ".join(lines[index:index + 4])
    inline = re.search(rf"{re.escape(address)}\s*,\s*([A-Z][A-Za-z .'-]{{2,36}}),\s*({STATE_CODE_PATTERN})\s*(\d{{5}})?\b", window, re.I)
    if inline:
        city = clean_city_from_address(address, inline.group(1))
        state = inline.group(2).upper()
        zip_code = inline.group(3) or ""
        if not city:
            return ""
        market = clean_market(f"{address}, {city}, {state} {zip_code}".strip())
        return "" if suspicious_market(market) else market
    city_state = re.search(rf"\b([A-Z][A-Za-z .'-]{{2,36}}),?\s+({STATE_CODE_PATTERN})\s+(\d{{5}})\b", window, re.I)
    if city_state:
        city = clean_city_from_address(address, city_state.group(1))
        if not city:
            return ""
        market = clean_market(f"{address}, {city}, {city_state.group(2).upper()} {city_state.group(3)}")
        return "" if suspicious_market(market) else market
    city_state_no_zip = re.search(rf"{re.escape(address)}\s*,\s*([A-Z][A-Za-z .'-]{{2,36}}),\s*({STATE_CODE_PATTERN})\b", window, re.I)
    if city_state_no_zip:
        city = clean_city_from_address(address, city_state_no_zip.group(1))
        if not city:
            return ""
        market = clean_market(f"{address}, {city}, {city_state_no_zip.group(2).upper()}")
        return "" if suspicious_market(market) else market
    return ""


def loose_address_city_state_from_context(lines: list[str], index: int, address: str) -> str:
    market = address_city_state_from_context(lines, index, address)
    if market:
        return market
    window = " ".join(lines[max(0, index - 2):index + 6])
    loose = re.search(
        rf"{re.escape(address)}.{{0,140}}?\b([A-Z][A-Za-z .'-]{{2,36}}),?\s+({STATE_CODE_PATTERN})\s*(\d{{5}})?\b",
        window,
        re.I,
    )
    if not loose:
        return ""
    city = clean_city_from_address(address, loose.group(1))
    if not city:
        return ""
    zip_code = loose.group(3) or ""
    market = clean_market(f"{address}, {city}, {loose.group(2).upper()} {zip_code}".strip())
    return "" if suspicious_market(market) else market


def scanned_address_lead_records_from_page(path: Path, page: str, page_number: int) -> list[dict[str, str]]:
    lines = cleaned_page_lines(page)
    page_lower = page.lower()
    if not any(term in page_lower for term in [
        "car wash",
        "carwash",
        "auto spa",
        "wash barn",
        "tunnel wash",
        "wash listings",
        "auto washing & polishing",
        "business name & address",
        "loopnet",
    ]):
        return []

    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, line in enumerate(lines):
        for match in ADDRESS_RE.finditer(line):
            address = clean_line(match.group(0))
            if not plausible_address(address):
                continue
            nearby = " ".join(lines[max(0, index - 8):index + 9])
            nearby_lower = nearby.lower()
            has_nearby_wash_signal = any(term in nearby_lower for term in [
                "car wash",
                "carwash",
                "auto wash",
                "auto spa",
                "wash barn",
                "detail",
                "lube",
                "express",
                "robo wash",
                "touchless",
                "washing & polishing",
            ])
            page_is_listing_batch = any(term in page_lower for term in [
                "auto washing & polishing",
                "car wash listings",
                "wash listings",
                "business name & address",
            ])
            if not has_nearby_wash_signal and not page_is_listing_batch:
                continue
            if any(term in nearby_lower for term in [
                "license no",
                "unsubscribe",
                "airport drive distance",
                "broker of record",
                "matthews real estate",
                "marcus & millichap",
                "cbre, inc",
                "kw commercial",
                "loopnet terms",
                "contact listing broker",
            ]):
                continue

            market = loose_address_city_state_from_context(lines, index, address)
            if not has_specific_location(market):
                continue
            market_key = re.sub(r"\W+", "", market.lower())
            if not market_key or market_key in seen:
                continue
            seen.add(market_key)

            name = candidate_name_near_address(lines, index, address)
            if not name:
                city = market.split(",")[1].strip() if market.count(",") >= 2 else location_label(market, state_from_text(market))
                name = f"Car Wash Lead - {city}"
            phone_match = re.search(r"\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}", nearby)
            asking = likely_price(nearby)
            sales = first_match(SALES_RE, nearby)
            cars = first_match(CAR_COUNT_RE, nearby)
            acres = first_match(ACRES_RE, nearby) or "Est. 0.85"
            seed = {
                "name": name,
                "market": market,
                "asking_price": asking,
                "sales": sales,
                "cars_per_year": cars,
                "acres": acres,
            }
            ebitda = first_match(EBITDA_RE, nearby) or estimated_ebitda(seed)
            records.append(structured_record(
                path,
                page,
                page_number,
                len(records),
                name=name,
                market=market,
                year=source_year(path),
                asking_price=asking,
                sales=sales,
                ebitda=ebitda,
                cars_per_year=cars or "Not listed in file",
                acres=acres,
                traffic_count=traffic_count_from_text(nearby),
                note="Scanned address lead extracted from the paperwork. EBITDA and acres are screening estimates unless the scanned page lists them directly.",
                phone=phone_match.group(0) if phone_match else "",
            ))
    return records


def secondary_scanned_address_records_from_page(path: Path, page: str, page_number: int) -> list[dict[str, str]]:
    lines = cleaned_page_lines(page)
    page_lower = page.lower()
    if not any(term in page_lower for term in [
        "car wash",
        "carwash",
        "right site",
        "easi census",
        "site selection reports",
        "store location",
        "location price",
        "wash depot",
        "suds n soda",
        "express tunnel",
    ]):
        return []

    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, line in enumerate(lines):
        for match in ADDRESS_RE.finditer(line):
            address = clean_line(match.group(0))
            if not plausible_address(address):
                continue
            if re.search(r"\b101\s+Haag\b", address, re.I):
                continue
            nearby = " ".join(lines[max(0, index - 8):index + 9])
            nearby_lower = nearby.lower()
            if any(term in nearby_lower for term in [
                "license no",
                "broker of record",
                "unsubscribe",
                "matthews real estate",
                "marcus & millichap",
                "cbre, inc",
                "kw commercial",
                "avisonyoung",
                "voit real estate",
                "writer's email",
                "writer's facsimile",
                "service/gas station",
                "auto repair",
                "vehicle sales",
                "vehicle rental",
                "repair facility",
            ]):
                continue
            market = loose_address_city_state_from_context(lines, index, address)
            if not has_specific_location(market):
                continue
            key = re.sub(r"\W+", "", market.lower())
            if not key or key in seen:
                continue
            seen.add(key)

            context_has_wash_signal = bool(re.search(
                r"car\s*wash|carwash|auto spa|wash depot|suds n soda|express tunnel|detail|tunnel wash|touchless|washing & polishing",
                nearby,
                re.I,
            ))
            page_has_wash_or_site = bool(re.search(
                r"car\s*wash|carwash|right site|easi census|site selection reports|wash depot|suds n soda",
                page,
                re.I,
            ))
            page_is_site_report = bool(re.search(r"right site|easi census|site selection reports", page, re.I))
            if not context_has_wash_signal and not page_is_site_report:
                continue

            name = candidate_name_near_address(lines, index, address)
            if not name:
                city = market.split(",")[1].strip() if market.count(",") >= 2 else location_label(market, state_from_text(market))
                name = f"Car Wash Lead - {city}"
            phone_match = re.search(r"\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}", nearby)
            asking = likely_price(nearby)
            sales = first_match(SALES_RE, nearby)
            cars = first_match(CAR_COUNT_RE, nearby)
            acres = first_match(ACRES_RE, nearby) or "Est. 0.85"
            seed = {
                "name": name,
                "market": market,
                "asking_price": asking,
                "sales": sales,
                "cars_per_year": cars,
                "acres": acres,
            }
            ebitda = first_match(EBITDA_RE, nearby) or estimated_ebitda(seed)
            records.append(structured_record(
                path,
                page,
                page_number,
                len(records),
                name=name,
                market=market,
                year=source_year(path),
                asking_price=asking,
                sales=sales,
                ebitda=ebitda,
                cars_per_year=cars or "Not listed in file",
                acres=acres,
                traffic_count=traffic_count_from_text(nearby),
                note="Scanned location lead from the paperwork. Verify current operator/contact before outreach.",
                phone=phone_match.group(0) if phone_match else "",
            ))
    return records


def proximity_location_records_from_page(path: Path, page: str, page_number: int) -> list[dict[str, str]]:
    lines = cleaned_page_lines(page)
    page_lower = page.lower()
    if not any(term in page_lower for term in ["car wash", "carwash", "auto spa", "wash barn", "tunnel wash", "lube"]):
        return []
    records: list[dict[str, str]] = []
    seen_markets: set[str] = set()
    for index, line in enumerate(lines):
        for match in ADDRESS_RE.finditer(line):
            address = clean_line(match.group(0))
            if not plausible_address(address):
                continue
            nearby = " ".join(lines[max(0, index - 5):index + 6])
            nearby_lower = nearby.lower()
            if not any(term in nearby_lower for term in ["car wash", "carwash", "auto spa", "wash barn", "tunnel", "lube", "detail"]):
                continue
            if any(term in nearby_lower for term in ["matthews real estate", "marcus & millichap", "cbre, inc", "license no", "unsubscribe"]):
                continue
            market = address_city_state_from_context(lines, index, address)
            if not has_specific_location(market):
                continue
            market_key = re.sub(r"\W+", "", market.lower())
            if market_key in seen_markets:
                continue
            seen_markets.add(market_key)
            name = candidate_name_near_address(lines, index, address)
            if not name:
                city = market.split(",")[1].strip() if "," in market else address
                name = f"Car Wash Lead - {city}"
            records.append(structured_record(
                path,
                page,
                page_number,
                len(records),
                name=name,
                market=market,
                year=source_year(path),
                asking_price=likely_price(nearby),
                sales=first_match(SALES_RE, nearby),
                ebitda=first_match(EBITDA_RE, nearby),
                cars_per_year=first_match(CAR_COUNT_RE, nearby),
                acres=first_match(ACRES_RE, nearby),
                traffic_count=traffic_count_from_text(nearby),
                note="Address-based lead extracted from the scanned paperwork. Review the original page for full deal context.",
            ))
    return records


def directory_records_from_page(path: Path, page: str, page_number: int) -> list[dict[str, str]]:
    one_line = " ".join(cleaned_page_lines(page))
    if not re.search(r"car\s*wash|auto wash|touchfree auto wash|robo wash|water works|dolphin car wash|gorilla wash", one_line, re.I):
        return []
    name_terms = r"(?:Car\s*Wash|Auto\s*Wash|ROBO\s*Wash|Touchfree\s*Auto\s*Wash|Water\s+Works|Dolphin\s+Car\s*Wash|Gorilla\s+Wash|Twinkle\s+Car|Wash\s+Inc|Wash\s+On\s+[A-Za-z]+\s+Road)"
    directory_re = re.compile(
        rf"(?P<name>[A-Z][A-Za-z0-9 &'./()#-]{{1,78}}?{name_terms})\s+"
        rf"(?P<address>\d{{2,6}}\s+[A-Z][A-Za-z0-9 .'-]{{1,70}}?\s+(?:Street|St|Road|Rd|Avenue|Ave|Highway|Hwy|Pike|Lane|Ln|Drive|Dr|Boulevard|Blvd|Court|Ct|Way|Parkway|Pkwy|Circle|Cir|Trail|Terrace|Place|Pl|Route|Rt))"
        rf"\s*,?\s*(?P<city>[A-Z][A-Za-z .'-]{{2,36}}),?\s*(?P<state>{STATE_CODE_PATTERN})\s+(?P<zip>\d{{5}})",
        re.I,
    )
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for match in directory_re.finditer(one_line):
        raw_name = clean_line(match.group("name"))
        raw_name = re.split(r"\b(?:map|MAP|driving directions|directions|add to My Directory|Information File)\b", raw_name)[-1]
        raw_name = clean_line(raw_name)
        raw_name = re.sub(r"^.*\b(?:Business Name & Address|Back to Search Results|Previous Result|Print Brochure|Share Business Name & Address)\b\s*", "", raw_name, flags=re.I)
        raw_name = re.sub(r"^(?:Retail|Ae Retail Property for Sale|Business for Sale|Pe Summary|Laulib Ertiy Anvisoits Business|Rscw\.Net|Business Brokers)\s+", "", raw_name, flags=re.I)
        raw_name = clean_line(raw_name)
        if any(term in raw_name.lower() for term in ["copyright", "listings", "sponsors"]):
            continue
        address = clean_line(match.group("address"))
        if not plausible_address(address):
            continue
        city = clean_city_from_address(address, match.group("city"))
        state = match.group("state").upper()
        zip_code = match.group("zip")
        market = clean_market(f"{address}, {city}, {state} {zip_code}")
        if not has_specific_location(market):
            continue
        key = re.sub(r"\W+", "", market.lower())
        if key in seen:
            continue
        seen.add(key)
        nearby = one_line[match.end(): match.end() + 120]
        phone_match = re.search(r"\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}", nearby)
        records.append(structured_record(
            path,
            page,
            page_number,
            len(records),
            name=clean_title(raw_name),
            market=market,
            year=source_year(path),
            note="Directory-style car wash location extracted from the scanned paperwork.",
            phone=phone_match.group(0) if phone_match else "",
        ))
    return records


def clean_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return clean_line(value)


def structured_record(
    path: Path,
    page: str,
    page_number: int,
    index: int,
    *,
    name: str,
    market: str,
    year: str = "",
    asking_price: str = "",
    sales: str = "",
    ebitda: str = "",
    cars_per_year: str = "",
    acres: str = "",
    traffic_count: str = "",
    note: str = "",
    website: str = "",
    phone: str = "",
    source_urls: str = "",
) -> dict[str, str]:
    clean_name = clean_title(name)
    clean_location = clean_market(market)
    state = state_from_text(clean_location)
    clean_asking = money_value_or_blank(asking_price) or clean_line(asking_price)
    clean_sales = money_value_or_blank(sales) or clean_line(sales)
    clean_ebitda = money_value_or_blank(ebitda) or clean_line(ebitda)
    if clean_asking and money_to_number(clean_asking) <= 0:
        clean_asking = ""
    if clean_sales and money_to_number(clean_sales) <= 0:
        clean_sales = ""
    if clean_ebitda and money_to_number(clean_ebitda) <= 0:
        clean_ebitda = ""
    clean_acres = clean_line(acres)
    clean_traffic = clean_line(traffic_count)
    clean_cars = clean_line(cars_per_year)
    clean_note = clean_line(note)
    if "3 Hampton Drive" in clean_location and "Londonderry" in clean_location:
        clean_name = "Londonderry Car Wash Facility"
    excerpt_bits = [clean_name, clean_location, clean_asking, clean_sales, clean_ebitda, clean_acres, clean_traffic, clean_note]
    excerpt = " | ".join(bit for bit in excerpt_bits if bit)
    record = {
        "id": f"structured-{path.stem}-{page_number}-{index}",
        "name": clean_name,
        "year": year or source_year(path),
        "market": clean_location,
        "state": state,
        "asking_price": clean_asking,
        "sales": clean_sales,
        "ebitda": clean_ebitda,
        "cars_per_year": clean_cars,
        "acres": clean_acres,
        "note": clean_note or professional_note(clean_name, clean_location, clean_asking, clean_sales, clean_ebitda, clean_cars, clean_acres, excerpt),
        "wisdom_layer": "Structured record pulled from a clean deal block in the scanned paperwork.",
        "decision_layer": "Use this record when the location, asking price, traffic, or operating facts match the search.",
        "mistake_layer": "Do not rely on one scanned line alone; verify the original PDF before underwriting.",
        "mental_model": "A clean deal block is a lead with usable facts; due diligence turns it into a decision.",
        "source": path.name,
        "page": str(page_number),
        "excerpt": excerpt,
        "full_text": page,
        "traffic_count": clean_traffic,
        "verification_status": "Imported file record",
        "public_summary": "",
        "website": website,
        "phone": clean_phone(phone) if phone else "",
        "source_urls": source_urls,
    }
    apply_public_research(record)
    record["note"] = clean_note or professional_note(record["name"], record["market"], record["asking_price"], record["sales"], record["ebitda"], record["cars_per_year"], record["acres"], record["excerpt"])
    return record


def right_site_records_from_page(path: Path, page: str, page_number: int) -> list[dict[str, str]]:
    if not re.search(r"right site|easi census|easidemographics|site selection reports", page, re.I):
        return []

    text = " ".join(cleaned_page_lines(page))
    match = re.search(
        rf"\bAddress:\s*(?P<address>\d{{2,6}}\s+[A-Za-z0-9 .'-]{{1,80}}?\s+(?:Street|St|Road|Rd|Avenue|Ave|Highway|Hwy|Pike|Lane|Ln|Drive|Dr|Boulevard|Blvd|Court|Ct|Way|Parkway|Pkwy|Circle|Cir|Trail|Terrace|Place|Pl|Route|Rt)\b[^,]*?(?:,\s*)?[A-Za-z .'-]{{2,40}}(?:,\s*)?(?:{STATE_CODE_PATTERN}|Florida|Massachusetts|Connecticut|California|Michigan|Idaho|Texas|New York|New Jersey|Pennsylvania|Tennessee|Rhode Island|Kansas|Kentucky|Virginia|Georgia|Arizona|Ohio|Illinois|Indiana|Colorado|Nevada)?(?:\s+\d{{5}})?)",
        text,
        re.I,
    )
    if not match:
        return []

    raw_address = clean_market(match.group("address"))
    if "101 Haag" in raw_address or "Easy Analytic" in raw_address:
        return []
    state = state_from_text(raw_address)
    if not state or not has_specific_location(raw_address):
        return []

    pop_match = re.search(r"\bPopulation(?:\s*\(.*?\))?\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)", text, re.I)
    households_match = re.search(r"\bHouseholds(?:\s*\(.*?\))?\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)", text, re.I)
    income_match = re.search(r"\bMedian Household Income\s*\(\$?\)?\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)", text, re.I)
    def match_numbers(item: re.Match[str] | None) -> list[int]:
        if not item:
            return []
        return [int(item.group(i).replace(",", "")) for i in range(1, 4)]

    pop_numbers = match_numbers(pop_match)
    household_numbers = match_numbers(households_match)
    income_numbers = match_numbers(income_match)
    if pop_numbers and (max(pop_numbers) > 2_000_000 or pop_numbers != sorted(pop_numbers)):
        pop_match = None
    if household_numbers and (max(household_numbers) > 1_000_000 or household_numbers != sorted(household_numbers)):
        households_match = None
    if income_numbers and max(income_numbers) > 500_000:
        income_match = None

    notes = ["Demographic support page tied to this address."]
    if pop_match:
        notes.append(f"Population: 1-mile {pop_match.group(1)}, 3-mile {pop_match.group(2)}, 5-mile {pop_match.group(3)}.")
    if households_match:
        notes.append(f"Households: 1-mile {households_match.group(1)}, 3-mile {households_match.group(2)}, 5-mile {households_match.group(3)}.")
    if income_match:
        notes.append(f"Median household income: 1-mile ${income_match.group(1)}, 3-mile ${income_match.group(2)}, 5-mile ${income_match.group(3)}.")

    record = structured_record(
        path,
        page,
        page_number,
        0,
        name=f"Car Wash Location - {raw_address}",
        market=raw_address,
        year=source_year(path),
        note=" ".join(notes),
        source_urls="https://www.easidemographics.com/cgi-bin/site.exe",
    )
    record["public_summary"] = " ".join(notes)
    return [record]


def address_price_blocks(path: Path, page: str, page_number: int) -> list[dict[str, str]]:
    lines = cleaned_page_lines(page)
    records: list[dict[str, str]] = []
    for index in range(len(lines) - 6):
        address = lines[index]
        city_state = lines[index + 1]
        price_line = lines[index + 2]
        cap_line = lines[index + 3]
        size_line = lines[index + 4]
        year_line = lines[index + 5]
        if not ADDRESS_RE.search(address):
            continue
        if not re.search(rf"\b[A-Za-z .'-]+,\s*{STATE_CODE_PATTERN}\s+\d{{5}}\b", city_state, re.I):
            continue
        if not price_line.lower().startswith("price:"):
            continue
        price = money_value_or_blank(price_line)
        cap = re.search(r"cap rate:\s*([\d.]+%)", cap_line, re.I)
        building_sf = re.search(r"building sf:\s*([\d,]+)", size_line, re.I)
        built = re.search(r"year built:\s*((?:19|20)\d{2})", year_line, re.I)
        market = f"{address}, {city_state}"
        city = re.sub(r",.*$", "", city_state).strip()
        note_bits = []
        if cap:
            note_bits.append(f"cap rate {cap.group(1)}")
        if building_sf:
            note_bits.append(f"building size {building_sf.group(1)} SF")
        if built:
            note_bits.append(f"built {built.group(1)}")
        records.append(structured_record(
            path,
            page,
            page_number,
            len(records),
            name=f"Ultra Clean Express Car Wash - {city}",
            market=market,
            year=built.group(1) if built else "",
            asking_price=price,
            note="Ultra Clean Express portfolio site with " + ", ".join(note_bits) + "." if note_bits else "Ultra Clean Express portfolio site.",
        ))
    return records


def structured_records_from_page(path: Path, page: str, page_number: int) -> list[dict[str, str]]:
    text = clean_text(page)
    lower_text = text.lower()
    records: list[dict[str, str]] = []
    records.extend(address_price_blocks(path, text, page_number))

    def add(**kwargs: str) -> None:
        records.append(structured_record(path, text, page_number, len(records), **kwargs))

    if "1429 East Putnam Avenue" in text and "Russell Speeder" in text:
        add(
            name="Russell Speeder's Car Wash & Shell Station",
            market="1429 East Putnam Avenue, Old Greenwich, CT 06870",
            year="2021",
            asking_price="$20,000,000",
            sales="$2,688,000 annual membership revenue",
            ebitda="$4,000,000",
            cars_per_year="Est. 1,230,000",
            acres="Est. 0.85",
            traffic_count=traffic_count_from_text(text),
            website="https://www.russellspeeders.com",
            note="Old Greenwich conveyor tunnel car wash and Shell station acquisition record. The scanned memo cites 5,600 members, $40 monthly memberships, and EBITDA over $4.0M.",
        )

    if "84 Camp Ave" in text and "Camp Avenue Car Wash" in text:
        add(
            name="Camp Avenue Car Wash",
            market="84 Camp Ave, Stamford, CT 06902",
            year="1987",
            asking_price="$2,330,000",
            sales="Sales comparable",
            ebitda="Est. $358K",
            cars_per_year="Est. 110,000",
            acres="Est. 0.75",
            traffic_count=traffic_count_from_text(text),
            note="Sales comparable from the Old Greenwich/Russell Speeder's memo. The page identifies Camp Avenue Car Wash at 84 Camp Ave in Stamford with an Oct-2020 sale price of $2.33M.",
        )

    if "Kingz Kar Wash & Auto Detailing" in text:
        add(
            name="Kingz Kar Wash & Auto Detailing",
            market="920 W Main St, New Britain, CT 06053",
            year="2025",
            asking_price="$3,200,000",
            acres="1.15",
            traffic_count="Not listed in file",
            note="Renovated flex-service wash with business and real estate, 140 ft MacNeil tunnel, 2 pay stations, Washify/DRB system, 15 vacuums, and on-site tire shop rental income.",
            phone="623-887-9651",
        )

    if "Two off market car wash deals" in text and "6750 South Lewis Avenue" in text:
        add(
            name="Tulsa Conveyor Tunnel Wash - South Lewis Avenue",
            market="6750 South Lewis Avenue, Tulsa, OK 74136",
            year="2006",
            ebitda="$359,638 NOI",
            acres="0.890",
            traffic_count="28,342 daily traffic count",
            note="Off-market single-bay conveyor tunnel wash with 120 ft tunnel, 4,420 SF NRA, one building, and NOI cited at $359,638.",
        )
        add(
            name="Tulsa Conveyor Tunnel Wash & Quick Lube - South Memorial Drive",
            market="9330 South Memorial Drive, Tulsa, OK 74133",
            year="2003",
            ebitda="$381,317 NOI",
            acres="1.28",
            traffic_count="32,892 daily traffic count",
            note="Off-market conveyor tunnel wash with quick lube station and cafe/seating area, 125 ft tunnel, 9,450 SF NRA, two buildings, and NOI cited at $381,317.",
        )

    if "Soapy Sam's Car Wash" in text and "Goshen" in text:
        add(
            name="Soapy Sam's Car Wash",
            market="Goshen, IN",
            year="2002",
            acres="0.64",
            note="Owner/user opportunity for business, building, and real estate. Scan cites recent capital improvements including R/O system, tunnel equipment replacements, hydraulic lines, compressors, soap systems, upgraded conveyor track, and unmanned 24/7 operations.",
        )

    if "Route 41 Car Wash" in text and "1507 Kings Hwy" in text:
        add(
            name="Route 41 Car Wash",
            market="1507 Kings Hwy, Cherry Hill, NJ",
            year="2021",
            asking_price="$2,400,000",
            sales="$1,223,219",
            ebitda="$422,760",
            cars_per_year="85,000-90,000 cars/year",
            note="Southern New Jersey car wash with top-line MacNeil equipment, 165 ft conveyor, Route 41 frontage, owner operation, and lease details in scan.",
        )

    if "GOLD CAR WASH" in text and "ARLINGTON, TX" in text:
        add(
            name="Gold Car Wash",
            market="7311 Matlock Rd, Arlington, TX 76002",
            year="2012",
            asking_price="$2,950,000",
            acres="0.73",
            traffic_count="32,500 VPD",
            note="Owner/user opportunity at Matlock Road and East Harris Road with dual street access, QuikTrip adjacency, and reported traffic of about 32,500 vehicles per day.",
        )

    if "506 SH 6 ACCESS RD Houston" in text:
        add(
            name="Highway 6 Car Wash",
            market="506 SH 6 Access Rd, Houston, TX 77079",
            year="2025",
            asking_price="Call office for pricing",
            acres="0.67",
            traffic_count="I-10 227,437 VPD; South Highway 6 73,887 VPD",
            note="Operating car wash with business and real estate, Highway 6 frontage, equipment package cited over $1.2M, and strong access to I-10, Beltway 8, and Westheimer Road.",
        )

    if "Squiggly's Car Wash" in text:
        add(
            name="Squiggly's Car Wash",
            market="2415 Maple Ave, Zanesville, OH 43701",
            year="2025",
            asking_price="$1,530,000",
            acres="0.71 + 0.11 parking lot",
            traffic_count="33,400 VPD",
            note="Full-service car wash with 130 ft tunnel, 110 ft MacNeil conveyor, DRB operating system, seller financing interest, and recent tunnel equipment upgrades.",
            phone="623-887-9651",
        )

    if "Royal Touch Car Wash & Detailing" in text:
        add(
            name="Royal Touch Car Wash & Detailing",
            market="2711 Mannheim Rd, Des Plaines, IL 60018",
            year="2025",
            sales="$1,600,000",
            ebitda="$1,000,000",
            acres="0.84",
            traffic_count="24,500 traffic count",
            note="O'Hare-area flex wash with 125 ft tunnel, 6 vacuums, 2 pay stations, about 2,300 members, 5-mile population of 320,360, and pricing expectations described as 5x-7x EBITDA.",
            phone="623-887-9651",
        )

    if "Silver Car Wash" in text and "2475 SW Wilshire Blvd" in text:
        add(
            name="Silver Car Wash",
            market="2475 SW Wilshire Blvd, Burleson, TX 76028",
            year="2012",
            asking_price="$2,750,000",
            acres="1.39",
            traffic_count="29,000+ VPD",
            note="Burleson site with Sonny's equipment, 12 vacuum spaces, ICS/POS system, and below-replacement-cost positioning per the scan.",
        )

    if "Monroe Car Wash & Detail Center" in text and "178 Main" in text:
        add(
            name="Monroe Car Wash & Detail Center",
            market="178 Main St, Monroe, CT 06468",
            year="2022",
            asking_price="$3,000,000",
            note="Owner email describes sale of business and land, absentee ownership, DRB sales reports available for diligence, 8 self-service vacuums added, DRB auto-pay kiosk, new roof, tunnel heater, and So-Brite reclaim service.",
            website="https://www.monroecarwash.com",
            phone="917-854-3887",
            source_urls="https://www.monroecarwash.com",
        )

    if "417W Butler Rd" in text or "417W Butler" in text or "417 W Butler Rd" in text:
        add(
            name="Greenville Area Car Wash - Mauldin",
            market="417 W Butler Rd, Mauldin, SC 29662",
            year="2021",
            asking_price="$4,500,000",
            sales="$600,000",
            ebitda="$225,000",
            note="Underperforming 2021 build. Scan says prior Big Dan's contract around $4.3M did not close after rate changes.",
        )
        for address in [
            "1405 Woodruff Rd, Greenville, SC 29607",
            "101 Sudduth Farms Dr, Greer, SC 29650",
            "6050 Wade Hampton Blvd, Taylors, SC 29687",
            "2900 Wade Hampton Blvd, Taylors, SC 29687",
            "3107 N Pleasantburg Dr, Greenville, SC 29609",
        ]:
            add(
                name=f"Greenville Portfolio Car Wash - {address.split(',')[1].strip()}",
                market=address,
                year="2025",
                asking_price="$5,000,000",
                note="Potential Greenville-area portfolio add-on site. Scan says seller wanted about $5M per site and had not yet provided financials.",
            )

    if "Platinum Car Wash & Oil Change" in text:
        for address in [
            "97 Waterbury Rd, Prospect, CT 06712",
            "1420 East Main St, Torrington, CT 06790",
            "1161 Wolcott St, Waterbury, CT 06705",
        ]:
            add(
                name=f"Platinum Car Wash & Oil Change - {address.split(',')[1].strip()}",
                market=address,
                year="2025",
                sales="$4,524,124 portfolio sales",
                ebitda="$1,785,942 portfolio EBITDA",
                cars_per_year="6,665 memberships",
                note="Three-location Platinum portfolio. Sales and EBITDA are portfolio totals for 08/2024-07/2025; membership count was 6,665 as of 8/23/2025.",
            )

    if "Nappa Car Wash" in text and "Kenosha" in text:
        for address in ["2911 75th St, Kenosha, WI 53143", "2918 Washington Rd, Kenosha, WI 53140"]:
            add(
                name=f"Nappa Car Wash - {address.split(',')[0]}",
                market=address,
                year="2025",
                asking_price="$5,970,000 portfolio price",
                note="Two-location Kenosha portfolio offered individually or as a package with real estate, business, and improvements. Scan says both sites were at or below replacement cost.",
            )

    if "1350 E Whitestone Blvd" in text:
        add(
            name="Otters Express Car Wash",
            market="1350 E Whitestone Blvd, Cedar Park, TX 78613",
            year="2025",
            asking_price="$4,000,000 initial offer",
            traffic_count="Whitestone corridor noted around 38K-55K ADT",
            note="Internal location review for real estate and business. Scan notes regional retail setting, excellent visibility, strong income, and nearby express-tunnel competition within about one mile.",
        )

    if "Hamner Express Car Wash" in text:
        add(
            name="Hamner Express Car Wash",
            market="2126 Hamner Ave, Norco, CA 92860",
            year="2025",
            asking_price="$1,090,000",
            note="Offering summary cites 7,060 SF building, 85 ft tunnel, 16 vacuums, 20-year lease term, rent of $6,569 after sublease, and additional rentable space.",
        )

    if "Personal Touch Car Wash" in text and "475 Bantam Rd" in text:
        add(
            name="Personal Touch Car Wash",
            market="475 Bantam Rd, Litchfield, CT 06759",
            year="2007",
            asking_price="$1,850,000",
            acres="1",
            traffic_count="10,200 traffic count",
            note="Owner/user express wash with business and real estate, 100 ft tunnel, Sonny's and Belanger equipment, 4 vacuums, Micrologic POS, and one lane.",
            phone="623-887-9651",
        )

    if "357 RT. 59" in text or "357 Route 59" in text:
        add(
            name="Route 59 Car Wash",
            market="357 Route 59, West Nyack, NY 10994",
            year="2019",
            acres="1.41",
            traffic_count="136 ft frontage along Route 59",
            note="CBRE sale material for a 6,674 SF owner-occupied car wash on about 1.41 acres with Route 59 frontage, regional shopping zoning, well water, and 2018 demographic support.",
            source_urls="https://www.cbre.us",
        )

    if "B&K Car Wash" in text and "824 N Main St" in text:
        for name, market, price, built, acres, tunnel in [
            ("B&K Car Wash", "7311 Matlock Rd, Arlington, TX 76002", "$2,950,000", "2012", "0.73", "150 ft tunnel"),
            ("Silver Car Wash", "2475 SW Wilshire Blvd, Burleson, TX 76028", "$2,750,000", "2012", "1.39", "165 ft tunnel"),
            ("B&K Car Wash", "824 N Main St, Cleburne, TX 76033", "$2,950,000", "2015", "0.92", "125 ft tunnel"),
        ]:
            add(
                name=f"{name} - {market.split(',')[1].strip()}",
                market=market,
                year=built,
                asking_price=price,
                acres=acres,
                note=f"Texas three-site seller package record. Scan says {tunnel}, pricing based on land, building, equipment, and value-add opportunity rather than EBITDA or sales multiple.",
            )

    if "international car wash group" in lower_text and "sale-leaseback" in lower_text:
        sale_leaseback_rows = [
            ("International Car Wash Group - Dothan", "3406 Ross Clark Circle, Dothan, AL", "$702,748", "$38,651 annual rent", "5.50%"),
            ("International Car Wash Group - Huntsville", "1419 Waddell Drive, Huntsville, AL", "$3,435,995", "$214,750 annual rent", "6.25%"),
            ("International Car Wash Group - Hot Springs", "1742 Albert Pike Rd, Hot Springs, AR", "$1,597,505", "$91,857 annual rent", "5.75%"),
            ("International Car Wash Group - Tupelo", "89 W Main St, Tupelo, MS", "$1,154,602", "$63,503 annual rent", "5.50%"),
            ("International Car Wash Group - New Philadelphia", "1100 West High Ave, New Philadelphia, OH", "$3,303,441", "$206,465 annual rent", "6.25%"),
            ("International Car Wash Group - North Randall", "680 Northfield Road, North Randall, OH", "$804,597", "$44,253 annual rent", "5.50%"),
            ("International Car Wash Group - Memphis", "3736 Riverdale Rd, Memphis, TN", "$3,049,140", "$190,571 annual rent", "6.25%"),
            ("International Car Wash Group - Bartlett", "975 Stage Rd, Bartlett, TN", "$3,689,701", "$230,606 annual rent", "6.25%"),
            ("International Car Wash Group - Perrysburg", "7375 Carronade Dr, Perrysburg, OH", "$2,635,595", "$158,136 annual rent", "6.00%"),
            ("International Car Wash Group - Montgomery", "909 Carter Hill Road, Montgomery, AL", "$1,159,645", "$63,780 annual rent", "5.50%"),
        ]
        for name, market, price, rent, cap_rate in sale_leaseback_rows:
            add(
                name=name,
                market=market,
                year="2020",
                asking_price=price,
                sales=rent,
                note=f"20-year NNN sale-leaseback record from the scan. Listed cap rate {cap_rate}; sales field shows annual rent because this is a leaseback table, not operating revenue.",
            )

    return records


def record_rows_from_page(path: Path, page: str, page_number: int) -> list[dict[str, str]]:
    records = []
    row_re = re.compile(
        rf"^\s*(?P<name>[A-Za-z][A-Za-z0-9 &'./-]{{2,42}}?)\s*[\|\[\{{]?\s*"
        rf"(?P<address>\d{{1,6}}\s+.+?\b{STATE_CODE_PATTERN})(?P<rest>.*)$"
    )
    for raw in page.splitlines():
        line = clean_line(raw)
        if len(line) < 18 or not re.search(r"\bcar\s*wash|classy|splash|buckmans|wash boss|personal touch|whistle", line, re.I):
            continue
        match = row_re.match(line)
        if not match:
            continue
        name = professional_title_case(match.group("name").strip(" |[{"))
        if "/" in name or name.lower().startswith("car washes"):
            continue
        address = clean_market(match.group("address"))
        state = state_from_text(address)
        if not address or not state:
            continue
        rest = match.group("rest")
        traffic_match = re.search(r"(\d{1,3}(?:,\d{3})|\d{4,6})\s*[\]\}\|!;1]?\s*(?:Yes|No)?\s*$", rest)
        traffic = traffic_match.group(1) if traffic_match else ""
        note_bits = [f"{name} location in {address}."]
        if traffic:
            note_bits.append(f"Scan row includes market count {traffic}.")
        note_bits.append("Use Maps for current operator/contact review.")
        records.append({
            "id": f"scan-row-{path.stem}-{page_number}-{len(records)}",
            "name": name if "car wash" in name.lower() else f"{name} Car Wash",
            "year": source_year(path),
            "market": address,
            "state": state,
            "asking_price": "",
            "sales": "",
            "ebitda": "",
            "cars_per_year": "Not listed in file",
            "acres": "Not listed in file",
            "note": " ".join(note_bits),
            "wisdom_layer": "Imported location row from scanned paperwork.",
            "decision_layer": "Review this location when the market, operator, or address matches the search.",
            "mistake_layer": "Confirm current operator details before using the record for outreach.",
            "mental_model": "A location row is a lead; contact and market review turn it into a qualified comp.",
            "source": path.name,
            "page": str(page_number),
            "excerpt": line,
            "full_text": line,
            "traffic_count": traffic,
            "verification_status": "Imported file record",
            "public_summary": "",
            "website": "",
            "phone": "",
            "source_urls": "",
        })
    return records


def is_relevant_page(page: str) -> bool:
    lower = page.lower()
    has_wash = any(term in lower for term in ["car wash", "carwash", "auto spa", "wash barn", "suds n soda", "tunnel wash"])
    has_deal_signal = bool(MONEY_RE.search(page) or ADDRESS_RE.search(page) or any(term in lower for term in ["asking", "ebitda", "cash flow", "revenue", "traffic count", "acres", "offering", "investment summary"]))
    demographic_only = any(term in lower for term in [
        "easi census",
        "site selection reports",
        "income household distribution",
        "income families and non-families",
        "demographic overview",
        "total population and households",
        "easy analytic software",
        "easidemographics",
    ])
    if demographic_only and not has_wash:
        return False
    if "m/la code" in lower and "wash name" in lower:
        return False
    if "property name" in lower and "international car wash group" in lower and "address" in lower:
        return False
    if not has_wash and not has_deal_signal:
        return False
    if len(useful_lines(page)) < 3:
        return False
    return True


def record_from_page(path: Path, page_text: str, page_number: int, index: int) -> dict[str, str]:
    page = clean_text(page_text)
    special_fields = special_record_fields(page)
    fallback = "Car Wash Opportunity"
    title = special_fields.get("name") or title_from_page(page, fallback)
    market = special_fields.get("market") or clean_market(market_from_page(page, title))
    state = special_fields.get("state") or state_from_text(market) or state_from_text(page[:1800])
    if (not has_title_term(title)) and market:
        title = f"Car Wash Opportunity - {market}"
    if title == fallback or title.lower().strip(" .:-") in GENERIC_TITLES:
        title = f"Car Wash Opportunity{f' - {location_label(market, state)}' if location_label(market, state) else ''}"
    if is_weak_title(title):
        title = f"Car Wash Opportunity{f' - {location_label(market, state)}' if location_label(market, state) else ''}"
    years = YEAR_RE.findall(page)
    year = years[0] if years else source_year(path)
    financials = extract_labeled_financials(page)
    asking = special_fields.get("asking_price") or financials.get("asking_price") or likely_price(page)
    ebitda = special_fields.get("ebitda") or financials.get("ebitda") or first_match(EBITDA_RE, page)
    sales = special_fields.get("sales") or financials.get("sales") or first_match(SALES_RE, page)
    if sales and money_to_number(sales) < 100_000:
        sales = ""
    if ebitda and money_to_number(ebitda) < 50_000:
        ebitda = ""
    if asking and sales and normalized_money(asking) == normalized_money(sales) and not has_immediate_labeled_value(page, r"sales|revenue|gross revenue|gross operating income|total revenue", sales):
        sales = ""
    if asking and ebitda and normalized_money(asking) == normalized_money(ebitda) and not has_immediate_labeled_value(page, r"ebitda|net income|noi", ebitda):
        ebitda = ""
    if asking and ebitda and normalized_money(asking) == normalized_money(ebitda) and not has_immediate_labeled_value(page, r"asking price|price|purchase price|list price|offered", asking):
        asking = ""
    cars = first_match(CAR_COUNT_RE, page)
    acres = first_match(ACRES_RE, page)
    excerpt = best_excerpt(page)
    note = professional_note(title, market, asking, sales, ebitda, cars, acres, excerpt)

    record = {
        "id": f"ocr-{path.stem}-{page_number}",
        "name": title,
        "year": year,
        "market": market,
        "state": state,
        "asking_price": asking,
        "sales": sales,
        "ebitda": ebitda,
        "cars_per_year": cars,
        "acres": acres,
        "note": note,
        "wisdom_layer": "Imported record from scanned paperwork. Use the full uploaded record text for exact wording and source context.",
        "decision_layer": "Review this record when the search terms, location, price, traffic, or operating details match the question.",
        "mistake_layer": "Scanned files can misread faint text, so confirm important numbers against the searchable PDF before making a decision.",
        "mental_model": "Treat each page as evidence. Search narrows the pile; due diligence confirms the number.",
        "source": path.name,
        "page": str(page_number),
        "excerpt": excerpt,
        "full_text": page,
        "traffic_count": traffic_count_from_text(page),
        "verification_status": "Imported file record",
        "public_summary": "",
        "website": "",
        "phone": special_fields.get("phone", ""),
        "source_urls": "",
    }
    apply_public_research(record)
    record["note"] = professional_note(record["name"], record["market"], record["asking_price"], record["sales"], record["ebitda"], record["cars_per_year"], record["acres"], record["excerpt"])
    return record


def keep_record(record: dict[str, str]) -> bool:
    lower_text = f"{record.get('name', '')} {record.get('market', '')} {record.get('full_text', '')}".lower()
    is_structured = record.get("id", "").startswith("structured-")
    if not is_structured and "confidentiality notice" in lower_text and "available inventory" in lower_text:
        return False
    if not is_structured and "confidentiality agreement - non-disclosure" in lower_text:
        return False
    if re.search(r"\bcontact\b", record.get("market", ""), re.I):
        return False
    if record.get("market", "").strip().upper() in STATE_CODES:
        return False
    if suspicious_market(record.get("market", "")):
        return False
    if re.fullmatch(r"Car Wash Opportunity - [A-Z]{2}", record.get("name", "").strip()):
        return False
    if record.get("name", "").strip() in {"Car Wash Opportunity", "Car Wash Offering Memorandum"} and not record.get("market"):
        return False
    if not record.get("market") and not record.get("state"):
        return False
    if not has_specific_location(record.get("market", "")):
        return False
    if not (record.get("state") or state_from_text(record.get("market", ""))):
        return False
    has_contact = bool(record.get("phone") or record.get("website") or record.get("source_urls") or record.get("external_research") or record.get("public_summary"))
    has_deal_detail = bool(record.get("asking_price") or record.get("sales") or record.get("ebitda") or record.get("cars_per_year") or record.get("acres") or record.get("traffic_count"))
    if not has_contact and not has_deal_detail:
        return False
    if record.get("name", "").strip().lower().startswith("car wash opportunity -") and not ADDRESS_RE.search(record.get("market", "")):
        return False
    if record.get("name", "").strip().lower().startswith("subject:"):
        return False
    if record.get("external_research"):
        return True
    if record.get("market") and record.get("state"):
        return True
    if has_title_term(record.get("name", "")) and (record.get("asking_price") or record.get("sales") or record.get("ebitda") or record.get("cars_per_year") or record.get("acres")):
        return True
    return False


def completeness_score(record: dict[str, str]) -> float:
    score = 0.0
    for key in ["name", "market", "state", "asking_price", "sales", "ebitda", "cars_per_year", "acres", "public_summary"]:
        if record.get(key):
            score += 1
    if money_to_number(record.get("asking_price", "")) >= 100_000:
        score += 2
    if record.get("verification_status") == "Publicly verified":
        score += 4
    if record.get("phone"):
        score += 2
    if record.get("website"):
        score += 2
    if record.get("maps_url") or record.get("latitude"):
        score += 1.5
    if record.get("id", "").startswith("structured-"):
        score += 1
    if has_title_term(record.get("name", "")):
        score += 1
    if is_weak_title(record.get("name", "")):
        score -= 4
    if record.get("name", "").lower().startswith(("car wash lead -", "car wash opportunity -", "car wash location -")):
        score -= 2
    if money_to_number(record.get("asking_price", "")) > 30_000_000 and not re.search(r"portfolio|package", record.get("name", "") + " " + record.get("note", ""), re.I):
        score -= 3
    return score


def merge_records(primary: dict[str, str], secondary: dict[str, str]) -> dict[str, str]:
    merged = dict(primary)
    for key, value in secondary.items():
        if key in {"id", "source", "page"}:
            continue
        if not value:
            continue
        current = merged.get(key, "")
        if not current or str(current).lower().startswith(("not listed", "not provided")):
            merged[key] = value
            continue
        if key in {"note", "public_summary"} and len(str(value)) > len(str(current)) and not is_weak_title(str(value)):
            merged[key] = value
    sources = [primary.get("source", ""), secondary.get("source", "")]
    pages = [primary.get("page", ""), secondary.get("page", "")]
    merged["source"] = " | ".join(dict.fromkeys(source for source in sources if source))
    merged["page"] = " | ".join(dict.fromkeys(page for page in pages if page))
    return merged


def public_coverage_records(existing_records: list[dict[str, str]]) -> list[dict[str, str]]:
    if not PUBLIC_CARWASHES:
        return []

    counts = {code: 0 for code in LOWER_48_STATE_CODES}
    seen_markets = {
        canonical_location_key(record.get("market", ""))
        for record in existing_records
        if record.get("market")
    }
    for record in existing_records:
        state = record.get("state") or state_from_text(record.get("market", ""))
        if state in counts and has_specific_location(record.get("market", "")):
            counts[state] += 1

    def make_public_record(code: str, index: int, item: dict[str, str]) -> dict[str, str] | None:
            market = clean_market(str(item.get("market", "")))
            if not has_specific_location(market):
                return None
            clean_market_key = canonical_location_key(market)
            if not clean_market_key or clean_market_key in seen_markets:
                return None
            seen_markets.add(clean_market_key)
            name = clean_title(str(item.get("name", ""))) or f"Car Wash - {market}"
            return {
                "id": f"public-map-{code}-{index}",
                "name": name,
                "year": "",
                "market": market,
                "state": code,
                "asking_price": "",
                "sales": "",
                "ebitda": estimated_ebitda(item),
                "cars_per_year": "",
                "acres": estimated_acres(item),
                "note": clean_line(str(item.get("note", ""))) or "Public location added for state coverage. EBITDA and acres are screening estimates unless separately listed.",
                "wisdom_layer": "Public location record, not a scanned deal comp.",
                "decision_layer": "Use this as a location lead; verify ownership and financials before underwriting.",
                "mistake_layer": "Do not treat a public map listing as a completed acquisition record.",
                "mental_model": "Public map data supports search coverage; scanned deal data supports valuation judgment.",
                "source": str(item.get("source", "")) or "Public map location layer",
                "page": "",
                "excerpt": "",
                "full_text": "",
                "traffic_count": clean_line(str(item.get("traffic_count", ""))),
                "verification_status": "Public map location",
                "public_summary": clean_line(str(item.get("public_summary", ""))) or f"Public map data lists {name} at {market}.",
                "website": str(item.get("website", "")).strip(),
                "phone": clean_phone(str(item.get("phone", ""))) if item.get("phone") else "",
                "source_urls": str(item.get("source_urls", "")).strip(),
                "maps_url": str(item.get("maps_url", "")).strip(),
                "latitude": str(item.get("latitude", "")).strip(),
                "longitude": str(item.get("longitude", "")).strip(),
            }

    additions: list[dict[str, str]] = []

    for code in sorted(LOWER_48_STATE_CODES):
        for index, item in enumerate(PUBLIC_CARWASHES.get(code, [])):
            if counts.get(code, 0) >= MIN_PUBLIC_RECORDS_PER_STATE:
                break
            record = make_public_record(code, index, item)
            if not record:
                continue
            additions.append(record)
            counts[code] = counts.get(code, 0) + 1

    target_additions = max(0, TARGET_RECORD_COUNT - len(existing_records) - len(additions))
    if target_additions:
        for code in sorted(LOWER_48_STATE_CODES, key=lambda state: counts.get(state, 0)):
            for index, item in enumerate(PUBLIC_CARWASHES.get(code, [])):
                if len(additions) >= target_additions + max(0, TARGET_RECORD_COUNT - len(existing_records) - target_additions):
                    break
                record = make_public_record(code, index, item)
                if not record:
                    continue
                additions.append(record)
                counts[code] = counts.get(code, 0) + 1
                if len(existing_records) + len(additions) >= TARGET_RECORD_COUNT:
                    break
            if len(existing_records) + len(additions) >= TARGET_RECORD_COUNT:
                break
    return additions


def dedupe_records(records: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen_market: dict[str, int] = {}
    for record in records:
        clean_market_key = canonical_location_key(record.get("market", ""))
        if clean_market_key and clean_market_key in seen_market:
            existing_index = seen_market[clean_market_key]
            existing = deduped[existing_index]
            if completeness_score(record) > completeness_score(existing):
                deduped[existing_index] = merge_records(record, existing)
            else:
                deduped[existing_index] = merge_records(existing, record)
            continue
        if clean_market_key:
            seen_market[clean_market_key] = len(deduped)
        deduped.append(record)
    return deduped


def build() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path in sorted(OCR_DIR.glob("*.txt")):
        pages = path.read_text(errors="ignore").split("\f")
        for page_number, page in enumerate(pages, start=1):
            page = clean_text(page)
            if len(page) < 90:
                continue
            right_site_records = right_site_records_from_page(path, page, page_number)
            if right_site_records:
                for right_site_record in right_site_records:
                    if keep_record(right_site_record):
                        records.append(right_site_record)
                continue
            fallback_address_records = secondary_scanned_address_records_from_page(path, page, page_number)
            if fallback_address_records:
                for fallback_address_record in fallback_address_records:
                    if keep_record(fallback_address_record):
                        records.append(fallback_address_record)
            if not is_relevant_page(page):
                continue
            structured_records = structured_records_from_page(path, page, page_number)
            if structured_records:
                for structured in structured_records:
                    if keep_record(structured):
                        records.append(structured)
                continue
            for directory_record in directory_records_from_page(path, page, page_number):
                if keep_record(directory_record):
                    records.append(directory_record)
            for location_record in proximity_location_records_from_page(path, page, page_number):
                if keep_record(location_record):
                    records.append(location_record)
            for address_lead_record in scanned_address_lead_records_from_page(path, page, page_number):
                if keep_record(address_lead_record):
                    records.append(address_lead_record)
            for secondary_address_record in secondary_scanned_address_records_from_page(path, page, page_number):
                if keep_record(secondary_address_record):
                    records.append(secondary_address_record)
            for row_record in record_rows_from_page(path, page, page_number):
                if keep_record(row_record):
                    records.append(row_record)
            record = record_from_page(path, page, page_number, len(records))
            if keep_record(record):
                records.append(record)
    deduped = [
        record
        for record in dedupe_records(records)
        if has_specific_location(record.get("market", ""))
    ]
    deduped.extend(public_coverage_records(deduped))
    final_records = [
        record
        for record in dedupe_records(deduped)
        if has_specific_location(record.get("market", ""))
        and (record.get("state") or state_from_text(record.get("market", ""))) not in EXCLUDED_STATES
        and (record.get("state") or state_from_text(record.get("market", "")))
    ]
    if len(final_records) < TARGET_RECORD_COUNT:
        final_records.extend(public_coverage_records(final_records))
        final_records = [
            record
            for record in dedupe_records(final_records)
            if has_specific_location(record.get("market", ""))
            and (record.get("state") or state_from_text(record.get("market", ""))) not in EXCLUDED_STATES
            and (record.get("state") or state_from_text(record.get("market", "")))
        ]
    for record in final_records:
        record["ebitda"] = estimated_ebitda(record)
        record["acres"] = estimated_acres(record)
        record["sales"] = estimated_sales(record)
        record["cars_per_year"] = estimated_cars_per_year(record)
        record["asking_price"] = estimated_asking_price(record)
        record["traffic_count"] = estimated_traffic_count(record)
        record["note"] = professional_note(
            record["name"],
            record["market"],
            record["asking_price"],
            record["sales"],
            record["ebitda"],
            record["cars_per_year"],
            record["acres"],
            record.get("excerpt", ""),
        )
    return final_records


def main() -> None:
    records = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(records, indent=2)
    OUT.write_text(
        "window.CARWASH_IMPORTED_RECORDS = " + payload + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(records)} records to {OUT}")


if __name__ == "__main__":
    main()
