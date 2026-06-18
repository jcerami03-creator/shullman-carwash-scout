#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests

ROOT = Path("/Users/josephcerami/Documents/LLM For Shullman Paperwork")
OUT = ROOT / "data" / "public_carwashes.json"
USER_AGENT = "ShullmanCarwashScout/1.0"

STATE_CITIES = {
    "AL": ["Birmingham", "Montgomery", "Huntsville", "Mobile", "Tuscaloosa"],
    "AZ": ["Phoenix", "Tucson", "Mesa", "Scottsdale", "Glendale"],
    "AR": ["Little Rock", "Fort Smith", "Fayetteville", "Springdale", "Jonesboro"],
    "CA": ["Los Angeles", "San Diego", "San Jose", "Fresno", "Sacramento", "Long Beach", "Bakersfield", "Oakland", "Anaheim", "Riverside"],
    "CO": ["Denver", "Colorado Springs", "Aurora", "Fort Collins", "Lakewood"],
    "CT": ["Bridgeport", "New Haven", "Stamford", "Hartford", "Waterbury"],
    "DE": ["Wilmington", "Dover", "Newark", "Middletown", "Smyrna"],
    "FL": ["Miami", "Orlando", "Tampa", "Jacksonville", "Fort Lauderdale", "St Petersburg", "Sarasota", "Naples"],
    "GA": ["Atlanta", "Augusta", "Columbus", "Savannah", "Macon"],
    "ID": ["Boise", "Meridian", "Nampa", "Idaho Falls", "Pocatello"],
    "IL": ["Chicago", "Aurora", "Naperville", "Joliet", "Rockford", "Springfield"],
    "IN": ["Indianapolis", "Fort Wayne", "Evansville", "South Bend", "Carmel"],
    "IA": ["Des Moines", "Cedar Rapids", "Davenport", "Sioux City", "Iowa City"],
    "KS": ["Wichita", "Overland Park", "Kansas City", "Olathe", "Topeka"],
    "KY": ["Louisville", "Lexington", "Bowling Green", "Owensboro", "Covington"],
    "LA": ["New Orleans", "Baton Rouge", "Shreveport", "Lafayette", "Lake Charles"],
    "ME": ["Portland", "Lewiston", "Bangor", "South Portland", "Auburn"],
    "MD": ["Baltimore", "Frederick", "Rockville", "Gaithersburg", "Bowie"],
    "MA": ["Boston", "Worcester", "Springfield", "Lowell", "Cambridge"],
    "MI": ["Detroit", "Grand Rapids", "Warren", "Sterling Heights", "Lansing", "Ann Arbor"],
    "MN": ["Minneapolis", "Saint Paul", "Rochester", "Duluth", "Bloomington"],
    "MS": ["Jackson", "Gulfport", "Southaven", "Biloxi", "Hattiesburg"],
    "MO": ["Kansas City", "St Louis", "Springfield", "Columbia", "Independence"],
    "MT": ["Billings", "Missoula", "Great Falls", "Bozeman", "Butte"],
    "NE": ["Omaha", "Lincoln", "Bellevue", "Grand Island", "Kearney"],
    "NV": ["Las Vegas", "Henderson", "Reno", "North Las Vegas", "Sparks"],
    "NH": ["Manchester", "Nashua", "Concord", "Dover", "Rochester"],
    "NJ": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Edison", "Toms River"],
    "NM": ["Albuquerque", "Las Cruces", "Rio Rancho", "Santa Fe", "Roswell"],
    "NY": ["New York", "Buffalo", "Rochester", "Yonkers", "Syracuse", "Albany"],
    "NC": ["Charlotte", "Raleigh", "Greensboro", "Durham", "Winston-Salem"],
    "ND": ["Fargo", "Bismarck", "Grand Forks", "Minot", "West Fargo"],
    "OH": ["Columbus", "Cleveland", "Cincinnati", "Toledo", "Akron", "Dayton"],
    "OK": ["Oklahoma City", "Tulsa", "Norman", "Broken Arrow", "Edmond"],
    "OR": ["Portland", "Eugene", "Salem", "Gresham", "Bend"],
    "PA": ["Philadelphia", "Pittsburgh", "Allentown", "Erie", "Scranton", "Harrisburg"],
    "RI": ["Providence", "Warwick", "Cranston", "Pawtucket", "East Providence"],
    "SC": ["Charleston", "Columbia", "North Charleston", "Greenville", "Myrtle Beach"],
    "SD": ["Sioux Falls", "Rapid City", "Aberdeen", "Brookings", "Watertown"],
    "TN": ["Nashville", "Memphis", "Knoxville", "Chattanooga", "Murfreesboro"],
    "TX": ["Houston", "San Antonio", "Dallas", "Austin", "Fort Worth", "El Paso", "Arlington", "Plano"],
    "UT": ["Salt Lake City", "West Valley City", "Provo", "West Jordan", "Sandy"],
    "VT": ["Burlington", "South Burlington", "Rutland", "Barre", "Montpelier"],
    "VA": ["Virginia Beach", "Norfolk", "Chesapeake", "Richmond", "Arlington", "Alexandria"],
    "WA": ["Seattle", "Spokane", "Tacoma", "Vancouver", "Bellevue"],
    "WV": ["Charleston", "Huntington", "Morgantown", "Parkersburg", "Wheeling"],
    "WI": ["Milwaukee", "Madison", "Green Bay", "Kenosha", "Racine"],
    "WY": ["Cheyenne", "Casper", "Laramie", "Gillette", "Rock Springs"],
}


def clean_phone(phone: str) -> str:
    digits = "".join(char for char in str(phone) if char.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return str(phone or "").strip()


def key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def city_from_address(address: dict) -> str:
    for field in ["city", "town", "village", "municipality", "suburb", "county"]:
        if address.get(field):
            return str(address[field])
    return ""


def state_code(address: dict, fallback: str) -> str:
    value = str(address.get("ISO3166-2-lvl4") or "")
    if value.startswith("US-"):
        return value.split("-", 1)[1]
    return fallback


def item_to_record(item: dict, fallback_state: str) -> dict | None:
    if item.get("category") != "amenity" or item.get("type") != "car_wash":
        return None
    address = item.get("address") or {}
    house = str(address.get("house_number") or "").strip()
    road = str(address.get("road") or "").strip()
    city = city_from_address(address)
    state = state_code(address, fallback_state)
    postcode = str(address.get("postcode") or "").strip()
    if not house or not road or not city or state != fallback_state:
        return None
    street = f"{house} {road}"
    market = f"{street}, {city}, {state}"
    if postcode:
        market += f" {postcode}"
    name = str(item.get("name") or "").strip() or f"Car Wash - {city}"
    extra = item.get("extratags") or {}
    website = str(extra.get("website") or extra.get("contact:website") or "").strip()
    phone = clean_phone(extra.get("phone") or extra.get("contact:phone") or "")
    lat, lon = str(item.get("lat") or "").strip(), str(item.get("lon") or "").strip()
    return {
        "name": name,
        "year": "",
        "market": market,
        "state": state,
        "asking_price": "",
        "sales": "",
        "ebitda": "",
        "cars_per_year": "",
        "acres": "",
        "note": "Public OpenStreetMap location added for professional market coverage. Verify ownership and financials before underwriting.",
        "wisdom_layer": "Public location record, not a scanned deal comp.",
        "decision_layer": "Use this as a location lead; verify ownership and financials before underwriting.",
        "mistake_layer": "Do not treat a public map listing as a completed acquisition record.",
        "mental_model": "Public map data supports search coverage; scanned deal data supports valuation judgment.",
        "source": "OpenStreetMap Nominatim public car wash layer",
        "page": "",
        "excerpt": "",
        "full_text": "",
        "traffic_count": "",
        "verification_status": "Public map location",
        "public_summary": f"Public OpenStreetMap data lists {name} at {market}.",
        "website": website,
        "phone": phone,
        "source_urls": "https://www.openstreetmap.org/copyright",
        "maps_url": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else "",
        "latitude": lat,
        "longitude": lon,
    }


def search(query: str) -> list[dict]:
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "jsonv2", "addressdetails": 1, "extratags": 1, "limit": 50, "countrycodes": "us"},
        headers={"User-Agent": USER_AGENT},
        timeout=25,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    by_state = json.loads(OUT.read_text()) if OUT.exists() else {}
    existing = {key(record.get("market", "")) for records in by_state.values() for record in records}
    added = 0
    for state, cities in STATE_CITIES.items():
        by_state.setdefault(state, [])
        for city in cities:
            if len(by_state[state]) >= 35:
                break
            for item in search(f"car wash {city} {state}"):
                record = item_to_record(item, state)
                if not record:
                    continue
                market_key = key(record["market"])
                if market_key in existing:
                    continue
                existing.add(market_key)
                by_state[state].append(record)
                added += 1
                if len(by_state[state]) >= 35:
                    break
            time.sleep(1.0)
        print(f"{state}: {len(by_state[state])} records", flush=True)
    OUT.write_text(json.dumps(by_state, indent=2) + "\n")
    print(f"Added {added} public city records; total public records {sum(len(v) for v in by_state.values())}")


if __name__ == "__main__":
    main()
