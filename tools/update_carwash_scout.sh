#!/usr/bin/env zsh
set -euo pipefail

project_dir="/Users/josephcerami/Documents/LLM For Shullman Paperwork"
pdf_dir="/Users/josephcerami/PDF FOR CAR WASH SCOUt"
output_dir="$project_dir/ocr-output"
ocr_bin_dir="$project_dir/mamba-ocr/bin"
runtime_python="/Users/josephcerami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
runtime_node="/Users/josephcerami/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
runtime_node_modules="/Users/josephcerami/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"

mkdir -p "$output_dir"
cd "$project_dir"

if [[ ! -e "$project_dir/node_modules" ]]; then
  ln -s "$runtime_node_modules" "$project_dir/node_modules"
fi

export PATH="$ocr_bin_dir:$PATH"

for input_pdf in "$pdf_dir"/*.pdf; do
  base="$(basename "$input_pdf" .pdf)"
  sidecar_txt="$output_dir/${base}.txt"
  output_pdf="$output_dir/${base}_ocr.pdf"

  if [[ -f "$sidecar_txt" ]]; then
    echo "Skipping $base, text already exists."
    continue
  fi

  echo "Extracting text: $base"
  set +e
  "$runtime_python" - "$input_pdf" "$sidecar_txt" <<'PY'
from pathlib import Path
import sys
from pypdf import PdfReader

source = Path(sys.argv[1])
target = Path(sys.argv[2])
reader = PdfReader(str(source))
pages = [(page.extract_text() or "") for page in reader.pages]
text = "\f".join(pages).strip()
if len(text) < 100:
    raise SystemExit(2)
target.write_text(text, encoding="utf-8")
print(f"Extracted embedded text from {len(reader.pages)} pages.")
PY
  ocr_status=$?
  set -e
  if [[ "$ocr_status" -eq 2 ]]; then
    echo "Embedded text was weak; running OCR: $base"
    ocrmypdf \
      --output-type pdf \
      --rotate-pages \
      --deskew \
      --sidecar "$sidecar_txt" \
      "$input_pdf" \
      "$output_pdf"
  elif [[ "$ocr_status" -ne 0 ]]; then
    exit "$ocr_status"
  fi
done

echo "Rendering image galleries..."
for input_pdf in "$pdf_dir"/*.pdf; do
  base="$(basename "$input_pdf" .pdf)"
  lower_base="${base:l}"
  if [[ "$lower_base" != *image* && "$lower_base" != *photo* && "$lower_base" != *picture* && "$lower_base" != *gallery* && "$lower_base" != *visual* ]]; then
    continue
  fi

  gallery_slug="$(printf "%s" "$base" | sed -E 's/[^A-Za-z0-9._-]+/-/g; s/^-+//; s/-+$//')"
  if [[ -z "$gallery_slug" ]]; then
    gallery_slug="document"
  fi

  echo "Rendering gallery: $base"
  swift tools/render_pdf_gallery.swift "$input_pdf" "$project_dir/documents/gallery/$gallery_slug" 420
done

echo "Rebuilding Carwash Scout records..."
python3 tools/build_carwash_records.py

echo "Rebuilding document library..."
python3 tools/build_document_library.py

echo "Running quality audit..."
python3 tools/audit_carwash_records.py

echo "Exporting spreadsheet..."
"$runtime_node" tools/export_carwash_spreadsheet.mjs

echo "Done. Site data and spreadsheet are updated."
