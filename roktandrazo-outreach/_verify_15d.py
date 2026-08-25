import sqlite3, os
from datetime import datetime, date
conn = sqlite3.connect(os.path.join("data","bd_leads.db")); conn.row_factory=sqlite3.Row
def dt(s):
    if not s: return None
    s = str(s).strip().replace("T"," ")
    try: return datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError: return None
W0=date(2026,8,4); W1=date(2026,8,18)

# window sends by email + lead
sends=[]
for r in conn.execute("SELECT id,lead_id,email,status,sent_at,smtp_accepted_at,error_message FROM send_log"):
    d=dt(r["sent_at"])
    if d and W0<=d.date()<=W1:
        sends.append({"id":r["id"],"lead_id":r["lead_id"],"email":(r["email"] or "").lower().strip(),
                      "day":d.date(),"status":r["status"],"acc":bool(r["smtp_accepted_at"]),
                      "err":r["error_message"]})
email_day = {}
for s in sends: email_day[s["email"]] = s["day"]
lead_day = {}
for s in sends: lead_day[s["lead_id"]] = s["day"]
print("window send rows:", len(sends))
for d in sorted({s['day'] for s in sends}):
    print("  ", d, sum(1 for s in sends if s['day']==d), "emails")
print("errors non-null:", sum(1 for s in sends if s["err"]))
print("accepted flag:", sum(1 for s in sends if s["acc"]))

# ambiguous bounce emails check membership
amb = ["info@gameuniverse.com","info@djhobbytoys.com","info@pulpfictioncomics.com","melissa@replaytoys.com"]
for e in amb:
    print(f"  {e:32s} in-window-send? {e in email_day} -> day {email_day.get(e)}")

# bounce set keyed by email (dedup), attributed by send_log email match else DSN date
bounce=[]
for r in conn.execute("SELECT email,bounce_received_at,diagnostic_code FROM bounce_log"):
    d=dt(r["bounce_received_at"])
    e=(r["email"] or "").lower().strip()
    bounce.append({"email":e,"send_day":email_day.get(e),"recv_day":d.date() if d else None,
                   "diag":(r["diagnostic_code"] or "")[:60],"src":"bounce_log"})
for r in conn.execute("SELECT original_recipient,original_sent_at,diagnostic_code FROM unmatched_dsn"):
    d=dt(r["original_sent_at"])
    e=(r["original_recipient"] or "").lower().strip()
    bounce.append({"email":e,"send_day":email_day.get(e) or (d.date() if d else None),
                   "recv_day":None,"diag":(r["diagnostic_code"] or "")[:60],"src":"dsn"})
seen=set(); bd=[]
for b in bounce:
    if b["email"] in seen: continue
    seen.add(b["email"]); bd.append(b)
print("\n=== UNIQUE bounces, attributed to send day ===")
for d in [date(2026,8,4+i) for i in range(15)]:
    bs=[b for b in bd if b["send_day"]==d]
    if bs:
        print(f"{d}: {len(bs)}")
        for b in bs: print(f"     {b['src']:11s} {b['email'][:44]:44s} recv={b['recv_day']} {b['diag'][:44]}")
un= [b for b in bd if b["send_day"] is None]
print("unattributed:", len(un))
for b in un: print("   ", b["email"], b["recv_day"], b["diag"][:40])

# unsubscribe / suppression timing
print("\nunsubscribe_request row:")
for r in conn.execute("SELECT email,reason,added_at FROM suppression_list WHERE reason LIKE '%unsubscribe%'"):
    print("   ", dict(r))
conn.close()
