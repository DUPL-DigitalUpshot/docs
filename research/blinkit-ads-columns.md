# Blinkit Ads — sheets and columns: dependent or independent

Every column Blinkit sends, sheet by sheet, and whether it carries its own information (**independent**) or can be calculated from other columns (**dependent**).

- **Measured on:** 15 workbooks: the 5 distinct files UniQCAI stored for Del Monte (2026-09-01 → 2026-10-13) and the 10 downloaded by the legacy prototype (1 Jul → 13 Oct 2026, run on the updated code on 14 Oct). Two advertisers: FIELD FRESH FOODS PVT LTD (Del Monte) and Dinshaw's Dairy Foods. Every sheet had one header layout across all 15 files.
- **Dependent %** = share of rows on which the formula reproduces Blinkit's own value.
- **Proposed treatment** comes from the ingest mappings in `backend/ingest/mappings/blinkit.brandcentral/`. Blinkit is not loaded yet (phase 3); `dashboard_export` has no mapping.
- **Captured:** 2026-10-14, re-measured after the legacy downloader changes.

| Status | Meaning |
|---|---|
| Independent · metric | A measured number: store it |
| Independent · setting / rank / status | Its own information, but never added up |
| **Dependent** | Can be recalculated from other columns: check it, don't rely on it |
| Label / Date | Says what the row is about |
| Brand check | Must match the login's brand |

**Only five kinds of column are dependent:** Direct RoAS, Total RoAS, CTR, Claimables and served_budget_consumed.

## Report 1 · `mtd_search_report` (browser download, one workbook)

### MTD Claimables

8 columns · 939 rows in 7 files

| # | Column | Status | Formula / note | Proposed treatment |
|---|---|---|---|---|
| 1 | `Manufacturer` | Brand check | The advertiser (e.g. `FIELD FRESH FOODS PVT LTD`): a manufacturer, not a brand (Q21). | brand check |
| 2 | `Campaign Name` | Label | Not a key: an ID can carry several names | label |
| 3 | `Campaign ID` | Label |  | label |
| 4 | `Campaign Type` | Label |  | label |
| 5 | `Impressions` | Independent · metric | Month-to-date control figure | stored as number |
| 6 | `Total Budget` | Independent · setting | Sum of the daily budgets over the campaign's active days | kept as-is |
| 7 | `Claimables` | **Dependent** | = min(served_budget_consumed, Total Budget) · 100% of 939 rows | kept as-is |
| 8 | `served_budget_consumed` | **Dependent** | = Σ daily Estimated Budget Consumed of the campaign since its last budget reset (usually the 1st) · 96.3% of 939 rows | kept as-is |

### Keyword Targeting

22 columns · 37,672 rows in 7 files

| # | Column | Status | Formula / note | Proposed treatment |
|---|---|---|---|---|
| 1 | `Manufacturer` | Brand check | The advertiser (e.g. `FIELD FRESH FOODS PVT LTD`): a manufacturer, not a brand (Q21). | brand check |
| 2 | `date_ist` | Date | ISO `YYYY-MM-DD` text | row date |
| 3 | `Campaign ID` | Label |  | label |
| 4 | `Campaign Name` | Label | Not a key: an ID can carry several names | label |
| 5 | `Keyword` | Label |  | label |
| 6 | `Most Viewed Position` | Independent · rank | A position, never summed | kept as-is |
| 7 | `Match Type` | Label | EXACT; SMART and NA also seen (July/August) | label |
| 8 | `Pacing Type` | Label |  | label |
| 9 | `CPM` | Independent · setting | The CPM bid. Spend = CPM × Impressions ÷ 1000 holds on 78.5% of 37,672 rows, so never derive spend from it | kept as-is |
| 10 | `Total Budget` | Independent · setting | Daily budget; never summed | kept as-is |
| 11 | `Impressions` | Independent · metric |  | stored as number |
| 12 | `Direct ATC` | Independent · metric |  | stored as number |
| 13 | `Indirect ATC` | Independent · metric |  | stored as number |
| 14 | `New Users` | Independent · metric | New-to-brand users (Q9) | stored as number |
| 15 | `Direct Sales` | Independent · metric |  | stored as number |
| 16 | `Indirect Sales` | Independent · metric |  | stored as number |
| 17 | `Direct Quantities Sold` | Independent · metric |  | stored as number |
| 18 | `Indirect Quantities Sold` | Independent · metric |  | stored as number |
| 19 | `Estimated Budget Consumed` | Independent · metric | Spend | stored as number |
| 20 | `Direct RoAS` | **Dependent** | = Direct Sales ÷ Estimated Budget Consumed · 100% of 37,672 rows | checked, then recalculated |
| 21 | `Total RoAS` | **Dependent** | = (Direct Sales + Indirect Sales) ÷ Estimated Budget Consumed · 100% of 37,672 rows | checked, then recalculated |
| 22 | `latest on hold timestamp` | Independent · status | When the daily budget ran out; `0` = it didn't (mixed number/text) | kept as-is |

### Category Targeting

21 columns · 154 rows in 5 files · only in the September files (no category campaigns in October)

| # | Column | Status | Formula / note | Proposed treatment |
|---|---|---|---|---|
| 1 | `Manufacturer` | Brand check | The advertiser (e.g. `FIELD FRESH FOODS PVT LTD`): a manufacturer, not a brand (Q21). | brand check |
| 2 | `date_ist` | Date | ISO `YYYY-MM-DD` text | row date |
| 3 | `Campaign ID` | Label |  | label |
| 4 | `Campaign Name` | Label | Not a key: an ID can carry several names | label |
| 5 | `Category Name` | Label |  | label |
| 6 | `Pacing Type` | Label |  | label |
| 7 | `Most Viewed Position` | Independent · rank | A position, never summed | kept as-is |
| 8 | `CPM` | Independent · setting | The CPM bid. Spend = CPM × Impressions ÷ 1000 holds on 65.6% of 154 rows, so never derive spend from it | kept as-is |
| 9 | `Total Budget` | Independent · setting | Daily budget; never summed | kept as-is |
| 10 | `Impressions` | Independent · metric |  | stored as number |
| 11 | `Direct ATC` | Independent · metric |  | stored as number |
| 12 | `Indirect ATC` | Independent · metric |  | stored as number |
| 13 | `New Users` | Independent · metric | New-to-brand users (Q9) | stored as number |
| 14 | `Direct Sales` | Independent · metric |  | stored as number |
| 15 | `Indirect Sales` | Independent · metric |  | stored as number |
| 16 | `Direct Quantities Sold` | Independent · metric |  | stored as number |
| 17 | `Indirect Quantities Sold` | Independent · metric |  | stored as number |
| 18 | `Estimated Budget Consumed` | Independent · metric | Spend | stored as number |
| 19 | `Direct RoAS` | **Dependent** | = Direct Sales ÷ Estimated Budget Consumed · 100% of 154 rows | checked, then recalculated |
| 20 | `Total RoAS` | **Dependent** | = (Direct Sales + Indirect Sales) ÷ Estimated Budget Consumed · 100% of 154 rows | checked, then recalculated |
| 21 | `latest on hold timestamp` | Independent · status | When the daily budget ran out; `0` = it didn't (mixed number/text) | kept as-is |

### Listing Spotlight

15 columns · 2,227 rows in 7 files

| # | Column | Status | Formula / note | Proposed treatment |
|---|---|---|---|---|
| 1 | `Manufacturer` | Brand check | The advertiser (e.g. `FIELD FRESH FOODS PVT LTD`): a manufacturer, not a brand (Q21). | brand check |
| 2 | `date_ist` | Date | ISO `YYYY-MM-DD` text | row date |
| 3 | `Campaign ID` | Label |  | label |
| 4 | `Campaign Name` | Label | Not a key: an ID can carry several names | label |
| 5 | `Keyword` | Label | Listing Spotlight folds small keywords into `Others` | label |
| 6 | `Match Type` | Label | EXACT; SMART and NA also seen (July/August) | label |
| 7 | `Pacing Type` | Label |  | label |
| 8 | `CPM` | Independent · setting | The CPM bid. Spend = CPM × Impressions ÷ 1000 holds on 99.8% of 2,227 rows, so never derive spend from it | kept as-is |
| 9 | `total_budget` | Independent · setting | Daily budget; never summed | kept as-is |
| 10 | `Impressions` | Independent · metric |  | stored as number |
| 11 | `Reach` | Independent · metric | Unique users; never summed | kept as-is |
| 12 | `Unique Clicks` | Independent · metric | Unique; never summed | kept as-is |
| 13 | `CTR %` | **Dependent** | = Unique Clicks ÷ **Reach** × 100 · 100% of 2,223 rows (÷ Impressions: only 39.2% of 1,353 rows) | checked, then recalculated |
| 14 | `Estimated Budget Consumed` | Independent · metric | Spend | stored as number |
| 15 | `latest on hold timestamp` | Independent · status | When the daily budget ran out; `0` = it didn't (mixed number/text) | kept as-is |

### Product Recommendation

22 columns · 3,446 rows in 7 files

| # | Column | Status | Formula / note | Proposed treatment |
|---|---|---|---|---|
| 1 | `Manufacturer` | Brand check | The advertiser (e.g. `FIELD FRESH FOODS PVT LTD`): a manufacturer, not a brand (Q21). | brand check |
| 2 | `date_ist` | Date | ISO `YYYY-MM-DD` text | row date |
| 3 | `Campaign ID` | Label |  | label |
| 4 | `Subcampaign ID` | Label |  | label |
| 5 | `Campaign Name` | Label | Not a key: an ID can carry several names | label |
| 6 | `Asset` | Label |  | label |
| 7 | `Title` | Label |  | label |
| 8 | `Pacing Type` | Label |  | label |
| 9 | `CPM` | Independent · setting | The CPM bid. Spend = CPM × Impressions ÷ 1000 holds on 100% of 3,446 rows, so never derive spend from it | kept as-is |
| 10 | `Total Budget` | Independent · setting | Daily budget; never summed | kept as-is |
| 11 | `Impressions` | Independent · metric |  | stored as number |
| 12 | `Direct ATC` | Independent · metric |  | stored as number |
| 13 | `Indirect ATC` | Independent · metric |  | stored as number |
| 14 | `New Users` | Independent · metric | New-to-brand users (Q9) | stored as number |
| 15 | `Direct Sales` | Independent · metric |  | stored as number |
| 16 | `Indirect Sales` | Independent · metric |  | stored as number |
| 17 | `Estimated Budget Consumed` | Independent · metric | Spend | stored as number |
| 18 | `Direct Quantities Sold` | Independent · metric |  | stored as number |
| 19 | `Indirect Quantities Sold` | Independent · metric |  | stored as number |
| 20 | `Direct RoAS` | **Dependent** | = Direct Sales ÷ Estimated Budget Consumed · 100% of 3,446 rows | checked, then recalculated |
| 21 | `Total RoAS` | **Dependent** | = (Direct Sales + Indirect Sales) ÷ Estimated Budget Consumed · 100% of 3,446 rows | checked, then recalculated |
| 22 | `latest on hold timestamp` | Independent · status | When the daily budget ran out; `0` = it didn't (mixed number/text) | kept as-is |

## Report 2 · `dashboard_export` (arrives by email, one workbook)

### BANNER_LISTING

12 columns · 1,367 rows in 8 files

| # | Column | Status | Formula / note | Proposed treatment |
|---|---|---|---|---|
| 1 | `Date` | Date | `DD-MM-YYYY` text: parse, don't sort as text | not mapped yet |
| 2 | `Campaign ID` | Label |  | not mapped yet |
| 3 | `Campaign Name` | Label | Not a key: an ID can carry several names | not mapped yet |
| 4 | `Targeting Type` | Label |  | not mapped yet |
| 5 | `Targeting Value` | Label |  | not mapped yet |
| 6 | `Match Type` | Label | EXACT; SMART and NA also seen (July/August) | not mapped yet |
| 7 | `CPM` | Independent · setting | The CPM bid. Spend = CPM × Impressions ÷ 1000 holds on 100% of 1,367 rows, so never derive spend from it | not mapped yet |
| 8 | `Impressions` | Independent · metric |  | not mapped yet |
| 9 | `Reach` | Independent · metric | Unique users; never summed | not mapped yet |
| 10 | `CTR` | **Dependent** | = Unique Clicks ÷ **Reach** × 100 · 100% of 1,364 rows (÷ Impressions: only 59.5% of 464 rows) | not mapped yet |
| 11 | `Unique Clicks` | Independent · metric | Unique; never summed | not mapped yet |
| 12 | `Estimated Budget Consumed` | Independent · metric | Spend | not mapped yet |

### PRODUCT_LISTING

20 columns · 26,022 rows in 7 files

| # | Column | Status | Formula / note | Proposed treatment |
|---|---|---|---|---|
| 1 | `Date` | Date | `DD-MM-YYYY` text: parse, don't sort as text | not mapped yet |
| 2 | `Campaign ID` | Label |  | not mapped yet |
| 3 | `Campaign Name` | Label | Not a key: an ID can carry several names | not mapped yet |
| 4 | `Targeting Type` | Label |  | not mapped yet |
| 5 | `Targeting Value` | Label |  | not mapped yet |
| 6 | `Match Type` | Label | EXACT; SMART and NA also seen (July/August) | not mapped yet |
| 7 | `Most Viewed Position` | Independent · rank | A position, never summed | not mapped yet |
| 8 | `Pacing Type` | Label |  | not mapped yet |
| 9 | `CPM` | Independent · setting | The CPM bid. Spend = CPM × Impressions ÷ 1000 holds on 80.4% of 26,022 rows, so never derive spend from it | not mapped yet |
| 10 | `Impressions` | Independent · metric |  | not mapped yet |
| 11 | `Direct ATC` | Independent · metric |  | not mapped yet |
| 12 | `Indirect ATC` | Independent · metric |  | not mapped yet |
| 13 | `Direct Quantities Sold` | Independent · metric |  | not mapped yet |
| 14 | `Indirect Quantities Sold` | Independent · metric |  | not mapped yet |
| 15 | `Direct Sales` | Independent · metric |  | not mapped yet |
| 16 | `Indirect Sales` | Independent · metric |  | not mapped yet |
| 17 | `New Users Acquired` | Independent · metric | Same as New Users in the MTD export | not mapped yet |
| 18 | `Estimated Budget Consumed` | Independent · metric | Spend | not mapped yet |
| 19 | `Direct RoAS` | **Dependent** | = Direct Sales ÷ Estimated Budget Consumed · 100% of 26,022 rows | not mapped yet |
| 20 | `Total RoAS` | **Dependent** | = (Direct Sales + Indirect Sales) ÷ Estimated Budget Consumed · 100% of 26,022 rows | not mapped yet |

### PRODUCT_RECOMMENDATION

17 columns · 2,992 rows in 7 files

| # | Column | Status | Formula / note | Proposed treatment |
|---|---|---|---|---|
| 1 | `Date` | Date | `DD-MM-YYYY` text: parse, don't sort as text | not mapped yet |
| 2 | `Campaign ID` | Label |  | not mapped yet |
| 3 | `Campaign Name` | Label | Not a key: an ID can carry several names | not mapped yet |
| 4 | `Targeting Type` | Label |  | not mapped yet |
| 5 | `Pacing Type` | Label |  | not mapped yet |
| 6 | `CPM` | Independent · setting | The CPM bid. Spend = CPM × Impressions ÷ 1000 holds on 100% of 2,992 rows, so never derive spend from it | not mapped yet |
| 7 | `Impressions` | Independent · metric |  | not mapped yet |
| 8 | `Direct ATC` | Independent · metric |  | not mapped yet |
| 9 | `Indirect ATC` | Independent · metric |  | not mapped yet |
| 10 | `Direct Quantities Sold` | Independent · metric |  | not mapped yet |
| 11 | `Indirect Quantities Sold` | Independent · metric |  | not mapped yet |
| 12 | `Direct Sales` | Independent · metric |  | not mapped yet |
| 13 | `Indirect Sales` | Independent · metric |  | not mapped yet |
| 14 | `New Users Acquired` | Independent · metric | Same as New Users in the MTD export | not mapped yet |
| 15 | `Estimated Budget Consumed` | Independent · metric | Spend | not mapped yet |
| 16 | `Direct RoAS` | **Dependent** | = Direct Sales ÷ Estimated Budget Consumed · 100% of 2,992 rows | not mapped yet |
| 17 | `Total RoAS` | **Dependent** | = (Direct Sales + Indirect Sales) ÷ Estimated Budget Consumed · 100% of 2,992 rows | not mapped yet |

## Related

- Plain-language overview: [blinkit-ads-schema.html](blinkit-ads-schema.html)
- What we propose to store: [blinkit-ads-storage.html](blinkit-ads-storage.html)
- Blinkit Sales columns: [blinkit-sales-columns.md](blinkit-sales-columns.md)
- Research notes: [blinkit-ads-schema.md](blinkit-ads-schema.md) · mapping design: [../unified-db/11-mapping-blinkit.md](../unified-db/11-mapping-blinkit.md)
