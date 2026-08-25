import sqlite3, os
from datetime import datetime, date
conn = sqlite3.connect(os.path.join("data","bd_leads.db")); conn.row_factory=sqlite3.Row

def dt(s):
    if not s: return None
    s = str(s).strip().replace("T"," ")
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M:%S.%f","%Y-%m-%d","%Y-%m-%d %H:%M"):
        try: return datetime.strptime(s[:19], fmt)
        except ValueError: pass
    return None

W0 = date(2026,8,4); W1 = date(2026,8,18)

# 1) send_log
sends = []
for r in conn.execute("SELECT id,lead_id,email,status,error_message,sent_at,smtp_accepted_at,message_type,template_id,batch_id FROM send_log"):
    d = dt(r["sent_at"])
    if d and W0 <= d.date() <= W1:
        sends.append({"id":r["id"],"lead_id":r["lead_id"],"email":r["email"],"status":r["status"],
                      "day":d.date(),"accepted":bool(r["smtp_accepted_at"]),"mt":r["message_type"],
                      "tmpl":r["template_id"],"batch":r["batch_id"]})
send_by_id = {s["id"]: s for s in sends}
lead_latest_day = {}
for s in sends:
    lead_latest_day.setdefault(s["lead_id"], s["day"])  # first in list order = earliest; we want latest send
# rebuild latest: order sends by sent_at ascending, take last per lead
sends_sorted = sorted(sends, key=lambda s: (s["day"], s["id"]))
lead_latest_day = {}
for s in sends_sorted:
    lead_latest_day[s["lead_id"]] = s["day"]

# 2) bounce_log
bounces = []
for r in conn.execute("SELECT id,lead_id,email,bounce_received_at,status_code,diagnostic_code,bounce_type FROM bounce_log"):
    d = dt(r["bounce_received_at"])
    day_send = lead_latest_day.get(r["lead_id"]) if r["lead_id"] else None
    bounces.append({"src":"bounce_log","email":r["email"],"lead_id":r["lead_id"],
                    "recv_day": d.date() if d else None,
                    "send_day": day_send, "diag":(r["diagnostic_code"] or "")[:50]})

# 3) unmatched_dsn
for r in conn.execute("SELECT id,original_recipient,original_sent_at,detected_at,diagnostic_code,matched_send_log_id,notes FROM unmatched_dsn"):
    d = dt(r["original_sent_at"]); det = dt(r["detected_at"])
    day_send = d.date() if d else (det.date() if det else None)
    bounces.append({"src":"unmatched_dsn","email":r["original_recipient"],"lead_id":None,
                    "recv_day": det.date() if det else None, "send_day": day_send,
                    "diag":(r["diagnostic_code"] or "")[:50]})

# dedup: same email + same send_day keep one (bounce_log preferred)
seen=set(); bd=[]
for b in bounces:
    key=(str(b["email"]).lower(), b["send_day"])
    if key in seen: continue
    seen.add(key); bd.append(b)

# per-day counts
def cnt(fn): return sum(1 for b in bd if fn(b))
print("=== BOUNCES attributed by SEND day (8/4-8/18) ===")
for b in sorted(bd, key=lambda x: str(x["send_day"])):
    print(f"   send_day={b['send_day']} recv={b['recv_day']} src={b['src']:13s} {str(b['email'])[:42]:42s} {b['diag']}")
print(f"\nTotal dedup bounces (window, by send-day): {len(bd)}")

print("\n=== DAILY TABLE ===")
d0 = date(2026,8,4)
from collections import defaultdict
by_day = defaultdict(list)
for s in sends: by_day[s["day"]].append(s)
for i in range(15):
    d = date(2026,8,4+i)
    sl = by_day[d]
    sent_n = len(sl)
    acc_n = sum(1 for s in sl if s["accepted"] or s["status"]=="sent")
    bnc_n = sum(1 for b in bd if b["send_day"]==d)
    rp = 0
    print(f"{d}  sent={sent_n}  accepted={acc_n}  bounce={bnc_n}")

print("\n=== 8/14 batch detail ===")
b14 = [s for s in sends if s["day"]==date(2026,8,14)]
print("send rows:", len(b14), "accepted:", sum(1 for s in b14 if s["accepted"]))
bn14 = [b for b in bd if b["send_day"]==date(2026,8,14)]
print("bounces(15d):", len(bn14))
for b in bn14: print("   ", b["email"], "|", b["diag"], "| recv", b["recv_day"])

print("\n=== 8/5 batch detail ===")
b5 = [s for s in sends if s["day"]==date(2026,8,5)]
print("send rows:", len(b5), "accepted_flag:", sum(1 for s in b5 if s["accepted"]), "status_sent:", sum(1 for s in b5 if s["status"]=="sent"))
print("mt:", set(s["mt"] for s in b5), "tmpl:", set(s["tmpl"] for s in b5))
bn5 = [b for b in bd if b["send_day"]==date(2026,8,5)]
print("bounces:", len(bn5))
for b in bn5: print("   ", b["email"], "|", b["diag"])

print("\n=== reply_log in window ===")
for r in conn.execute("SELECT * FROM reply_log"):
    d = dt(r["reply_received_at"])
    print(f"   id={r['id']} {r['email']} day={d.date() if d else None} type={r['reply_type']} summary={r['summary']}")

print("\n=== suppression added in window ===")
for r in conn.execute("SELECT email,reason,added_at FROM suppression_list"):
    d = dt(r["added_at"])
    if d and W0 <= d.date() <= W1:
        print(f"   {d.date()} {r['reason'][:36]:36s} {r['email']}")

print("\n=== leads status set in window (sent->bounced etc) ===")
for r in conn.execute("SELECT id,store_name,status FROM leads WHERE status IN ('bounced','do_not_contact','unsubscribed','replied')"):
    print("   ", dict(r))
conn.close()
