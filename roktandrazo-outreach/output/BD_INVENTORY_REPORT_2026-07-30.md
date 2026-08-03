# BD Inventory Report — 2026-07-30 15:00 Asia/Shanghai

## Strict A0 Organizations

| Metric | Value |
|--------|-------|
| Unsent A0 Locations | **0** |
| Unsent A0 Organizations | **0** |
| Target | 120 |
| Gap | 120 |

**Status: CRITICAL** — pool completely drained. 3 A0 leads sent 2026-07-29 (B Side Games #316, Sunny Toys #531, The Great Escape #671) and excluded by send_log gate. No new A0 leads available for tonight's send.

## Organization Outreach Opportunities (Broad Outreach)

| Metric | Count |
|--------|-------|
| Broad Ready Locations | 99 |
| Broad Ready Organizations | 99 |
| **Org Outreach Opportunities** | **99** |
| Contact Form Only | 20 |
| Exception Review (no email) | 142 |
| Contact Recovery Pending | 0 |

## City Queue

| # | City | State | Priority | Status |
|---|------|-------|----------|--------|
| 1 | Nashville | TN | 1 | search_matrix_exhausted ✅ |
| 2 | **Memphis** | **TN** | **2** | **active** ← |
| 3 | Knoxville | TN | 3 | pending |
| 4 | Little Rock | AR | 10 | pending |
| 5 | Fayetteville | AR | 11 | pending |
| 6 | Louisville | KY | 20 | pending |
| 7 | Lexington | KY | 21 | pending |

Nashville work complete. Memphis is the active city.

## Blocked Breakdown

| Reason | Count |
|--------|-------|
| Previously sent | 362 |
| Permanently blocked | 7 |
| Invalid email excluded | 13 |
| Org key patched | 579 |
| Contact role uncertain → unblocked | 99 |

## Near-A0 Candidates (manual upgrade potential)

18 leads are confidence A/B with emails but auto_sendable=0:

**10 have bad/unusable emails** (sentry/wixpress, image filenames, placeholder, anthropic bot):
- #594 Bandit Board Games → sentry.wixpress.com
- #310 The Bend Store → .png filename
- #414 Dilly Dally's Toy Store → .jpg filename
- #25 Palmetto Puzzle Works → sentry.wixpress.com
- #432 Kentucky Fried Gaming → sentry.io
- #44 Christys Toy Outlet → .jpg filename
- #47 Eugene Toy and Hobby → .png filename
- #15 Alphabet Soup → xxx@xxx.xxx
- #569 Wildkin → anthropic.com
- #551 Dilly Dallys Toy Store → .jpg filename

**8 have real emails that could be upgraded to A0 if evidence chain is completed:**
- #356 Old Fox Books → booksrock@oldfoxbooks.com
- #29 The Acadia Shops → shop@acadiashops.com
- #320 Quarterstaff Games → diane@sevendaysvt.com
- #27 Thinker Toys (Carmel) → carmel@thinkertoys.com
- #31 Packrat's Paradise → PackratsParadiseES@gmail.com
- #339 Hopscotch Childrens Store → info@hopscotchstore.com
- #417 The Toy Store Gifts and More → www.kll@toystoreandgifts.com (malformed)
- #541 Mammoth Cave NP Store → customercare@easternnational.org

## B-Grade Leads — No Email (11 total)

All 11 B-grade leads in AR/TN have no email AND no official_website URL. These were collected as bulk discovery hits without website verification.

## Discovery Pipeline

- **Lane A (Google Places)**: configuration_blocked — API key not configured
- **Staging postprocess**: empty — no unprocessed results
- **Memphis contact_form_pool**: 1 candidate (Memphis Toy Exchange #529) — no email found

## Orchestrator Run Summary

- Stage: `python bd_orchestrator.py --stage inventory --live`
- Active city: Memphis, TN
- Lane A discovery: configuration_blocked
- Staging B/C/D: staging_postprocess_empty
- 5 loops × 1 candidate from Memphis contact_form_pool → 0 emails recovered
- Final A0: 0/120, gap: 120
- Job run: `inventory:2026-07-30:bc140633` → partial (max_loops_reached)

## Blockers

1. **Google Places API** not configured → no new place discovery
2. **Astrill VPN proxy** SSL errors prevent website scraping for email recovery
3. **Lead Factory** not producing evidence_snippet during collection
4. **send_log duplicate bug** → lead status not updated after send; A0 leads incorrectly appear as "new"
