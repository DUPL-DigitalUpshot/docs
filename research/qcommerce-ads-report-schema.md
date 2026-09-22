# Q-Commerce Ads Reports — Report Types & Column Reference

Scope: Zepto, Blinkit, Swiggy Instamart, Flipkart Minutes, BigBasket
Prepared: 23 Aug 2026 · Project: Vishnu-DM / marketplace commerce platform

---

## Important caveat on "exact" column names

None of these five publish an ads-reporting schema publicly. Blinkit Brand Central, Zepto Ads Manager, Swiggy's Instamart Ads Manager and BigBasket's ads console are all behind brand/seller logins, and their CSV headers change between releases without notice. Flipkart is the only one of the five with semi-public reporting documentation (via Flipkart Ads / Flipkart Commerce Cloud partner docs).

So this document has two parts:

1. **What is known** — report types and metric labels per platform, marked by confidence.
2. **How to lock down the exact headers** — the one-hour capture exercise that gives you ground truth, which is the only defensible input for an RPA parser.

Treat everything marked *unverified* as a strong prior, not a spec. Do not hardcode a parser against it.

---

## 1. Flipkart Ads (incl. Flipkart Minutes) — best documented

Console: advertise.flipkart.com / Flipkart Seller Hub → Advertising

**Report types**

| Report | Grain |
|---|---|
| Consolidated / Campaign report | campaign × day |
| Search Term report | campaign × search term × day |
| Keyword report | campaign × keyword × match type × day |
| Placement report | campaign × placement × day |
| Product / FSN report | campaign × FSN × day |

**Columns — high confidence (Flipkart's own vocabulary)**

Note Flipkart says **Views** (not Impressions) and **ROI** (not ROAS), and splits every outcome into Direct / Indirect / Total.

```
Date
Campaign Name
Campaign ID
Campaign Type            (PLA / PCA / Brand)
Campaign Status
Ad Group / Ad Set Name
FSN
Product Title
Views
Clicks
CTR
Ad Spend
CPC
Product Page Views
Direct Units Sold
Indirect Units Sold
Total Units Sold
Direct Revenue
Indirect Revenue
Total Revenue
Direct ROI
Indirect ROI
Total ROI
```

Keyword / Search Term reports add: `Keyword`, `Match Type` (Exact / Phrase / Broad), `Search Term`, `Add to Cart`.

**Flipkart Minutes:** ads for Minutes run through the same console. Expect a store/placement dimension (`Placement` or `Business Unit`) rather than a separate report family — confirm which value identifies Minutes inventory before you build the filter.

---

## 2. Blinkit (Brand Central) — medium confidence

Console: brands.blinkit.com

**Campaign families:** Reach campaigns (banner / visibility) and Performance campaigns (product recommendation, search listing).

- Reach reporting is built around: impressions, add-to-cart, campaign cost.
- Performance reporting is built around: impressions, add-to-carts, sales, return on ad spend, new user acquisition.

**Expected export columns — unverified**

```
Date
Campaign Name
Campaign ID
Campaign Type            (Product Recommendation / Search / Banner)
Status
Start Date / End Date
Budget
Estimated Budget Consumed        ← Blinkit's word for spend
Impressions
Clicks
CTR
Add to Cart
Direct Quantities Sold
Indirect Quantities Sold
Total Quantities Sold
Direct Sales
Indirect Sales
Total Sales
ROAS
CPM
New Users / New User Acquisition
```

Blinkit also exposes city and dark-store level breakdowns in some views — check whether `City` and `Store ID` appear in your account's export, since that materially changes your table grain.

---

## 3. Zepto Ads — verify from your own extraction

Console: Zepto brand/ads portal (Zepto Ads Manager; analytics under Zepto Atom)

You already have working RPA extraction for Zepto with client-validated data. **Your own Zepto export is the authoritative schema** — dump its header row and treat that as the reference implementation for the other four.

**Typical fields — unverified**

```
Date
Campaign Name / Campaign ID
Campaign Type            (Product Listing Ad / Product Recommendation / Banner)
Status
Daily Budget / Total Budget
Spend
Impressions
Clicks
CTR
CPC
Add to Cart
Orders
Units Sold
Revenue / GMV
ROAS
Conversion Rate
SKU / Product ID / Product Name
Keyword, Match Type      (keyword-level report)
City                      (where geo breakdown is enabled)
```

---

## 4. Swiggy Instamart Ads — low confidence

Console: Swiggy brand partner portal → Ads Manager (revamped brand sales dashboard rolled out recently, so headers are actively changing)

**Ad formats:** Sponsored/keyword-driven product ads, display banners, category placements.

**Expected columns — unverified**

```
Date
Campaign Name / Campaign ID
Campaign Type
Status
Budget
Spend
Impressions
Clicks
CTR
CPC
Add to Cart
Orders
Units Sold
GMV / Sales
ROI / ROAS
Direct vs Indirect split (presence varies)
Item ID / Product Name
City / Store
```

Flag: because Instamart's brand dashboard was recently rebuilt, build the Instamart parser last and schema-diff it on every run.

---

## 5. BigBasket Ads — lowest confidence

Console: BigBasket brand/supplier ads platform

**Ad formats:** sponsored product (search), banners, brand store.

**Expected columns — unverified**

```
Date
Campaign Name / Campaign ID
Campaign Type
Status
Budget
Spend
Impressions
Clicks
CTR
CPC
Orders
Units Sold
Revenue / Sales
ROAS
SKU ID / Product Name
City / Fulfilment Centre
```

BigBasket reporting has historically been the most manual of the five — expect emailed or on-request reports rather than a clean self-serve CSV for some account types. Confirm with the client what their BigBasket account actually exposes before estimating effort.

---

## Normalized schema for the unified platform

Map every platform into one fact table. Suggested canonical columns:

```
report_date
platform                 (zepto | blinkit | instamart | flipkart_minutes | bigbasket)
account_id
campaign_id
campaign_name
campaign_type_raw
campaign_type_norm       (search | product_recommendation | display | brand_store)
ad_group_id / ad_group_name
sku_id_raw               (FSN / item id / SKU)
sku_name
keyword
match_type
city
store_id
impressions              ← Flipkart "Views"
clicks
ctr
spend                    ← Blinkit "Estimated Budget Consumed"
cpc
cpm
add_to_cart
orders
units_direct
units_indirect
units_total
revenue_direct
revenue_indirect
revenue_total
roas                     ← Flipkart "ROI"
new_users
source_file
extracted_at
raw_row_json
```

Two rules worth enforcing from day one:

- **Keep `raw_row_json`.** When a platform silently renames a column, you can reprocess history instead of re-scraping it.
- **Store the raw header row per extraction run** and diff it against the last known header. A changed header should raise an alert, not silently produce nulls.

---

## Getting ground truth — the capture exercise

For each of the five, ask the client (who holds the domain knowledge and the logins) to:

1. Log into the ads console.
2. Export every available report type for the same 7-day window.
3. Send the raw files untouched — no Excel cleanup.
4. Note which reports are self-serve vs. account-manager-supplied.

Then produce a single `header_inventory.csv`: `platform, report_name, column_position, column_name, sample_value, inferred_type`. That file becomes the contract for the parser layer, and it is what should go into the proposal as the schema deliverable rather than any list assembled from public sources.

Ask specifically whether each platform's export includes:

- city / dark-store granularity
- direct vs indirect attribution split
- keyword and search-term level rows
- SKU-level rows, and which product identifier is used

Those four questions decide the grain of your fact table, and getting the grain wrong is the expensive mistake to make in month one.
