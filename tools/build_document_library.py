from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = Path("/Users/josephcerami/PDF FOR CAR WASH SCOUt")
OCR_DIR = ROOT / "ocr-output"
DOC_DIR = ROOT / "documents"
GALLERY_DIR = DOC_DIR / "gallery"
OUT = ROOT / "generated" / "document_library.js"

KEY_TERMS = re.compile(
    r"\b(?:car wash|carwash|traffic counts?|ebitda|revenue|current site list|development sites|asking price|purchase price|acres|vacuum spaces|site selection)\b",
    re.I,
)
CITY_STATE_RE = re.compile(
    r"\b([A-Z][A-Za-z .'-]+,\s*(?:AL|AR|AZ|CA|CO|CT|DE|FL|GA|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)(?:\s+\d{5})?)\b"
)
CITY_STATE_SIMPLE_RE = re.compile(
    r"\b([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){0,3},\s*(?:AL|AR|AZ|CA|CO|CT|DE|FL|GA|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)(?:\s+\d{5})?)\b"
)
ADDRESS_RE = re.compile(
    r"\b\d{1,6}(?:-\d{1,6})?\s+[A-Z][A-Za-z0-9'.-]*(?:\s+[A-Za-z0-9'.#&/-]+){1,8},?\s+[A-Z][A-Za-z .'-]+,?\s+(?:AL|AR|AZ|CA|CO|CT|DE|FL|GA|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)\b(?:\s+\d{5})?",
    re.I,
)
TRAFFIC_RE = re.compile(
    r"\b(?:traffic\s+count|traffic\s+volume|average\s+daily\s+traffic|AADT|ADT|VPD)\D{0,50}(\d{1,3}(?:,\d{3})+|\d{4,6})\b"
    r"|\b(\d{1,3}(?:,\d{3})+|\d{4,6})\s*(?:VPD|AADT|ADT|vehicles\s+per\s+day|daily\s+traffic)\b",
    re.I,
)
EBITDA_RE = re.compile(r"\bEBITDA\b[^$\d]*(\$\s?\d[\d,]*(?:\.\d+)?\s?(?:m|k|million)?)", re.I)
REVENUE_RE = re.compile(r"\b(?:sales|revenue|gross operating income|total revenue)\b[^$\d]*(\$\s?\d[\d,]*(?:\.\d+)?\s?(?:m|k|million)?)", re.I)
PRICE_RE = re.compile(r"\b(?:asking price|price|purchase price)\b[^$\d]*(\$\s?\d[\d,]*(?:\.\d+)?\s?(?:m|k|million)?)", re.I)
BAD_TITLE_BITS = re.compile(
    r"\b(?:page \d+|biz search|listings by email|buyer's workbook|sales comps|property records|add listing|back to search|"
    r"contact listing broker|request additional information|http|www\.|google map|yahoo map|all rights reserved|"
    r"terms and conditions|financial information cont|general financial information|profit centers include|"
    r"capture rate|standard in the car wash industry|car wash sector|brokers harmless|source of all updated estimates)\b",
    re.I,
)
STREET_WORD_RE = re.compile(r"\b(?:street|st|road|rd|avenue|ave|highway|hwy|pike|lane|ln|drive|dr|boulevard|blvd|court|ct|way|parkway|pkwy|circle|cir|trail|terrace|place|pl|route|rt|us-|i-)\b", re.I)
BAD_ADDRESS_BITS = re.compile(r"\b(?:cars|detailing|building and equipment|mile from|miles of the site|of \d+|page|bizbuysell|loopnet|google|yahoo|copyright|reserved)\b", re.I)
BAD_LOCATION_BITS = re.compile(r"\b(?:miles?|site|criteria|representative|car wash|businesses|profit|income|spa, VA|clinic|source|updated estimates)\b", re.I)

IMAGE_SCAN_PAGE_GROUPS = {
    "Images Scanned": {
        "Wash Menu & Service Pricing": {13, 22, 52},
        "Fuel & Promo Signage": {40},
        "Roadside Signs & Branding": {11, 12, 15, 21, 25, 26, 33, 34, 37, 46, 55, 57, 58},
        "Site Exterior & Building": {1, 4, 5, 9, 14, 16, 17, 19, 20, 23, 24, 27, 28, 29, 30, 31, 32, 35, 36, 39, 45, 48, 51, 62},
        "Street Frontage & Access Views": {2, 3, 7, 8, 10, 18, 38, 47, 53, 54, 56, 59, 60, 61},
        "Interior, Tunnel & Equipment": {6, 41, 42, 43, 44, 49, 50},
    }
}

IMAGE_SCAN_INTERPRETATIONS = {
    "Wash Menu & Service Pricing": "Pages with visible wash package boards or service-price signage.",
    "Fuel & Promo Signage": "Fuel price boards, promotional signs, and non-wash price signage near the site.",
    "Roadside Signs & Branding": "Pylon signs, brand signs, directional signs, and customer-facing exterior signage.",
    "Site Exterior & Building": "Building, bay, lot, canopy, and exterior site condition views.",
    "Street Frontage & Access Views": "Drive-by, roadway, frontage, ingress/egress, and visibility views.",
    "Interior, Tunnel & Equipment": "Interior bay, tunnel, wash equipment, utility, and operating-condition photos.",
}


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def readable_line(value: str) -> bool:
    line = clean(value)
    if len(line) < 12:
        return False
    letters = sum(ch.isalpha() for ch in line)
    numbers = sum(ch.isdigit() for ch in line)
    useful = letters + numbers
    if useful < 8:
        return False
    if useful / max(len(line), 1) < 0.42:
        return False
    if re.search(r"(?:\b[A-Z]\b[\s|,.-]*){5,}", line):
        return False
    if re.search(r"(?:V\s*){6,}|(?:I\s*){6,}|(?:[^\w\s]\s*){8,}", line, re.I):
        return False
    return True


def short_text(value: str, max_chars: int = 86) -> str:
    value = clean(value)
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip(" ,.;:-") + "..."


def first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    for group in match.groups():
        if group:
            return clean(group)
    return clean(match.group(0))


def valid_address(value: str) -> bool:
    value = clean(value)
    if not value or BAD_ADDRESS_BITS.search(value):
        return False
    if not STREET_WORD_RE.search(value):
        return False
    letters = sum(ch.isalpha() for ch in value)
    digits = sum(ch.isdigit() for ch in value)
    return letters >= 6 and digits >= 1


def valid_addresses_from(text: str) -> list[str]:
    addresses = []
    for match in ADDRESS_RE.finditer(text):
        address = clean(match.group(0))
        if valid_address(address):
            addresses.append(address)
    return list(dict.fromkeys(addresses))


def best_city_state(text: str) -> str:
    for pattern in (CITY_STATE_SIMPLE_RE, CITY_STATE_RE):
        for match in pattern.finditer(text):
            location = clean(match.group(1))
            if len(location) <= 45 and not BAD_LOCATION_BITS.search(location):
                return location
    return ""


def money_value(value: str) -> float:
    text = clean(value).lower().replace("$", "").replace(",", "")
    multiplier = 1.0
    if text.endswith("million"):
        multiplier = 1_000_000.0
        text = text.replace("million", "")
    elif text.endswith("m"):
        multiplier = 1_000_000.0
        text = text[:-1]
    elif text.endswith("k"):
        multiplier = 1_000.0
        text = text[:-1]
    match = re.search(r"\d+(?:\.\d+)?", text)
    return float(match.group(0)) * multiplier if match else 0.0


def best_document_title(lines: list[str], location: str, source: str, page_number: int) -> str:
    for line in lines[:22]:
        if BAD_TITLE_BITS.search(line):
            continue
        if location and (line.count("|") >= 2 or len(re.findall(r"\d", line)) > 18):
            continue
        if re.search(r"\b(?:car wash|carwash|auto spa|wash barn|suds n soda|gas station|express wash|site location|offering memorandum|investment summary)\b", line, re.I):
            return short_text(line)
    for line in lines[:18]:
        if BAD_TITLE_BITS.search(line):
            continue
        if location and (line.count("|") >= 2 or len(re.findall(r"\d", line)) > 18):
            continue
        if readable_line(line) and not re.match(r"^[\d\s$.,:/-]+$", line):
            return short_text(line)
    if location:
        return short_text(f"Evidence - {location}")
    return f"Evidence page {page_number}"


def professional_title(value: str) -> bool:
    value = clean(value)
    if not value or BAD_TITLE_BITS.search(value):
        return False
    if len(value) < 6 or len(value) > 92:
        return False
    if value[:1].islower():
        return False
    if re.search(r"[{}[\]<>~`]{1,}|[‘’]{2,}", value):
        return False
    if len(re.findall(r"\d", value)) > 18:
        return False
    if value.count("|") >= 2:
        return False
    if re.search(r"\b(?:this|that|the property|the location|industry|customer|consumer|brokers)\b", value, re.I) and not re.search(r"\b(?:car wash|auto spa|gas station|site location|investment summary|offering memorandum|listing)\b", value, re.I):
        return False
    return True


def infer_evidence_type(text: str) -> str:
    value = clean(text).lower()
    if "current site list" in value or "current portfolio" in value:
        return "Current Portfolio Site"
    if "development site" in value or "in construction" in value or "pre-construction" in value:
        return "Development Site"
    if "right site" in value or "site selection" in value or "census" in value or "demographic" in value:
        return "Demographic Support"
    if "profit & loss" in value or "financial analysis" in value or "rent roll" in value:
        return "Financial Support"
    if "for sale" in value or "asking price" in value or "purchase price" in value or "loopnet" in value or "bizbuysell" in value:
        return "Listing / Offering"
    if "traffic" in value or "vpd" in value or "aadt" in value:
        return "Traffic / Site Evidence"
    return "Source Evidence"


def generic_evidence_row(text: str, source: str, page_number: int, summary: str, addresses: list[str]) -> dict[str, str] | None:
    lines = [clean(line) for line in text.splitlines() if readable_line(line)]
    if not lines:
        return None

    location = addresses[0] if addresses else best_city_state(text)
    traffic = first_match(TRAFFIC_RE, text)
    ebitda = first_match(EBITDA_RE, text)
    revenue = first_match(REVENUE_RE, text)
    asking = first_match(PRICE_RE, text)
    has_financial_signal = bool(asking or revenue or traffic or (ebitda and money_value(ebitda) >= 10_000))
    has_listing_signal = bool(re.search(r"\b(?:for sale|asking price|purchase price|loopnet|bizbuysell|crexi|offering memorandum)\b", text, re.I))
    if not (addresses or has_financial_signal or (has_listing_signal and location)):
        return None
    evidence_type = infer_evidence_type(text)
    title = best_document_title(lines, location, source, page_number)
    if not professional_title(title):
        if location:
            title = short_text(f"{evidence_type} - {location}")
        else:
            title = f"{evidence_type} - Page {page_number}"
    note_parts = [summary]
    if asking:
        note_parts.append(f"Asking price {asking}.")
    if revenue:
        note_parts.append(f"Revenue {revenue}.")
    if traffic:
        note_parts.append(f"Traffic {traffic}.")
    if ebitda:
        note_parts.append(f"EBITDA {ebitda}.")
    note = short_text(" ".join(part for part in note_parts if part), 260)

    return {
        "type": evidence_type,
        "document": source,
        "page": str(page_number),
        "name": title,
        "location": location,
        "status": "",
        "lot_size": "",
        "traffic_count": traffic,
        "revenue": revenue,
        "asking_price": asking,
        "ebitda": ebitda,
        "note": note or f"Relevant scanned evidence on page {page_number}.",
    }


def evidence_sort_key(row: dict[str, str]) -> tuple[int, int, int, int]:
    row_type = row.get("type", "")
    type_rank = {
        "Current Portfolio Site": 0,
        "Development Site": 1,
        "Listing / Offering": 2,
        "Traffic / Site Evidence": 3,
        "Demographic Support": 4,
        "Financial Support": 5,
        "Source Evidence": 6,
    }.get(row_type, 7)
    missing_location = 0 if row.get("location") else 1
    missing_metrics = 0 if (row.get("traffic_count") or row.get("ebitda") or row.get("revenue") or row.get("asking_price")) else 1
    page = int(row.get("page") or 9999)
    return (type_rank, missing_location, missing_metrics, page)


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    return slug or "document.pdf"


def ensure_document_link(pdf_path: Path) -> str:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    target = DOC_DIR / slugify(pdf_path.name)
    if target.is_symlink():
        target.unlink()
    if target.exists():
        return f"documents/{target.name}"
    shutil.copy2(pdf_path, target)
    return f"documents/{target.name}"


def page_summary(page: str, max_chars: int = 340) -> str:
    lines = [clean(line) for line in page.splitlines() if readable_line(line)]
    scored: list[tuple[int, str]] = []
    for line in lines:
        score = 0
        if KEY_TERMS.search(line):
            score += 8
        if ADDRESS_RE.search(line):
            score += 5
        if re.search(r"\$\s?\d|(?:19|20)\d{2}|\b\d{1,3},\d{3}\b", line):
            score += 3
        if score:
            scored.append((score, line))
    if scored:
        scored.sort(reverse=True)
        return clean(" ".join(line for _, line in scored[:3]))[:max_chars]
    return ""


def page_search_text(page: str, max_chars: int = 2400) -> str:
    lines = [clean(line) for line in page.splitlines() if readable_line(line)]
    text = clean(" ".join(lines))
    return text[:max_chars]


def document_group(pdf_path: Path, is_image_scan: bool) -> str:
    title = pdf_path.stem.lower()
    if is_image_scan:
        return "Image Scans"
    if "most recent" in title:
        return "Recent Traffic & Site Packet"
    if "bin" in title:
        return "Scanned Deal Bins"
    if re.search(r"document_\d{8}", title):
        return "Dated Source PDFs"
    return "Supporting Source PDFs"


def extract_development_rows(text: str, source: str, page_number: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in text.splitlines():
        line = clean(raw)
        match = re.match(
            r"(?P<site>[A-Z][A-Za-z0-9& .'-]+?)\s+"
            r"(?P<city>[A-Z][A-Za-z .'-]+,\s*(?:AZ|CA|CO))\s+"
            r"(?P<status>In Construction|Pre-Construction|In Escrow)\s+"
            r"(?P<dates>.+?)\s+"
            r"(?P<own>Own|Lease)\s+"
            r"(?P<lot>(?:\d+(?:\.\d+)?|0?2)\s+acres)\s+"
            r"(?P<tunnel>\d{2,3})\s+"
            r"(?P<vacuums>\d{1,2})\s+"
            r"(?P<traffic>\d{1,3},\d{3})\s+"
            r"(?P<cost>\d[\d, ]{5,})\s+"
            r"(?P<ebitda>\d[\d,]{5,})$",
            line,
        )
        if not match:
            continue
        data = {key: clean(value) for key, value in match.groupdict().items()}
        rows.append(
            {
                "type": "Development Site",
                "document": source,
                "page": str(page_number),
                "name": data["site"],
                "location": data["city"],
                "status": data["status"],
                "lot_size": data["lot"].replace("02 acres", "0.2 acres"),
                "traffic_count": data["traffic"],
                "revenue": "",
                "ebitda": f"${data['ebitda']}",
                "note": f"{data['status']} Super Star development site with {data['lot']} lot, {data['traffic']} traffic count, and stabilized EBITDA listed at ${data['ebitda']}.",
            }
        )
    return rows


def extract_current_site_rows(text: str, source: str, page_number: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    state = ""
    if "Current Site List - Arizona" in text:
        state = "AZ"
    elif "Current Site List - California" in text:
        state = "CA"
    if not state:
        return rows

    for raw in text.splitlines():
        line = clean(raw)
        match = re.match(
            r"(?P<site>[A-Z][A-Za-z0-9& .'-]+?)\s+"
            r"(?P<year>(?:19|20)\d{2})\s+"
            r"(?P<own>Own|Lease)\s+"
            r"(?P<lot>(?:\d+k SF|\d+(?:\.\d+)?\s+acres))\s+"
            r"(?P<vacuums>\d{1,2})\s+"
            r"(?P<traffic>\d{1,3},\d{3})\s+"
            r"(?P<revenue>\d[\d,]{5,})\s+"
            r"(?P<ebitda>\d[\d,]{5,})$",
            line,
        )
        if not match:
            continue
        data = {key: clean(value) for key, value in match.groupdict().items()}
        rows.append(
            {
                "type": "Current Portfolio Site",
                "document": source,
                "page": str(page_number),
                "name": data["site"],
                "location": state,
                "status": data["own"],
                "lot_size": data["lot"],
                "traffic_count": data["traffic"],
                "revenue": f"${data['revenue']}",
                "ebitda": f"${data['ebitda']}",
                "note": f"Super Star {state} site-list row from the scanned PDF. The row gives site label, year, ownership, lot size, traffic, revenue, and adjusted EBITDA, but not always a numbered street address.",
            }
        )
    return rows


def manual_visual_category(pdf_stem: str, page_number: int) -> tuple[str, str] | None:
    groups = IMAGE_SCAN_PAGE_GROUPS.get(pdf_stem, {})
    for group, pages in groups.items():
        if page_number in pages:
            return group, IMAGE_SCAN_INTERPRETATIONS[group]
    return None


def visual_category(text: str) -> tuple[str, str]:
    value = clean(text).lower()
    if not value or len(value) < 25:
        return ("Photo / Visual Reference", "Image-heavy pages with little readable OCR; review the thumbnail or full PDF page for site, signage, equipment, or visual context.")
    if re.search(r"\b(good|better|best|ultimate|deluxe|package|price|\$|wax|shine|tire|wheel|foam|ceramic|wash menu)\b", value):
        return ("Menu & Pricing", "Package boards, service levels, pricing, wax/tire add-ons, and customer-facing wash menus.")
    if re.search(r"\b(equipment|tunnel|conveyor|vacuum|pump|dryer|pre-?wash|scrubber|rinse|simoniz|touchless|automatic)\b", value):
        return ("Equipment & Operations", "Tunnel/equipment visuals, wash process details, vendor references, and operating setup clues.")
    if re.search(r"\b(site|building|exterior|entrance|exit|lane|road|street|parking|lot|sign|canopy|aerial|location)\b", value):
        return ("Site & Exterior", "Location/site visuals, signage, access, frontage, building views, and exterior context.")
    if re.search(r"\b(ebitda|revenue|sales|traffic|acres|cars|volume|count|financial|note|memo|asking)\b", value):
        return ("Deal & Operating Notes", "Pages that appear to contain operating, financial, traffic, or deal-context notes.")
    return ("Partial OCR Visuals", "Image pages with partial readable text; use the thumbnail and full PDF page together for interpretation.")


def gallery_images_for(pdf_path: Path, pages: list[str]) -> list[dict[str, str]]:
    folder = GALLERY_DIR / slugify(pdf_path.stem)
    if not folder.exists():
        return []
    images = []
    image_paths = sorted(folder.glob("page-*.jpg")) or sorted(folder.glob("page-*.png"))
    for image_path in image_paths:
        match = re.search(r"page-(\d+)", image_path.stem)
        page = str(int(match.group(1))) if match else ""
        page_index = int(page) - 1 if page else -1
        page_text = pages[page_index] if 0 <= page_index < len(pages) else ""
        manual_category = manual_visual_category(pdf_path.stem, int(page) if page else 0)
        group, interpretation = manual_category or visual_category(page_text)
        images.append(
            {
                "page": page,
                "group": group,
                "interpretation": interpretation,
                "image_url": f"documents/gallery/{folder.name}/{image_path.name}",
                "pdf_page_url": f"documents/{slugify(pdf_path.name)}#page={page}" if page else f"documents/{slugify(pdf_path.name)}",
            }
        )
    return images


def build() -> list[dict[str, object]]:
    documents: list[dict[str, object]] = []
    for pdf_path in sorted(PDF_DIR.glob("*.pdf")):
        txt_path = OCR_DIR / f"{pdf_path.stem}.txt"
        text = txt_path.read_text(errors="ignore") if txt_path.exists() else ""
        pages = text.split("\f") if text else []
        page_cards = []
        search_pages = []
        evidence_rows = []
        for index, page in enumerate(pages, start=1):
            if not clean(page):
                continue
            searchable_text = page_search_text(page)
            if searchable_text:
                search_pages.append(
                    {
                        "page": str(index),
                        "text": searchable_text,
                    }
                )
            addresses = valid_addresses_from(page)
            has_evidence = bool(KEY_TERMS.search(page) or addresses)
            page_rows = []
            page_rows.extend(extract_current_site_rows(page, txt_path.name if txt_path.exists() else pdf_path.name, index))
            page_rows.extend(extract_development_rows(page, txt_path.name if txt_path.exists() else pdf_path.name, index))
            if has_evidence:
                summary = page_summary(page)
                if not summary:
                    continue
                if not page_rows:
                    generic_row = generic_evidence_row(page, txt_path.name if txt_path.exists() else pdf_path.name, index, summary, addresses)
                    if generic_row:
                        page_rows.append(generic_row)
                page_cards.append(
                    {
                        "page": str(index),
                        "summary": summary,
                        "addresses": list(dict.fromkeys(addresses[:10])),
                        "terms": [term for term in ["car wash", "traffic", "EBITDA", "revenue", "acres", "site list", "development"] if re.search(term, page, re.I)],
                    }
                )
            evidence_rows.extend(page_rows)
        gallery_images = gallery_images_for(pdf_path, pages)
        is_image_scan = bool(gallery_images) or re.search(r"\bimage|photo|picture|scan\b", pdf_path.stem, re.I)
        evidence_rows.sort(key=evidence_sort_key)
        documents.append(
            {
                "title": pdf_path.stem,
                "file_name": pdf_path.name,
                "category": "Image Scans" if is_image_scan else "Deal Records",
                "group": document_group(pdf_path, is_image_scan),
                "pdf_url": ensure_document_link(pdf_path),
                "text_url": f"ocr-output/{txt_path.name}" if txt_path.exists() else "",
                "page_count": len(pages),
                "evidence_page_count": len(page_cards),
                "evidence_row_count": len(evidence_rows),
                "pages": page_cards,
                "search_pages": search_pages[:500],
                "evidence_rows": evidence_rows,
                "gallery_images": gallery_images,
            }
        )
    return documents


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(build(), indent=2)
    OUT.write_text("window.CARWASH_DOCUMENT_LIBRARY = " + payload + ";\n", encoding="utf-8")
    print(f"Wrote document library to {OUT}")


if __name__ == "__main__":
    main()
