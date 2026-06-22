#!/usr/bin/env python3
import csv
import io
import json
import math
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

import requests
from requests import RequestException

ROOT = Path(__file__).resolve().parents[1]
RECORDS_PATH = ROOT / "generated" / "carwash_records.js"
CACHE_PATH = ROOT / "cache" / "demographics_cache.json"
ACS_YEAR = "2024"
ACS_POPULATION_CACHE_KEY = f"block_groups_{ACS_YEAR}"

STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09",
    "DE": "10", "DC": "11", "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17",
    "IN": "18", "IA": "19", "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29", "MT": "30", "NE": "31",
    "NV": "32", "NH": "33", "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38",
    "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46",
    "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54",
    "WI": "55", "WY": "56",
}

MILES_TO_METERS = {1: 1609.344, 3: 4828.032, 5: 8046.72}


def load_records():
    text = RECORDS_PATH.read_text()
    payload = text[text.index("[") : text.rindex("]") + 1]
    return json.loads(payload)


def write_records(records):
    payload = json.dumps(records, indent=2)
    RECORDS_PATH.write_text(f"window.CARWASH_IMPORTED_RECORDS = {payload};\n")


def load_cache():
    try:
        return json.loads(CACHE_PATH.read_text())
    except Exception:
        return {"geocode": {}, "rings": {}, "acs": {}}


def save_cache(cache):
    CACHE_PATH.parent.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, sort_keys=True))


def clean_number(value):
    digits = re.sub(r"[^\d]", "", str(value or ""))
    return f"{int(digits):,}" if digits else ""


def scanned_population(record):
    text = str(record.get("full_text") or "")
    patterns = [
        r"(?:DEMOGRAPHIC OVERVIEW\s*)?Population\s+(\d[\d,]*)\s+(\d[\d,]*)\s+(\d[\d,]*)",
        r"Population\s*\(4/1/2010\)\s+(\d[\d,]*)\s+(\d[\d,]*)\s+(\d[\d,]*)",
        r"Total population[^0-9]{0,90}(\d[\d,]*)\s+(\d[\d,]*)\s+(\d[\d,]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            one, three, five = [clean_number(part) for part in match.groups()]
            if one and three and five:
                return {
                    "population_1_mile": one,
                    "population_3_mile": three,
                    "population_5_mile": five,
                    "demographics_source": "Scanned EASI/The Right Site demographic support page",
                }
    return {}


def address_for(record):
    address = str(record.get("market") or "").strip()
    return re.sub(r"\s+", " ", address)


def geocode_batch(records, cache):
    pending = []
    for record in records:
        address = address_for(record)
        if not address or address in cache["geocode"]:
            continue
        pending.append((record["id"], address))

    if not pending:
        return

    url = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
    for offset in range(0, len(pending), 500):
        chunk = pending[offset : offset + 500]
        id_to_address = {record_id: address for record_id, address in chunk}
        body = io.StringIO()
        writer = csv.writer(body)
        for record_id, address in chunk:
            writer.writerow([record_id, address, "", "", ""])
        files = {"addressFile": ("addresses.csv", body.getvalue(), "text/csv")}
        data = {"benchmark": "Public_AR_Current"}
        response = requests.post(url, files=files, data=data, timeout=60)
        response.raise_for_status()
        for row in csv.reader(io.StringIO(response.text)):
            if len(row) < 6:
                continue
            record_id, input_address, match_status = row[0], row[1], row[2]
            coord = row[5] if len(row) > 5 else ""
            key = id_to_address.get(record_id) or re.sub(r",\s*,\s*,\s*$", "", input_address.strip())
            key = re.sub(r"\s+", " ", key.strip())
            if "Match" in match_status and "," in coord:
                try:
                    lon, lat = [float(part) for part in coord.split(",", 1)]
                    cache["geocode"][key] = {"lat": lat, "lon": lon, "id": record_id}
                except ValueError:
                    cache["geocode"][key] = None
            else:
                cache["geocode"][key] = None
        save_cache(cache)
        time.sleep(0.25)


def get_population_map(cache):
    if ACS_POPULATION_CACHE_KEY in cache["acs"]:
        return cache["acs"][ACS_POPULATION_CACHE_KEY]
    url = f"https://www2.census.gov/programs-surveys/acs/summary_file/{ACS_YEAR}/table-based-SF/data/5YRData/acsdt5y{ACS_YEAR}-b01003.dat"
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    out = {}
    for line in response.text.splitlines()[1:]:
      parts = line.split("|")
      if len(parts) < 2:
          continue
      geoid, pop = parts[0], parts[1]
      if not geoid.startswith("1500000US"):
          continue
      try:
          out[geoid.replace("1500000US", "", 1)] = int(pop)
      except ValueError:
          pass
    cache["acs"][ACS_POPULATION_CACHE_KEY] = out
    save_cache(cache)
    return out


def block_groups_near(lat, lon, miles, cache):
    ring_key = f"{ACS_YEAR}:{lat:.6f},{lon:.6f}:{miles}"
    if ring_key in cache["rings"]:
        return cache["rings"][ring_key]
    params = {
        "f": "json",
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": str(MILES_TO_METERS[miles]),
        "units": "esriSRUnit_Meter",
        "outFields": "GEOID",
        "returnGeometry": "false",
    }
    url = f"https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS{ACS_YEAR}/MapServer/10/query"
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=90)
            response.raise_for_status()
            break
        except RequestException:
            if attempt == 2:
                cache["rings"][ring_key] = []
                save_cache(cache)
                return []
            time.sleep(1.5 * (attempt + 1))
    features = response.json().get("features") or []
    geoids = sorted({str(feature.get("attributes", {}).get("GEOID") or "") for feature in features if feature.get("attributes")})
    geoids = [geoid for geoid in geoids if geoid]
    cache["rings"][ring_key] = geoids
    save_cache(cache)
    time.sleep(0.08)
    return geoids


def estimate_ring_populations(record, cache):
    address = address_for(record)
    geo = cache["geocode"].get(address)
    if not geo:
        return {}
    population_by_bg = get_population_map(cache)
    if not population_by_bg:
        return {}
    values = {}
    for miles in (1, 3, 5):
        geoids = block_groups_near(geo["lat"], geo["lon"], miles, cache)
        total = sum(population_by_bg.get(geoid, 0) for geoid in geoids)
        if total:
            values[f"population_{miles}_mile"] = f"{int(total):,}"
    if values:
        values["demographics_source"] = f"Estimated from Census ACS {ACS_YEAR} block groups within radius"
    return values


def int_value(value):
    digits = re.sub(r"[^\d]", "", str(value or ""))
    return int(digits) if digits else 0


def median(values):
    clean = sorted(value for value in values if value)
    if not clean:
        return 0
    mid = len(clean) // 2
    return clean[mid] if len(clean) % 2 else round((clean[mid - 1] + clean[mid]) / 2)


def fill_modeled_fallbacks(records):
    by_state = {}
    national = {1: [], 3: [], 5: []}
    for record in records:
        state = str(record.get("state") or "").upper()
        if not state:
            continue
        by_state.setdefault(state, {1: [], 3: [], 5: []})
        for miles in (1, 3, 5):
            value = int_value(record.get(f"population_{miles}_mile"))
            if value:
                by_state[state][miles].append(value)
                national[miles].append(value)

    national_medians = {miles: median(values) for miles, values in national.items()}
    filled = 0
    for record in records:
        if record.get("population_1_mile") and record.get("population_3_mile") and record.get("population_5_mile"):
            continue
        state = str(record.get("state") or "").upper()
        state_values = by_state.get(state) or {}
        for miles in (1, 3, 5):
            value = median(state_values.get(miles, [])) or national_medians[miles]
            record[f"population_{miles}_mile"] = f"{int(value):,}" if value else "Not available"
        record["demographics_source"] = "Modeled state fallback from available Scout Census/TIGER records; verify with a demographic report"
        filled += 1
    return filled


def main(limit=None):
    records = load_records()
    cache = load_cache()
    scanned_fallback = 0
    estimated = 0
    unchanged = 0

    for record in records:
        source = str(record.get("demographics_source") or "")
        has_all = record.get("population_1_mile") and record.get("population_3_mile") and record.get("population_5_mile")
        if has_all and f"ACS {ACS_YEAR}" in source:
            continue
        for key in ["population_1_mile", "population_3_mile", "population_5_mile", "demographics_source"]:
            record.pop(key, None)

    geocode_batch(records, cache)

    processed = 0
    for record in records:
        source = str(record.get("demographics_source") or "")
        if record.get("population_1_mile") and record.get("population_3_mile") and record.get("population_5_mile") and f"ACS {ACS_YEAR}" in source:
            estimated += 1
            continue
        if record.get("population_1_mile") and record.get("population_3_mile") and record.get("population_5_mile") and source.startswith("Scanned EASI"):
            scanned_fallback += 1
            continue
        if record.get("population_1_mile") and record.get("population_3_mile") and record.get("population_5_mile") and source.startswith("Modeled state fallback"):
            continue
        if limit and processed >= limit:
            break
        values = estimate_ring_populations(record, cache)
        if values:
            record.update(values)
            estimated += 1
        else:
            scanned_values = scanned_population(record)
            if scanned_values:
                record.update(scanned_values)
                scanned_fallback += 1
            else:
                unchanged += 1
        processed += 1
        if processed % 25 == 0:
            write_records(records)
            print(f"processed {processed}, estimated {estimated}, scanned_fallback {scanned_fallback}, unchanged {unchanged}", flush=True)

    fallback = 0 if limit else fill_modeled_fallbacks(records)
    write_records(records)
    save_cache(cache)
    filled = sum(1 for r in records if r.get("population_1_mile") and r.get("population_3_mile") and r.get("population_5_mile"))
    print(json.dumps({"records": len(records), "filled": filled, "acs_year": ACS_YEAR, "estimated": estimated, "scanned_fallback": scanned_fallback, "modeled_fallback": fallback, "unchanged": unchanged}, indent=2))


if __name__ == "__main__":
    limit_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(limit_arg)
