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

## Easiest Future Workflow

1. Open the hosted Scout site and log in.
2. Click `Admin Upload`.
3. Use `Upload Files` for PDFs, scans, photos, screenshots, CSVs, or notes.
4. Use `Add One Car Wash` when you already know the location/details and just want it searchable fast.
5. Use `Research Queue` for LoopNet, BizBuySell, broker pages, or other online leads: copy the listing URL and visible listing text, paste it there, and save.
6. Go back to the Scout and search. Admin-added washes and pasted research leads load automatically from the hosted backend.

## Searching Images

Open `Document Library` and use the document search box. For scanned image pages, search terms like:

- `image`
- `menu`
- `pricing`
- `traffic`
- `census`
- `aerial`
- city, state, address, page number, or car wash name

The Document Library also has quick search chips for common image searches.

## Daily LoopNet / BizBuySell Agent

The automatic workflow is:

1. Create saved searches/alerts for car washes on LoopNet, BizBuySell, broker sites, or approved listing feeds.
2. Send those alert emails/exports into a parser such as Zapier, Make, or a custom approved feed.
3. Post each new lead into the Scout endpoint: `/api/manual-records`.
4. The Scout loads those records automatically and compares them against existing records by URL, map link, website, phone, name, market, and state.

Do not build this as a bot that bypasses site login, scraping limits, or terms of use. Use alerts, approved exports, broker emails, or licensed feeds for the daily intake. That still gives the practical result: new car wash leads are added to the Scout automatically every day.
