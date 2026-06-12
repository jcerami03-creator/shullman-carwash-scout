from __future__ import annotations

import collections
import json
import re
from pathlib import Path


ROOT = Path("/Users/josephcerami/Documents/LLM For Shullman Paperwork")
DATA_PATH = ROOT / "generated" / "carwash_records.js"

BAD_VISIBLE_TERMS = [
    "right site census",
    "pnet",
    "roule",
    "commercialone",
    "entrance tax",
    "print all",
    "all properties",
    "ocr location",
    "scanned car wash lead",
    "holabird",
    "billion sq",
    "million sq",
    "auto repair",
    "loopnet confirms",
]


def load_records() -> list[dict[str, object]]:
    text = DATA_PATH.read_text(encoding="utf-8")
    payload = text[text.index("[") : text.rindex("]") + 1]
    return json.loads(payload)


def normalized_address(value: object) -> str:
    text = str(value or "").lower()
    state_match = re.findall(r"\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)\b", str(value or ""))
    state = state_match[-1].lower() if state_match else ""
    address_match = re.search(
        r"\b\d{1,6}(?:-\d{1,6})?\s+[A-Za-z0-9][A-Za-z0-9 .'/#-]{1,70}?\s+(?:Street|St|Road|Rd|Avenue|Ave|Highway|Hwy|Pike|Lane|Ln|Drive|Dr|Boulevard|Blvd|Court|Ct|Way|Parkway|Pkwy|Circle|Cir|Trail|Terrace|Place|Pl|Route|Rt|Expressway|Expy|Square|Sq)\b",
        str(value or ""),
        re.I,
    )
    if address_match:
        text = f"{address_match.group(0)} {state}".lower()
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
        "terrace": "ter",
        "place": "pl",
    }
    for long, short in replacements.items():
        text = re.sub(rf"\b{long}\b", short, text)
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def has_map_ready_address(value: object) -> bool:
    text = str(value or "")
    return bool(re.search(r"\b\d{1,6}(?:-\d{1,6})?\s+[A-Za-z0-9]", text)) and bool(
        re.search(r"\b[A-Z]{2}(?:\s+\d{5})?\b", text)
    )


def money_value(value: object) -> float:
    raw = str(value or "").lower()
    match = re.search(r"\d+(?:\.\d+)?", raw.replace("$", "").replace(",", ""))
    if not match:
        return 0
    number = float(match.group())
    if "million" in raw or re.search(r"\d(?:\.\d+)?\s*m\b", raw):
        number *= 1_000_000
    elif re.search(r"\d(?:\.\d+)?\s*k\b", raw):
        number *= 1_000
    return number


def visible_text(record: dict[str, object]) -> str:
    keys = [
        "name",
        "market",
        "asking_price",
        "sales",
        "ebitda",
        "cars_per_year",
        "acres",
        "note",
        "public_summary",
        "traffic_count",
    ]
    return " ".join(str(record.get(key, "")) for key in keys)


def audit() -> dict[str, object]:
    records = load_records()
    address_counts = collections.Counter(normalized_address(record.get("market")) for record in records)
    state_counts = collections.Counter(str(record.get("state", "")) for record in records)
    flags: collections.Counter[str] = collections.Counter()
    examples: list[dict[str, object]] = []

    for index, record in enumerate(records):
        record_flags: list[str] = []
        if address_counts[normalized_address(record.get("market"))] > 1:
            record_flags.append("duplicate-address")
        if not has_map_ready_address(record.get("market")):
            record_flags.append("no-map-ready-address")
        if any(term in visible_text(record).lower() for term in BAD_VISIBLE_TERMS):
            record_flags.append("bad-visible-text")
        if not money_value(record.get("asking_price")):
            record_flags.append("no-asking")
        if not money_value(record.get("sales")):
            record_flags.append("no-sales")
        if not money_value(record.get("ebitda")):
            record_flags.append("no-ebitda")
        if not re.search(r"\d", str(record.get("acres", ""))):
            record_flags.append("no-acres")
        if not re.search(r"\d", str(record.get("cars_per_year", ""))):
            record_flags.append("no-cars")
        if not re.search(r"\d", str(record.get("traffic_count", ""))):
            record_flags.append("no-traffic")

        flags.update(record_flags)
        if record_flags and len(examples) < 20:
            examples.append(
                {
                    "index": index,
                    "id": record.get("id"),
                    "name": record.get("name"),
                    "market": record.get("market"),
                    "flags": record_flags,
                }
            )

    return {
        "total": len(records),
        "states": len([state for state in state_counts if state]),
        "min_state_count": min(state_counts.values()) if state_counts else 0,
        "duplicate_address_groups": sum(1 for count in address_counts.values() if count > 1),
        "duplicate_records": sum(count for count in address_counts.values() if count > 1),
        "flags": dict(flags),
        "examples": examples,
    }


def main() -> None:
    print(json.dumps(audit(), indent=2))


if __name__ == "__main__":
    main()
