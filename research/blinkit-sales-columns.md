# Blinkit Sales (PartnersBiz) — reports and columns: dependent or independent

Every column of every Blinkit Sales report, and whether it carries its own information (**independent**) or can be calculated from other columns (**dependent**).

- **Measured on:** the files downloaded by the legacy prototype (`legacy/blinkit/reports/partnersbiz/`, runs of 31 Aug, 1 Sep and 12 Sep 2026). UniQCAI has stored no Blinkit Sales file yet: the 7 report types exist but are inactive.
- **Dependent %** = share of rows on which the formula reproduces Blinkit's own value.
- **Headers** were identical across all runs for every report.
- **Captured:** 2026-10-14, after the PartnersBiz engine changes in `legacy/blinkit/partnersbiz_engine.py`.

**Watch out:** in `sales`, `mrp` is the MRP *value* (qty × unit MRP), not a price. In `po`, the GST columns are *rates*, not amounts, and `igst` = `cgst` + `sgst` (summing all three double-counts). Money is plain rupees; round float noise to 2 decimals.

## Sales (daily units and MRP value) · `sales`

10 columns · 53,668 rows in 8 files · data 2026-07-01 → 2026-09-11 · grain: `item_id`, `city_id`, `date`

Final daily data: never restated after D-1. Sparse: only rows with sales.

| # | Column | Status | Formula / note |
|---|---|---|---|
| 1 | `item_id` | Label | Blinkit item id, 8 digits; 1:1 with item_name |
| 2 | `item_name` | Label | product name; 1:1 with item_id |
| 3 | `manufacturer_id` | Label | constant per business (one value) |
| 4 | `manufacturer_name` | Label | constant per business |
| 5 | `city_id` | Label | 1-4 digit int; 1:1 with city_name |
| 6 | `city_name` | Label | 39 cities |
| 7 | `category` | Label | Blinkit L0 category; 1:1 with item_id; same values as scorecard l0_category |
| 8 | `date` | Label | YYYY-MM-DD, IST calendar day; data lags one day (file ends yesterday) |
| 9 | `qty_sold` | Independent · metric | units, written as N.0 float text; min 1 (only rows with sales; zero days are absent) |
| 10 | `mrp` | **Dependent** | NOT unit MRP: GMV at MRP = sum over units of unit MRP = qty_sold x unit MRP (97.5-98.8% of rows with the item's modal unit MRP; ~96% of the rest are a mix of two MRPs the same day). Rupees, 1 decimal text |

## Stock on hand (snapshot) · `soh`

7 columns · 2,216 rows in 8 files · data 2026-08-31 → 2026-09-12 · grain: `created_at`, `backend_facility_id`, `item_id`

A snapshot on the download day; not a period.

| # | Column | Status | Formula / note |
|---|---|---|---|
| 1 | `created_at` | Label | snapshot date YYYY-MM-DD = download day; single value per file |
| 2 | `backend_facility_name` | Label | Blinkit warehouse (feeder) name; 1:1 with id |
| 3 | `backend_facility_id` | Label | 4-digit int |
| 4 | `item_id` | Label | 8-digit Blinkit item id |
| 5 | `item_name` | Label | product name |
| 6 | `backend_inv_qty` | Independent · metric | units at the warehouse; mostly 0 (94-97% zero in the Aug files) |
| 7 | `frontend_inv_qty` | Independent · metric | units in dark stores fed by that warehouse; independent of backend (frontend > backend on ~80% of Aug rows) |

## Purchase orders · `po`

25 columns · 3,120 rows in 12 files · data 2026-07-01 → 2026-09-12 · grain: `po_number`, `item_id`, `landing_rate`

A mutable snapshot: PO state and remaining quantity change between downloads.

| # | Column | Status | Formula / note |
|---|---|---|---|
| 1 | `po_number` | Label | 13- or 14-digit numeric id (format depends on facility); keep as text |
| 2 | `facility_name` | Label | Blinkit receiving facility; no facility id in this report |
| 3 | `manufacturer_name` | Label | constant |
| 4 | `entity_vendor_legal_name` | Label | Blinkit buying entity; value carries literal double quotes (raw """..."""), except a few newer rows -> same entity appears in two spellings |
| 5 | `vendor_name` | Label | supplier (the brand's own vendor codes, 2 values) |
| 6 | `order_date` | Label | 'YYYY-MM-DD 00:00:00 +0000 UTC' (Go time format), always midnight; report's date filter applies to it |
| 7 | `appointment_date` | Independent · setting / status | same format; blank unless a delivery slot is booked (Scheduled, some Expired/Fulfilled) |
| 8 | `expiry_date` | Independent · setting / status | same format; order_date + 2 days (~88%), +7 days (~11%), +3 |
| 9 | `po_state` | Independent · setting / status | line-level status, mutable: Expired, Unscheduled, Scheduled, Partially Scheduled, Fulfilled, Cancelled post Creation; changes between downloads (e.g. Scheduled/Fulfilled->Expired) |
| 10 | `item_id` | Label | 8-digit item id; 1:1 with upc |
| 11 | `name` | Label | product name |
| 12 | `uom_text` | Label | pack size text, mixed case units: '500 ML','300 GM','250 g','1 L','100 g (2 pieces)' |
| 13 | `upc` | Label | 13-digit EAN |
| 14 | `units_ordered` | Independent · metric | ordered units |
| 15 | `remaining_quantity` | **Dependent** | units not yet received = units_ordered - received; 0 <= remaining <= units_ordered (100%); invoice total_grn_quantity = sum(units_ordered - remaining_quantity) per PO on 99% of POs. Mutable snapshot |
| 16 | `landing_rate` | **Dependent** | GST-inclusive unit cost = cost_price x (1 + tax_value/100) (100%) = mrp x (1 - margin_percentage/100) (100%, +-0.01) |
| 17 | `cost_price` | **Dependent** | GST-exclusive unit cost = landing_rate / (1 + tax_value/100) (100%) |
| 18 | `margin_percentage` | Independent · setting / status | Blinkit margin %, integer (7..25); = round((mrp - landing_rate)/mrp x 100) (100%) |
| 19 | `cess_value` | Independent · setting / status | cess RATE %, always 0 |
| 20 | `sgst_value` | Independent · setting / status | SGST RATE % (0 or 2.5), not an amount |
| 21 | `igst_value` | Independent · setting / status | IGST RATE % (0 or 5), filled together with CGST/SGST; not an amount |
| 22 | `cgst_value` | Independent · setting / status | CGST RATE % (0 or 2.5) |
| 23 | `tax_value` | **Dependent** | total GST RATE % = igst_value = cgst_value + sgst_value (100%); NOT igst+cgst+sgst. No tax AMOUNT column exists |
| 24 | `total_amount` | **Dependent** | line value incl. GST = units_ordered x landing_rate (100%, +-0.01) |
| 25 | `mrp` | Independent · setting / status | unit MRP, integer rupees (PO-time master data) |

## Invoices · `invoice`

32 columns · 392 rows in 8 files · data 2026-07-01 → 2026-09-09 · grain: `invoice_id`

A mutable snapshot: status and money fields change as invoices move DRAFT → VERIFIED → COMPLETED.

| # | Column | Status | Formula / note |
|---|---|---|---|
| 1 | `invoice_id` | Label | vendor invoice number, unique per row; 1 invoice per PO in these files |
| 2 | `invoice_date` | Label | YYYY-MM-DD; equals grn_date on 100% of rows |
| 3 | `invoice_status` | Independent · setting / status | DRAFT, VERIFIED, COMPLETED; mutable (DRAFT->VERIFIED/COMPLETED between runs) |
| 4 | `po_number` | Label | joins to PO report po_number (147/153) |
| 5 | `due_status` | Independent · setting / status | Paid, Overdue, Not Yet Due; Paid <=> payment_date present (99.3-100%); relative to download day |
| 6 | `due_date` | **Dependent** | = grn_date + credit_days (97.8-100%); can change when invoice leaves DRAFT |
| 7 | `credit_days` | Independent · setting / status | 3, 7 or 15 |
| 8 | `city_name` | Label | facility city |
| 9 | `facility_name` | Label | Blinkit facility; same names as PO report |
| 10 | `vendor_name` | Label | supplier |
| 11 | `buyer_name` | Label | Blinkit buying entity; literal double quotes as in PO report |
| 12 | `manufacturer_name` | Label | constant |
| 13 | `reject_reason` | Independent · setting / status | always blank in samples |
| 14 | `sku_quantity` | Independent · metric | distinct SKUs on the invoice (1-7); equals PO distinct items on ~75% |
| 15 | `invoice_amount_before_tax` | Independent · metric | Rs, GST-exclusive; blank for DRAFT |
| 16 | `invoice_amount_after_tax` | **Dependent** | Rs incl. GST; >= before_tax (100%); after/before - 1 is 0% or 5% or a blend (mixed-rate invoices); blank for DRAFT |
| 17 | `grn_date` | Label | YYYY-MM-DD; the report's date filter (Grn Date option) |
| 18 | `total_grn_amount` | **Dependent** | Rs received value at landing rate = sum over PO lines (units_ordered - remaining_quantity) x landing_rate (99%); float noise up to 12 decimals |
| 19 | `total_grn_quantity` | **Dependent** | units received = sum (units_ordered - remaining_quantity) of the PO (99%) |
| 20 | `total_dn_quantity` | Independent · metric | debit-note units; always 0 |
| 21 | `total_dn_amount` | Independent · metric | debit-note Rs; always 0 |
| 22 | `total_grn_difference` | Independent · metric | always 0.0 or blank (blank where price_variance blank) |
| 23 | `approved_amount` | **Dependent** | Rs Blinkit accepts; <= invoice_amount_after_tax (100%); = min(after_tax, grn_amount) only ~50% (line-level rule, not reproducible from this file); blank for DRAFT |
| 24 | `tds_amount` | **Dependent** | = round(0.1% x invoice_amount_before_tax, 2) (100%) - TDS u/s 194Q |
| 25 | `price_variance` | **Dependent** | Rs; approx after_tax - approved_amount (within Rs1 on ~68%); blank for DRAFT and some COMPLETED |
| 26 | `purchase_return_note` | Independent · metric | always 0.0 or blank |
| 27 | `incentive_on_sale` | Independent · metric | always blank |
| 28 | `advance_paid` | Independent · metric | always blank |
| 29 | `amount_payable` | **Dependent** | = approved_amount - tds_amount (100%) |
| 30 | `payment_date` | Independent · setting / status | 'YYYY-MM-DD 00:00:00+00:00'; blank until paid; usually 0-3 days before due_date |
| 31 | `payment_amount` | **Dependent** | = amount_payable (95.7-100%); blank until paid |
| 32 | `utr_number` | Label | bank transfer ref; shared by 1-7 invoices (one payment batch) - do not sum payment per UTR as if one invoice |

## Fees and charges · `fees`

17 columns · 0 rows in 8 files · data n/a · grain: `charge_id (assumed; no data rows)`

Header only in every file so far (no charges); statuses inferred from names, not measured.

| # | Column | Status | Formula / note |
|---|---|---|---|
| 1 | `charge_id` | Label | no data rows in any sample; status inferred from name only |
| 2 | `charge_type` | Label | no data rows in any sample; status inferred from name only |
| 3 | `charge_sub_type` | Label | no data rows in any sample; status inferred from name only |
| 4 | `created_at` | Label | no data rows in any sample; status inferred from name only |
| 5 | `billing_date` | Label | no data rows in any sample; status inferred from name only |
| 6 | `amount` | Independent · metric | no data rows in any sample; status inferred from name only |
| 7 | `operation` | Independent · setting / status | no data rows in any sample; status inferred from name only |
| 8 | `buyer_entity_name` | Label | no data rows in any sample; status inferred from name only |
| 9 | `status` | Independent · setting / status | no data rows in any sample; status inferred from name only |
| 10 | `facility_id` | Label | no data rows in any sample; status inferred from name only |
| 11 | `facility_name` | Label | no data rows in any sample; status inferred from name only |
| 12 | `reference_id` | Label | no data rows in any sample; status inferred from name only |
| 13 | `reference_type` | Label | no data rows in any sample; status inferred from name only |
| 14 | `purchase_orders` | Label | no data rows in any sample; status inferred from name only |
| 15 | `charge_dispute_sla_date` | Independent · setting / status | no data rows in any sample; status inferred from name only |
| 16 | `has_dispute` | Independent · setting / status | no data rows in any sample; status inferred from name only |
| 17 | `dispute_status` | Independent · setting / status | no data rows in any sample; status inferred from name only |

## Fill-rate scorecard (portal) · `scorecard`

32 columns · 1,055 rows in 6 files · data po_expiry → insert_dt_ist · grain: `po_number`, `item_id`

One week chosen by the portal; read the week from the data, not the manifest.

| # | Column | Status | Formula / note |
|---|---|---|---|
| 1 | `po_number` | Label | two formats: 18-char alphanumeric for 'Parent PO' rows (not in PO report/invoices) and 13-digit for 'Parent_PO' rows (join to PO report) |
| 2 | `po_type` | Label | 'Parent PO' or 'Parent_PO' - two spellings that mark two PO sources |
| 3 | `po_issue_date` | Label | 'YYYY-MM-DD 00:00:00.000' |
| 4 | `po_expiry_date` | Label | same format; defines the scorecard week (Mon..Mon) |
| 5 | `facility_id` | Label | 4-digit warehouse id (same id space as SOH backend_facility_id) |
| 6 | `facility_name` | Label | warehouse code-style name; differs from PO-report facility naming |
| 7 | `vendor_id` | Label | 5-digit; 5 vendors incl. distributors |
| 8 | `vendor_name` | Label | supplier |
| 9 | `city` | Label | Nagpur, Delhi, Pune, Raipur |
| 10 | `item_id` | Label | 8-digit |
| 11 | `product_name` | Label | Blinkit catalogue name (prefix differs from sales item_name) |
| 12 | `manufacturer_name` | Label | constant |
| 13 | `brand_name` | Label | constant |
| 14 | `l0_category` | Label | same values as sales.category |
| 15 | `l1_category` | Label | 7 values |
| 16 | `l2_category` | Label | 16 values |
| 17 | `po_qty` | Independent · metric | ordered units |
| 18 | `cost_price` | Independent · setting / status | unit cost excl. GST |
| 19 | `landing_price` | **Dependent** | = cost_price x (1 + GST) with GST 0% (92-98%) or 5% (100% of rows in {0,5,12,18,40}%; 99.4% in one file) |
| 20 | `grn_landing_price` | **Dependent** | blank when grn_qty=0; = landing_price on 91-100% of received rows |
| 21 | `po_value` | **Dependent** | = po_qty x landing_price (100%); float noise up to 13 decimals |
| 22 | `po_mrp` | Independent · setting / status | unit MRP, only filled for Parent_PO rows |
| 23 | `grn_mrp` | Independent · setting / status | unit MRP; filled on every row despite the name; = po_mrp where both exist |
| 24 | `po_status` | **Dependent** | line-level despite name: Serviced <=> grn_qty > 0 (100%), else Expired |
| 25 | `grn_id` | Label | filled only for Parent_PO rows; otherwise a single SPACE ' ', not empty |
| 26 | `grn_qty` | Independent · metric | received units; 0 when nothing received; <= po_qty (100%) |
| 27 | `grn_value` | **Dependent** | = grn_qty x grn_landing_price (100%); blank when grn_qty=0 |
| 28 | `grn_date` | Label | blank <=> grn_qty = 0 (100%) |
| 29 | `upc` | Label | 13-digit EAN |
| 30 | `insert_dt_ist` | Label | snapshot date (the Monday closing the week); single value per file |
| 31 | `item_status` | **Dependent** | from grn_qty vs po_qty (100%): Item Fully Serviced / Item Partially Serviced / Item Zero Fill - PO Not Delivered (no line of the PO received) / Item Zero Fill but PO Delivered |
| 32 | `new_po_status` | **Dependent** | PO-level rollup (100% of POs): PO Fully Serviced / PO Partially Serviced / Zero Fill PO |

## Fill-rate scorecard (email, rebuilt by us) · `scorecard_email`

18 columns · 64 rows in 3 files · data 2026-08-24 → 2026-09-07 · grain: `Summary: Field`, `facilities: Facilities (name; no id)`, `top_skus: Item Id`

Built by our prototype from the email body; the email itself is the raw source. Three sheets: Summary, facilities, top_skus.

| # | Column | Status | Formula / note |
|---|---|---|---|
| 1 | `Summary.Entity` | Label | business legal name (from mail subject) |
| 2 | `Summary.Period start` | Label | text YYYY-MM-DD |
| 3 | `Summary.Period end` | Label | text YYYY-MM-DD, Monday-to-Monday week |
| 4 | `Summary.Current Grade` | Independent · setting / status | text: Poor, Average (others unseen) |
| 5 | `Summary.Fill Rate` | **Dependent** | text '68.97%'; = sum grn_qty / sum po_qty of the portal scorecard CSV for the same week (verified exactly on 2026-08-24..08-31) |
| 6 | `Summary.Weighted Fill Rate Percent` | **Dependent** | text '%'; weighting unknown (not value-weighted, not reproducible from the CSV) |
| 7 | `Summary.Potential Loss` | **Dependent** | text '₹6,269'; = sum facilities.Potential Loss (exact) = sum top_skus.Potential Loss (within Rs1) |
| 8 | `Summary.Highest Rank In Category` | Independent · setting / status | text '3 (Dairy)': rank + category |
| 9 | `facilities.Facilities` | Label | warehouse name, no id |
| 10 | `facilities.City` | Label | city |
| 11 | `facilities.PO Fill Rate` | **Dependent** | integer % = round(100 x sum grn_qty / sum po_qty) per facility from the scorecard CSV (7/7 facilities) |
| 12 | `facilities.Weighted Fill Rate` | **Dependent** | integer %; method unknown |
| 13 | `facilities.Potential Loss` | Independent · metric | Rs, integer (rounded) |
| 14 | `top_skus.Item Id` | Label | 8-digit item id |
| 15 | `top_skus.UPC` | Label | 13-digit EAN |
| 16 | `top_skus.Item Name` | Label | name |
| 17 | `top_skus.Description` | Label | text |
| 18 | `top_skus.Potential Loss` | Independent · metric | Rs, 2 decimals; table lists only SKUs with loss > 0 (8 and 3 rows), so it sums to the total |

## Related

- Blinkit Ads columns: [blinkit-ads-columns.md](blinkit-ads-columns.md)
