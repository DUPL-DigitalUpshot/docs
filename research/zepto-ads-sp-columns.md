# Zepto Ads — Sponsored Products: columns per report

The columns of each Zepto Sponsored Products report, in file order, exactly as Zepto writes them.

- **Source:** the stored header rows (`report_files.header_row`) of the latest file per report.
- **Brand:** Dinshaw's, the only brand with Zepto files so far.
- **Stability:** each report has had one header layout across all of its stored files.
- **Captured:** 2026-10-05.

| Report | Key | Columns | Files checked |
|---|---|---|---|
| [Campaign](#campaign-performance) | `zepto.ads:sp.campaign_performance` | 21 | 20 |
| [Category](#category-performance) | `zepto.ads:sp.category_performance` | 17 | 18 |
| [City](#city-performance) | `zepto.ads:sp.city_performance` | 15 | 24 |
| [Keyword](#keyword-performance) | `zepto.ads:sp.keyword_performance` | 19 | 17 |
| [Page](#page-performance) | `zepto.ads:sp.page_performance` | 15 | 18 |
| [Product](#product-performance) | `zepto.ads:sp.product_performance` | 20 | 17 |

## Campaign performance

`zepto.ads:sp.campaign_performance` · 21 columns

| # | Column |
|---|---|
| 1 | `CampaignName` |
| 2 | `BrandID` |
| 3 | `BrandName` |
| 4 | `CampaignType` |
| 5 | `Atc` |
| 6 | `Clicks` |
| 7 | `Cpc` |
| 8 | `Cpm` |
| 9 | `Daily_budget` |
| 10 | `Impressions` |
| 11 | `New_to_brand_user_percentage` |
| 12 | `Orders` |
| 13 | `Other_skus` |
| 14 | `Revenue` |
| 15 | `Roas` |
| 16 | `Robas` |
| 17 | `Same_skus` |
| 18 | `Spend` |
| 19 | `Status` |
| 20 | `Unique_considerations` |
| 21 | `Unique_reach` |

## Category performance

`zepto.ads:sp.category_performance` · 17 columns

| # | Column |
|---|---|
| 1 | `BrandID` |
| 2 | `BrandName` |
| 3 | `Atc` |
| 4 | `Campaign_id` |
| 5 | `Campaign_name` |
| 6 | `Category` |
| 7 | `Clicks` |
| 8 | `Cpc` |
| 9 | `Cpm` |
| 10 | `Impressions` |
| 11 | `Orders` |
| 12 | `Other_skus` |
| 13 | `Revenue` |
| 14 | `Roas` |
| 15 | `Robas` |
| 16 | `Same_skus` |
| 17 | `Spend` |

## City performance

`zepto.ads:sp.city_performance` · 15 columns

| # | Column |
|---|---|
| 1 | `CityName` |
| 2 | `BrandID` |
| 3 | `BrandName` |
| 4 | `Atc` |
| 5 | `Clicks` |
| 6 | `Cpc` |
| 7 | `Cpm` |
| 8 | `Impressions` |
| 9 | `Orders` |
| 10 | `Other_skus` |
| 11 | `Revenue` |
| 12 | `Roas` |
| 13 | `Robas` |
| 14 | `Same_skus` |
| 15 | `Spend` |

## Keyword performance

`zepto.ads:sp.keyword_performance` · 19 columns

| # | Column |
|---|---|
| 1 | `KeywordName` |
| 2 | `KeywordMatchType` |
| 3 | `BrandID` |
| 4 | `BrandName` |
| 5 | `Atc` |
| 6 | `Campaign_id` |
| 7 | `Campaign_name` |
| 8 | `Clicks` |
| 9 | `Cpc` |
| 10 | `Cpm` |
| 11 | `Ctr` |
| 12 | `Impressions` |
| 13 | `Orders` |
| 14 | `Other_skus` |
| 15 | `Revenue` |
| 16 | `Roas` |
| 17 | `Robas` |
| 18 | `Same_skus` |
| 19 | `Spend` |

## Page performance

`zepto.ads:sp.page_performance` · 15 columns

| # | Column |
|---|---|
| 1 | `PageName` |
| 2 | `BrandID` |
| 3 | `BrandName` |
| 4 | `Atc` |
| 5 | `Clicks` |
| 6 | `Cpc` |
| 7 | `Cpm` |
| 8 | `Impressions` |
| 9 | `Orders` |
| 10 | `Other_skus` |
| 11 | `Revenue` |
| 12 | `Roas` |
| 13 | `Robas` |
| 14 | `Same_skus` |
| 15 | `Spend` |

## Product performance

`zepto.ads:sp.product_performance` · 20 columns

| # | Column |
|---|---|
| 1 | `ProductID` |
| 2 | `ProductName` |
| 3 | `BrandID` |
| 4 | `BrandName` |
| 5 | `Atc` |
| 6 | `Campaign_id` |
| 7 | `Campaign_name` |
| 8 | `Category` |
| 9 | `Clicks` |
| 10 | `Cpc` |
| 11 | `Cpm` |
| 12 | `Ctr` |
| 13 | `Impressions` |
| 14 | `Orders` |
| 15 | `Other_skus` |
| 16 | `Revenue` |
| 17 | `Roas` |
| 18 | `Robas` |
| 19 | `Same_skus` |
| 20 | `Spend` |

## Not included

- **Sponsored Brands and Sponsored Display:** no real file has been stored yet, so their columns are unverified.
- **Meaning, types and mapping of each column:** see [zepto-ads-schema.md](zepto-ads-schema.md).
