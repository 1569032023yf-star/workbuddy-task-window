import sqlite3, os
from datetime import datetime, date
conn = sqlite3.connect(os.path.join("data","bd_leads.db")); conn.row_factory=sqlite3.Row
def dt(s):
    if not s: return None
    s = str(s).strip().replace("T"," ")
    try: return datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError: return None
W0=date(2026,8,4); W1=date(2026,8,18)

sends=[]
for r in conn.execute("SELECT id,lead_id,email,status,sent_at,smtp_accepted_at,error_message FROM send_log"):
    d=dt(r["sent_at"])
    if d and W0<=d.date()<=W1:
        sends.append({"day":d.date(),"email":(r["email"] or "").lower().strip(),
                      "acc":bool(r["smtp_accepted_at"]),"status":r["status"],"err":r["error_message"]})
email_day={}
for s in sends: email_day[s["email"]]=s["day"]

bounces=[]
for r in conn.execute("SELECT email,bounce_received_at,diagnostic_code FROM bounce_log"):
    d=dt(r["bounce_received_at"])
    bounces.append({"email":(r["email"] or "").lower().strip(),
                    "send_day":email_day.get((r["email"] or "").lower().strip()),
                    "recv":d.date() if d else None,"diag":(r["diagnostic_code"] or "")[:40]})
for r in conn.execute("SELECT original_recipient,original_sent_at,detected_at,diagnostic_code FROM unmatched_dsn"):
    d=dt(r["original_sent_at"]); det=dt(r["detected_at"])
    e=(r["original_recipient"] or "").lower().strip()
    bounces.append({"email":e,"send_day":email_day.get(e) or (d.date() if d else None),
                    "recv":det.date() if det else None,"diag":(r["diagnostic_code"] or "")[:40]})
seen=set(); bd=[]
for b in bounces:
    if b["email"] in seen: continue
    seen.add(b["email"]); bd.append(b)

print("=== DAILY 8/4-8/18 (fresh) ===")
t_sent=t_acc=t_bnc=0
for i in range(15):
    d=date(2026,8,4+i)
    sl=[s for s in sends if s["day"]==d]
    sent=len(sl); acc=sum(1 for s in sl if s["acc"] or s["status"]=="sent")
    bnc=sum(1 for b in bd if b["send_day"]==d)
    t_sent+=sent; t_acc+=acc; t_bnc+=bnc
    rate = f"{bnc/sent*100:.1f}%" if sent else "–"
    print(f"{d}  sent={sent}  accepted={acc}  bounce={bnc}  rate={rate}")
print(f"\nTOTALS sent={t_sent} accepted={t_acc} bounce={t_bnc} rate={t_bnc/t_sent*100:.1f}%")

print("\n=== OOO / REPLY / UNSUB in window ===")
for r in conn.execute("SELECT reply_received_at,reply_type,email FROM reply_log"):
    d=dt(r["reply_received_at"])
    print(f"  reply_log: {r['email']} {r['reply_type']} day={d.date() if d else None} (in-window={bool(d and W0<=d.date()<=W1)})")
for r in conn.execute("SELECT email,reason,added_at FROM suppression_list WHERE reason LIKE '%unsubscribe%'"):
    d=dt(r["added_at"])
    print(f"  unsub: {r['email']} day={d.date() if d else None} (in-window={bool(d and W0<=d.date()<=W1)})")

print("\n=== 8/18 today ===")
for s in sends:
    if s["day"]==W1: print("  ", s)
conn.close()
