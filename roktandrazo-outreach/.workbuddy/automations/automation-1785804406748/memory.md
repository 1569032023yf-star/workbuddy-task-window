# BD Production Pre-Send Automation Memory

## 2026-08-05 21:26 CST — NO_BATCH_TODAY
- **Batch:** `new_outreach_20260805_et1000`
- **Snapshot:** `frozen_new_outreach_20260805_et1000.json` — NOT FOUND
- **Result:** NO_BATCH_TODAY — no 21:10 freeze snapshot exists for today
- **Orgs:** 0 (clean exit)
- **preflight_status:** `no_batch`
- **Script:** `_pre_send_plan_tonight.py`
- **Report:** `output/pre_send_report_2026-08-05_2126.md`

## 2026-08-04 21:30 CST — SUCCESS
- **Batch:** `new_outreach_20260804_et1000`
- **Snapshot:** `frozen_new_outreach_20260804_et1000.json` (count=40, frozen 18:40)
- **Result:** 30 orgs selected, Final Send Plan created
- **Auth:** `auth_new_outreach_20260804_et1000_0e41d38a2f225535`
- **States:** TN=4, CA=5, WI=4, UT=3, NY=2, OR=2, NC=2, AZ=2, AR=1, WA/MA/MN/PA/GA=1 each
- **KY=0** (all 7 KY unsent leads were already-sent orgs)
- **Templates:** 29 retail, 1 custom
- **Follow-up:** 0
- **SMTP:** 0 (pre-send only, no SMTP)
- **preflight_status:** `planned`
- **Skipped:** 20 invalid (contact_form_pool), 5 suppressed/bounced, 52 already-sent orgs
- **Script:** `_pre_send_plan_tonight.py`
- **Report:** `output/pre_send_report_2026-08-04_2129.md`
