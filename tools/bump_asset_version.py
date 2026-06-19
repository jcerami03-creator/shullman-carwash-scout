#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "index.html"
RECORDS_PATH = ROOT / "generated" / "carwash_records.js"


def generated_records_changed() -> bool:
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", str(RECORDS_PATH.relative_to(ROOT))],
        cwd=ROOT,
    )
    return result.returncode != 0


def main() -> None:
    if not generated_records_changed():
        print("No generated record changes; asset version unchanged.")
        return

    html = INDEX_PATH.read_text(encoding="utf-8")

    def bump(match: re.Match[str]) -> str:
        return f'{match.group(1)}{int(match.group(2)) + 1}'

    updated = re.sub(r'(generated/carwash_records\.js\?v=)(\d+)', bump, html, count=1)
    if updated == html:
        raise SystemExit("Could not find generated carwash record script version in index.html")
    INDEX_PATH.write_text(updated, encoding="utf-8")
    print("Bumped generated carwash records asset version.")


if __name__ == "__main__":
    main()
