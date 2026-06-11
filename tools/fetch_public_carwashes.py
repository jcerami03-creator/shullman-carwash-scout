from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path


ROOT = Path("/Users/josephcerami/Documents/LLM For Shullman Paperwork")
OUT = ROOT / "data" / "public_carwashes.json"
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

STATE_CODES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}


def query_state(code: str) -> dict:
    query = (
        f'[out:json][timeout:25];'
        f'nwr["amenity"="car_wash"]["addr:state"="{code}"];'
        f'out tags center 40;'
    )
    last_error = ""
    for endpoint in ENDPOINTS:
        try:
            result = subprocess.run(
                ["curl", "-sS", "-X", "POST", endpoint, "--data", f"data={query}"],
                check=True,
                capture_output=True,
                text=True,
                timeout=45,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            last_error = str(exc)
            time.sleep(1.5)
            continue
        if result.stdout.lstrip().startswith("{"):
            return json.loads(result.stdout)
        last_error = result.stdout[:2000]
        time.sleep(1.5)
    raise RuntimeError(last_error)


def value(tags: dict, *keys: str) -> str:
    for key in keys:
        if tags.get(key):
            return str(tags[key]).strip()
    return ""


def clean_phone(phone: str) -> str:
    phone = phone.strip()
    digits = "".join(char for char in phone if char.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone


def record_from_element(code: str, element: dict) -> dict | None:
    tags = element.get("tags", {})
    lat = element.get("lat") or element.get("center", {}).get("lat")
    lon = element.get("lon") or element.get("center", {}).get("lon")
    if lat is None or lon is None:
        return None

    house = value(tags, "addr:housenumber")
    street = value(tags, "addr:street")
    city = value(tags, "addr:city", "addr:place")
    postcode = value(tags, "addr:postcode")
    state = value(tags, "addr:state") or code

    if not street or not city:
        return None

    address = f"{house} {street}".strip() if house else street
    market = f"{address}, {city}, {state}"
    if postcode:
        market += f" {postcode}"

    name = value(tags, "name", "brand", "operator") or f"Car Wash - {city}"
    website = value(tags, "website", "contact:website")
    phone = clean_phone(value(tags, "phone", "contact:phone"))
    maps_query = f"{lat},{lon}"

    return {
        "name": name,
        "year": "",
        "market": market,
        "state": code,
        "asking_price": "",
        "sales": "",
        "ebitda": "",
        "cars_per_year": "",
        "acres": "",
        "note": f"Public map location in {STATE_NAMES[code]}. Added to make the Scout useful for location discovery even when scanned paperwork has no deal record for this area.",
        "wisdom_layer": "Public location record, not a scanned deal comp.",
        "decision_layer": "Use this to identify local car wash options and then verify ownership, traffic, and financials separately.",
        "mistake_layer": "Do not treat a public location as an acquisition comp without deal data.",
        "mental_model": "Public map data broadens coverage; scanned deal data supports underwriting.",
        "source": "OpenStreetMap public car wash layer",
        "page": "",
        "excerpt": "",
        "full_text": "",
        "traffic_count": "",
        "verification_status": "Public map location",
        "public_summary": f"Public map data lists {name} at {market}.",
        "website": website,
        "phone": phone,
        "source_urls": "https://www.openstreetmap.org/copyright",
        "maps_url": f"https://www.google.com/maps/search/?api=1&query={maps_query}",
        "latitude": str(lat),
        "longitude": str(lon),
    }


def main() -> None:
    by_state: dict[str, list[dict]] = {}
    for index, code in enumerate(STATE_CODES, start=1):
        print(f"{index:02d}/50 {code}", flush=True)
        try:
            payload = query_state(code)
        except RuntimeError as exc:
            print(f"  skipped {code}: {exc}", flush=True)
            by_state[code] = []
            continue
        records: list[dict] = []
        seen: set[str] = set()
        for element in payload.get("elements", []):
            record = record_from_element(code, element)
            if not record:
                continue
            key = "".join(ch for ch in record["market"].lower() if ch.isalnum())
            if key in seen:
                continue
            seen.add(key)
            records.append(record)
            if len(records) >= 12:
                break
        by_state[code] = records
        time.sleep(0.35)

    OUT.write_text(json.dumps(by_state, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {sum(len(v) for v in by_state.values())} public records to {OUT}")


if __name__ == "__main__":
    main()
