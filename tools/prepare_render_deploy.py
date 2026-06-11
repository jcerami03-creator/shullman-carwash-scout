from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path("/Users/josephcerami/Documents/LLM For Shullman Paperwork")
PDF_DIR = Path("/Users/josephcerami/PDF FOR CAR WASH SCOUt")
DOCUMENTS_DIR = ROOT / "documents"


def slugify(name: str) -> str:
    keep = []
    for char in name:
        if char.isalnum() or char in "._-":
            keep.append(char)
        elif char.isspace():
            keep.append("-")
    slug = "".join(keep).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or name.replace(" ", "-")


def main() -> None:
    DOCUMENTS_DIR.mkdir(exist_ok=True)
    copied = 0
    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        target = DOCUMENTS_DIR / slugify(pdf.name)
        if target.is_symlink():
            target.unlink()
        if target.exists() and target.stat().st_size == pdf.stat().st_size:
            continue
        shutil.copy2(pdf, target)
        copied += 1
    print(f"Render deploy documents ready. Copied/updated {copied} PDFs in {DOCUMENTS_DIR}.")


if __name__ == "__main__":
    main()
