from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


ROOT = Path("/Users/josephcerami/Documents/LLM For Shullman Paperwork")
PDF_DIR = Path("/Users/josephcerami/PDF FOR CAR WASH SCOUt")
OCR_DIR = ROOT / "ocr-output"
DOC_DIR = ROOT / "documents"
GALLERY_DIR = DOC_DIR / "gallery"
OUT = ROOT / "generated" / "document_library.js"

KEY_TERMS = re.compile(
    r"\b(?:car wash|carwash|traffic counts?|ebitda|revenue|current site list|development sites|asking price|purchase price|acres|vacuum spaces|site selection)\b",
    re.I,
)
ADDRESS_RE = re.compile(
    r"\b\d{1,6}(?:-\d{1,6})?\s+[A-Z][A-Za-z0-9'.-]*(?:\s+[A-Za-z0-9'.#&/-]+){1,8},?\s+[A-Z][A-Za-z .'-]+,?\s+(?:AL|AR|AZ|CA|CO|CT|DE|FL|GA|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)\b(?:\s+\d{5})?",
    re.I,
)


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


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
    lines = [clean(line) for line in page.splitlines() if clean(line)]
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
    return clean(" ".join(lines[:4]))[:max_chars]


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
        group, interpretation = visual_category(page_text)
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
        evidence_rows = []
        for index, page in enumerate(pages, start=1):
            if not clean(page):
                continue
            addresses = [clean(match.group(0)) for match in ADDRESS_RE.finditer(page)]
            has_evidence = bool(KEY_TERMS.search(page) or addresses)
            evidence_rows.extend(extract_current_site_rows(page, txt_path.name if txt_path.exists() else pdf_path.name, index))
            evidence_rows.extend(extract_development_rows(page, txt_path.name if txt_path.exists() else pdf_path.name, index))
            if has_evidence:
                page_cards.append(
                    {
                        "page": str(index),
                        "summary": page_summary(page),
                        "addresses": list(dict.fromkeys(addresses[:10])),
                        "terms": [term for term in ["car wash", "traffic", "EBITDA", "revenue", "acres", "site list", "development"] if re.search(term, page, re.I)],
                    }
                )
        gallery_images = gallery_images_for(pdf_path, pages)
        is_image_scan = bool(gallery_images) or re.search(r"\bimage|photo|picture|scan\b", pdf_path.stem, re.I)
        documents.append(
            {
                "title": pdf_path.stem,
                "file_name": pdf_path.name,
                "category": "Image Scans" if is_image_scan else "Deal Records",
                "pdf_url": ensure_document_link(pdf_path),
                "text_url": f"ocr-output/{txt_path.name}" if txt_path.exists() else "",
                "page_count": len(pages),
                "evidence_page_count": len(page_cards),
                "evidence_row_count": len(evidence_rows),
                "pages": page_cards[:180],
                "evidence_rows": evidence_rows[:300],
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
