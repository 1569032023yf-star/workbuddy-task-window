# BD Tonight Pre-Send Report — 2026-08-03 21:30 CST

**Batch:** `new_outreach_20260803_et1000`  
**Mode:** Read-only plan creation (NO SMTP)  
**Follow-up:** 0  

---

## Summary

| Metric | Value |
|--------|-------|
| Raw eligible (TN/AR/KY, unsent) | 13 orgs |
| Rejected (invalid email) | 4 |
| **Final plan entries** | **9** |
| Strict A0 | 1 |
| Broad Outreach | 8 |

## Rejected Leads

| # | Store | State | Reason |
|---|-------|-------|--------|
| 1 | Wildkin | TN | `claudebot@anthropic.com` — Anthropic bounce trap |
| 2 | Dilly Dally's Toy Store | AR | `download_23_235x235@2x.jpg` — image filename, not email |
| 3 | Dilly Dallys Toy Store | AR | `certificate1_235x235@2x.jpg` — image filename, not email |
| 4 | Kentucky Fried Gaming | KY | `13e49d...@sentry.io` — Sentry error tracking, not business |

## Final Send Plan (9 entries)

| # | State | Tier | Store | Email | Template |
|---|-------|------|-------|-------|----------|
| 01 | TN | **A0** | Purple Butterfly Kids | info@purplebutterflykids.com | retail_distributor (ccb51505) |
| 02 | TN | Broad | Next Level Games | customers@tnlg.net | retail_distributor (ccb51505) |
| 03 | TN | Broad | Storehouse no 9 | help@storehouseno9.com | **custom_printing** (5893dbc9) |
| 04 | TN | Broad | Vintage to Modern Toys | hothtoys@gmail.com | retail_distributor (ccb51505) |
| 05 | TN | Broad | The Game Piece | daltong@thegamepiece.net | retail_distributor (ccb51505) |
| 06 | TN | Broad | Karz&Dollz Toy Shop | karzndollztoyshop@gmail.com | retail_distributor (ccb51505) |
| 07 | TN | Broad | Geeks Etc Video Games | geeksetc@lighttube.net | retail_distributor (ccb51505) |
| 08 | AR | Broad | The Toy Store Gifts and More | www.kll@toystoreandgifts.com | **custom_printing** (5893dbc9) |
| 09 | AR | Broad | Steadfast Hobbies Hot Springs | steadfasthobbies@gmail.com | retail_distributor (ccb51505) |

## Template Distribution

- **retail_distributor_v5_locked** (ccb51505): 7 — game/toy/hobby/children's stores
- **custom_printing_production_v5_locked** (5893dbc9): 2 — gift shops

## Authorization

- **ID:** `auth_2026-08-03_ab777bd5`
- **Plan:** `2026-08-03:new_outreach:3939af2047`
- **Status:** active
- **Expires:** 2026-08-03 23:59:59 CST
- **Entries:** 9 (all authorized)
- **Tracking tokens:** 9 (email_tracking_messages created)

## State Breakdown

| State | A0 | Broad | Total |
|-------|-----|-------|-------|
| TN | 1 | 6 | 7 |
| AR | 0 | 2 | 2 |
| KY | 0 | 0 | 0 |
| **Total** | **1** | **8** | **9** |

## Routing Note

Storehouse no 9 (`home decor / gift shop`) was manually re-routed from `retail_distributor` to `custom_printing_production` — the `route_template_for_lead()` heuristic only checks `store_name` for keywords (not composite `store_type`), missing "Storehouse no 9" as a gift shop.
