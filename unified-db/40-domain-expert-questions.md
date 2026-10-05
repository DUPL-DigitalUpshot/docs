# Questions for the marketing / e-commerce expert

**Why we are asking.** We are building one dashboard that brings together ad results from Zepto, Blinkit, Instamart, Flipkart Minutes and later BigBasket. Each platform names and counts things differently. Before we add them together we need to know what each number really means to a brand manager. Short answers are fine. "Don't know, ask the platform" is a useful answer too.

Each question notes the parts of the design waiting on it.

**Numbering.** These are the **unified-db questions**. Inside `docs/unified-db/`, ❓Qn always means question n of this file. Anywhere else, cite them as **UQ-n** (for example UQ-10). They are unrelated to the PRD's open questions (PRD §12), which are cited as "PRD Q-n". The numbers are not in reading order, because they are stable references; there are no gaps (Q1–Q25).

## A. What matters most

**Q1.** When a brand manager opens the dashboard in the morning, which 6–10 numbers do they look at first? Which are "nice to have"?
*Unblocks:* the default dashboard tiles.

**Q10.** Which ways of slicing the data matter most? For example: by platform, campaign, ad type, keyword, search term, product, category or city. Please name the top 3.
For ad type, we plan to group each platform's own types into four house groups: *Search / Product listing*, *Recommendation*, *Banner / Display* and *Brand*. Do these groups make sense to clients?
*Unblocks:* which drill-downs we build first; whether daily search-term data is worth storing; the ad-type filter.

**Q13.** What are the standard comparisons: this week vs last week, this month vs last month, this year vs last year, or actual vs target? Do clients set targets?
*Unblocks:* the comparison options; whether we need a "targets" feature.

## B. What the numbers mean

**Q2.** When we say "ad revenue", which does the client mean?
- (a) sales of the advertised product only, or
- (b) the advertised product plus other products of the brand that were bought after the ad ("halo")?

Should it mean the same thing on every platform?
*Unblocks:* the headline Revenue and ROAS on every platform.

**Q3.** Instamart reports ad revenue three ways: a total, "direct within 7 days" and "direct within 14 days". Which one is our standard? Do you know what window Zepto, Blinkit and Flipkart use?
Until we know Instamart's total window, "revenue from other products" (total − direct) is shown as not available for Instamart, because the two numbers may use different windows.
*Unblocks:* Instamart revenue; comparing ROAS across platforms fairly.

**Q4.** Is ad revenue counted at MRP or at the selling price? With or without GST? Before or after returns and cancellations? Is this the same on every platform?
*Unblocks:* whether revenue can be compared across platforms at all.

**Q5.** Flipkart Minutes reports "Actions", which are add-to-basket events, instead of clicks. Should we treat them like clicks, like add-to-cart, or as their own thing?
*Unblocks:* Flipkart Minutes CTR, CPC and add-to-cart figures.

**Q6.** Blinkit shows three spend-like numbers: "Estimated Budget Consumed", "Claimables" and "served budget consumed". Which one is the amount the brand is actually billed? Is GST charged on top of the spend shown on any platform?

What the files show:
- "Claimables" always equals the **smaller** of "served budget consumed" and the campaign's total budget (693 of 693 rows). It looks like the budget-capped amount Blinkit can bill.
- The daily "Estimated Budget Consumed", added up over the month, equals "served budget consumed" within ₹1 for about 95% of campaigns. The exceptions are mostly **Product Booster** campaigns, where the daily figures add up to more (up to 45×).

So: is Claimables the billed amount? And why would Product Booster daily spend exceed what was served?
*Unblocks:* Blinkit spend, and therefore Blinkit ROAS.

**Q7.** Which names do clients expect: ROAS, ROI, ACOS, or something else? Zepto also shows "ROBA". Do you know what that measures? We can't work it out from the other columns.
*Unblocks:* labels on every chart; whether ROBA appears at all.

**Q8.** Which matters more to clients, **orders** or **units**? Is an "order" one basket, or one product line in a basket?
- On Zepto, "Orders" is often higher than "add to cart", so it may really be units.
- Instamart "conversions": are they orders?
- BigBasket "Orders (SKU)": orders or product lines?

*Unblocks:* the Orders tile, conversion rate and cost per order.

**Q9.** Is "new-to-brand customers" an important number? Blinkit gives a count. Zepto gives only a percentage, and it was always 0 in our files.
*Unblocks:* whether NTB is a headline KPI.

## C. Products and places

**Q11.** Do clients want to compare the *same product* across platforms ("my 1 kg atta on Zepto vs Blinkit")? If so, is the barcode (EAN) a reliable link, and who would keep the product list up to date?
*Unblocks:* the cross-platform product master (not in v1 unless needed).

**Q12.** Is there a standard list of cities we should use? Flipkart reports "business zones" instead of cities. Should these be mapped to cities, or kept separate?
*Unblocks:* the city filter and city charts.

## D. Timing and trust

**Q14.** Platforms change past numbers after the fact. How many days until a day's figures stop changing on each platform? What we measured by downloading the same days twice:
- **Blinkit:** only the last ~3 days change, by up to about ₹25 per campaign per day.
- **Instamart:** only the last ~3 days change, by up to about ₹90 per campaign per day.
- **Flipkart Minutes:** spend never changed, but revenue for a week grew by 13–20% between a pull the next day and one four days later, and was still changing when the day was over a week old.
- **Zepto:** not yet measured.

We plan to treat the last 5 days as "provisional" (14 days for Flipkart Minutes revenue). Does that match your experience? Do you know Flipkart's attribution window?
*Unblocks:* the "provisional" marker; how often we re-download history.

**Q15.** Should today and yesterday be marked "provisional"? Do weeks run Monday–Sunday or Sunday–Saturday? Are months calendar months?
*Unblocks:* weekly and monthly charts.

**Q18.** Before new data is shown to a client, should someone on our side check and approve it? Who? Or is automatic approval fine once a report has been reliable for a couple of weeks?
*Unblocks:* the approval step.

## E. Platform-specific

**Q19.** Blinkit offers a month-to-date "search report" and a separate dashboard download. When they disagree, which should we trust?
*Unblocks:* which Blinkit file feeds the dashboard.

**Q20.** Blinkit's "CTR" is unique clicks ÷ unique people reached, which is not the usual clicks ÷ impressions. Should we show Blinkit's own CTR, or show CTR as "not available" for Blinkit?
*Unblocks:* the CTR tile.

**Q21.** Blinkit files name the **manufacturer**, not the brand. When one manufacturer owns several brands that we manage separately, how should their Blinkit ads be split? By campaign name, by product, or by a list the client gives us? Or is one manufacturer always one client for us?
*Unblocks:* the Blinkit brand check; whether Blinkit data can be split across brands.

**Q22.** On BigBasket:
- Should spend on *awareness* campaigns (banners and bookings) count in the brand's overall ROAS, or be shown separately?
- Do clients care about BigBasket's split of sales into online vs offline?

*Unblocks:* BigBasket totals.

**Q23.** Instamart's most detailed report (campaign × day × ad type × keyword × product × city) adds up to **all** of the spend. An earlier "one third" figure came from a broken download. It is also the largest file we store (about 47 MB per brand per month). Which of its slices would clients actually use: keyword × city, product × city, or ad type × keyword? Is it worth keeping daily, or is weekly enough?
*Unblocks:* which Instamart drill-downs we build, and how often we download the detailed report.

**Q24.** Instamart reports "branded searches clicks". Do you know what this measures, and is it useful?
*Unblocks:* whether the metric appears.

**Q25.** Every Instamart export file name starts with `AUTO_`. Is that the campaign type (automatic campaigns), the export mode, or something else? If there are non-`AUTO_` exports (for example manual campaigns), we are missing them.
*Unblocks:* whether the Instamart catalogue is complete.

## F. Users and outputs

**Q16.** Should a client ever see how their brand compares with brands they don't own (an anonymous benchmark)? We assume **never** unless you say otherwise.

**Q17.** After looking at the dashboard, what do clients need: an Excel download, a PDF, or a scheduled email?
