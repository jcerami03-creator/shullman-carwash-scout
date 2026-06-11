# Shullman Car Wash Knowledge Base

A private browser-based prototype for searching car wash deal notes, valuation tables, and wisdom-layer memos.

## What It Does

- Loads a demo knowledge base modeled after the photographed worksheet.
- Uploads CSV, JSON, or OCR text exports.
- Searches by typed or spoken questions.
- Supports prompt examples like:
  - What made a great acquisition?
  - Show 1990s valuation trends.
  - Find examples of moats being destroyed.
- Filters by market, year, and max asking price.
- Shows deal-table fields:
  - Year
  - Market
  - Asking Price
  - Sales
  - EBITDA
  - Cars/Yr
  - Acres
  - Note
- Opens a professional detail view with wisdom, decision, mistake, and mental-model layers.

## Best Upload Format

CSV is best:

```csv
year,market,asking_price,sales,ebitda,cars_per_year,acres,note,wisdom_layer,decision_layer,mistake_layer,mental_model
2007,Florida,$5.2M,$2.0M,$610K,120000,1.05,Seller story stretched,Future-proofing required separating proof from hope,Do not chase without lower basis,Paying for upside twice,Price is a fact; upside is a hypothesis
```

Scanned PDFs should be OCR'd into CSV, JSON, or text before uploading.
