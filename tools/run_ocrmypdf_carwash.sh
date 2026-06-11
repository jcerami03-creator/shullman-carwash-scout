#!/usr/bin/env zsh
set -euo pipefail

project_dir="/Users/josephcerami/Documents/LLM For Shullman Paperwork"
input_dir="/Users/josephcerami/PDF FOR CAR WASH SCOUt"
output_dir="$project_dir/ocr-output"
ocr_bin_dir="$project_dir/mamba-ocr/bin"

mkdir -p "$output_dir"

export PATH="$ocr_bin_dir:$PATH"

for input_pdf in "$input_dir"/*.pdf; do
  base="$(basename "$input_pdf" .pdf)"
  output_pdf="$output_dir/${base}_ocr.pdf"
  sidecar_txt="$output_dir/${base}.txt"

  if [[ -f "$output_pdf" && -f "$sidecar_txt" ]]; then
    echo "Skipping $base, already OCRed."
    continue
  fi

  echo "OCR starting: $base"
  ocrmypdf \
    --output-type pdf \
    --rotate-pages \
    --deskew \
    --sidecar "$sidecar_txt" \
    "$input_pdf" \
    "$output_pdf"
  echo "OCR finished: $base"
done

echo "All OCR jobs finished. Output folder: $output_dir"
