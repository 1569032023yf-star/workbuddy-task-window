import sqlite3, os
conn = sqlite3.connect(os.path.join("data","bd_leads.db")); conn.row_factory=sqlite3.Row
P = "status='manual_review_needed'"

print("=== MANUAL_POOL_TOTAL ===")
print(" ", conn.execute(f"SELECT COUNT(*) c FROM leads WHERE {P}").fetchone()["c"])

print("\n=== BY review_reason_code ===")
for r in conn.execute(f"SELECT COALESCE(NULLIF(review_reason_code,''),'(empty)') rc, COUNT(*) c FROM leads WHERE {P} GROUP BY rc ORDER BY c DESC"):
    print(f"  {r['rc']:<34} {r['c']}")

print("\n=== ICP classification (icp_route / icp_priority) ===")
try:
    for r in conn.execute(f"SELECT COALESCE(icp_route,'UNSET') route, COALESCE(icp_priority,'UNSET') pri, COUNT(*) c FROM leads WHERE {P} GROUP BY route, pri ORDER BY c DESC"):
        print(f"  route={r['route']:<14} pri={r['pri']:<8} {r['c']}")
except Exception as e:
    print("  (no icp columns)", str(e)[:50])

print("\n=== overlaps ===")
sent = conn.execute(f"SELECT COUNT(*) c FROM leads WHERE {P} AND id IN (SELECT lead_id FROM send_log WHERE status='sent')").fetchone()["c"]
bounced = conn.execute(f"SELECT COUNT(*) c FROM leads WHERE {P} AND (status='bounced' OR id IN (SELECT lead_id FROM bounce_log))").fetchone()["c"]
supp = conn.execute(f"SELECT COUNT(*) c FROM leads WHERE {P} AND email IS NOT NULL AND email!='' AND email IN (SELECT email FROM suppression_list)").fetchone()["c"]
duporg = conn.execute(f"SELECT COUNT(*) c FROM leads WHERE {P} AND organization_key IS NOT NULL AND organization_key!='' AND organization_key IN (SELECT organization_key FROM leads WHERE status='sent' AND organization_key IS NOT NULL AND organization_key!='')").fetchone()["c"]
dupdom = conn.execute(f"SELECT COUNT(*) c FROM leads WHERE {P} AND domain_hash IN (SELECT domain_hash FROM leads WHERE status='sent' AND domain_hash IS NOT NULL)").fetchone()["c"]
noemail = conn.execute(f"SELECT COUNT(*) c FROM leads WHERE {P} AND (email IS NULL OR email='')").fetchone()["c"]
hasweb = conn.execute(f"SELECT COUNT(*) c FROM leads WHERE {P} AND official_website IS NOT NULL AND official_website!=''").fetchone()["c"]
print(f"  already_sent (lead in send_log sent) : {sent}")
print(f"  bounced (status or bounce_log)       : {bounced}")
print(f"  suppressed (email in suppression)    : {supp}")
print(f"  duplicate org (org_key= sent org)    : {duporg}")
print(f"  duplicate domain (domain_hash=sent)  : {dupdom}")
print(f"  no email at all                      : {noemail}")
print(f"  has official_website                 : {hasweb}")

print("\n=== contact_form_pool ===")
print(" ", conn.execute("SELECT COUNT(*) c FROM leads WHERE status='contact_form_pool'").fetchone()["c"])
conn.close()
