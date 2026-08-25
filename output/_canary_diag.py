import sqlite3
from collections import Counter
DB=r'C:/Users/15690/WorkBuddy/2026-06-05-15-31-42/roktandrazo-outreach/data/bd_leads.db'
c=sqlite3.connect(DB); cur=c.cursor()
cur.execute("""SELECT fsp.id, fsp.lead_id, fsp.recipient_email, l.evidence_url, l.evidence_snippet,
                      l.email_verified_on_official_site, l.mx_provider, l.recipient_timezone, l.timezone_status,
                      l.sent_at
               FROM final_send_plan fsp JOIN leads l ON l.id=fsp.lead_id
               WHERE fsp.outreach_batch_date='2026-08-20' AND fsp.status='planned'""")
rows=cur.fetchall()
cols=[d[0] for d in cur.description]
cur.execute("SELECT DISTINCT lead_id FROM send_log"); sent=set(r[0] for r in cur.fetchall())
cur.execute("SELECT email FROM suppression_list"); supp=set(r[0].lower() for r in cur.fetchall())
domains=Counter((r[2] or '').split('@')[-1] for r in rows)

n=len(rows)
def rate(name, pred):
    cnt=sum(1 for r in rows if pred(r))
    print(f"  {name:28s}: {cnt}/{n} pass")
    return cnt

c_official=lambda r: bool(r[3]) and bool(r[4]) and r[5]==1
c_mx=lambda r: bool(r[6])
c_tz=lambda r: bool(r[7]) and r[8] not in (None,'TIMEZONE_UNRESOLVED','unresolved')
c_unsent=lambda r: r[9] is None and r[1] not in sent
c_nosupp=lambda r: (r[2] or '').lower() not in supp
c_nodup_batch=lambda r: domains[(r[2] or '').split('@')[-1]]==1

print(f"Total planned FSPs: {n}\nPer-criterion pass rates:")
rate("official_evidence", c_official)
rate("mx_pass(proxy)", c_mx)
rate("timezone_resolved", c_tz)
rate("unsent", c_unsent)
rate("not_suppressed", c_nosupp)
rate("no_dup_in_batch", c_nodup_batch)

all_ok=sum(1 for r in rows if c_official(r) and c_mx(r) and c_tz(r) and c_unsent(r) and c_nosupp(r) and c_nodup_batch(r))
print(f"\nALL-SIX pass: {all_ok}")

# Relaxed: ignore in-batch dup (dup = previously sent only)
relaxed=sum(1 for r in rows if c_official(r) and c_mx(r) and c_tz(r) and c_unsent(r) and c_nosupp(r))
print(f"Relaxed (allow in-batch domain dup): {relaxed}")

# Show up to 5 leads passing official+mx+tz+unsent+nosupp (ignore batch dup) with their domain dup count
print("\nSample relaxed-pass leads (official+mx+tz+unsent+nosupp):")
shown=0
for r in rows:
    if c_official(r) and c_mx(r) and c_tz(r) and c_unsent(r) and c_nosupp(r):
        dom=(r[2] or '').split('@')[-1]
        print(f"  fsp={r[0]} lead={r[1]} {r[2]} mx={r[6]} tz={r[7]} dom_dups_in_batch={domains[dom]}")
        shown+=1
        if shown>=8: break
