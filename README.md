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
3. Use `Screenshot Lead` for one screenshot, photo, or PDF. This is the easiest option.
4. Use `Paste a Listing Link` when you have a public LoopNet, BizBuySell, broker, or listing page URL.
5. Use `Type Details Instead` only when you already know the location/details.
6. Use `Upload Many Files` for bulk PDFs, scans, photos, spreadsheets, or ZIP backups.
7. Go back to the Scout and search. Admin-added washes load automatically from the hosted backend.

## Automatic Enrichment

Admin-added records can be enriched automatically when API keys are configured on the server:

- `OPENAI_API_KEY`: reads uploaded screenshot/photo images and extracts visible listing fields.
- `OPENAI_VISION_MODEL`: optional model override for image reading.
- `GOOGLE_PLACES_API_KEY` or `GOOGLE_MAPS_API_KEY`: looks up the address and fills public contact fields such as current business name, phone, website, Google Maps link, and coordinates.
- `TRAFFIC_API_URL`: optional traffic-count provider URL. Use `{lat}`, `{lng}`, and `{address}` placeholders if your provider supports them.
- `DEMOGRAPHICS_API_URL`: optional demographic provider URL for 1-mile, 3-mile, and 5-mile population rings. Use `{lat}`, `{lng}`, and `{address}` placeholders if your provider supports them. If this is not set, live maintenance falls back to public Census ACS/TIGER population estimates.
- `MAINTENANCE_SECRET`: private token used by the nightly maintenance agent to update live admin records.

Scout does not invent financials or traffic counts. EBITDA, asking price, sales, cars/year, and traffic are filled only when visible in the uploaded material or supplied by an approved data source. The 1/3/5-mile population fields can be filled from imported demographic pages or estimated from public Census ACS/TIGER block groups. Phone, website, Google Maps link, and coordinates can be filled from Google Places when an address is found.

## Nightly Maintenance Agent

The repo includes a GitHub Actions agent at `.github/workflows/nightly-scout-maintenance.yml`.

What it does every night:

- Runs at 8:00 PM Eastern time.
- Rebuilds the screened Scout records from the repo data.
- Fills missing 1-mile, 3-mile, and 5-mile demographics with Census ACS 2024/TIGER data where possible.
- Audits duplicates, bad addresses, and missing core fields.
- Calls the live Render site to re-check admin/Claude-added records.
- Commits updates back to GitHub, which lets Render redeploy automatically.

This works when your computer is closed because GitHub runs it in the cloud.

GitHub repo secrets to add:

- `SCOUT_SITE_URL`: your Render URL, for example `https://shullman-carwash-scout.onrender.com`
- `MAINTENANCE_SECRET`: the same private value you put in Render.
- `SCOUT_BASIC_AUTH`: optional, in this exact format: `shullman:yourRenderPassword`

Render environment variables to add:

- `MAINTENANCE_SECRET`: same value as the GitHub secret.
- Keep `SCOUT_PASSWORD` set so the site stays private.

Important: if another agent adds records by committing them to GitHub, the nightly job catches them in the repo. If another agent adds records through the live Admin page, the Render maintenance endpoint catches those live admin records.

## Importing Listing Links

The Admin page has a `Paste a Listing Link` form. When a public listing page is readable by the server, Scout pulls visible page text such as title, address, price, acres, phone, and deal notes, then saves the record into search. If `OPENAI_API_KEY` is configured, Scout can understand messier listing text more accurately. If `GOOGLE_PLACES_API_KEY` is configured, Scout can use the extracted address to add current public contact fields.

Some listing sites may block server-side reading, require login, or hide information behind scripts. In that case Scout still saves the URL as a lead, and the best fallback is to upload a screenshot or PDF of the listing.

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
