import os, sys, sqlite3
from datetime import datetime
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
def _load_env(p):
    try:
        for line in open(p, encoding="utf-8"):
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,v=line.split("=",1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError: pass
_load_env(os.path.join(BASE,".env"))

conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory=sqlite3.Row

print("=== 1) TODAY-NEW LEADS (collected_at or last_checked_at = 2026-08-18) ===")
rows = conn.execute("""SELECT id,store_name,city,state,email,email_source_type,
    email_verified_on_official_site,organization_key,recipient_timezone,timezone_status,
    mx_provider,auto_sendable,status,confidence_score,collected_at,last_checked_at
    FROM leads WHERE collected_at LIKE '2026-08-18%' OR last_checked_at LIKE '2026-08-18%'
    ORDER BY id""").fetchall()
print(f"count={len(rows)}")
for r in rows:
    print(f"  id={r['id']:<5} {r['store_name'][:26]:<26} {r['state']:<3} {str(r['email'])[:38]:<38} src={str(r['email_source_type'])[:18]:<18} mx={str(r['mx_provider']):<4} tz={str(r['recipient_timezone'])[:20]:<20} auto={r['auto_sendable']} status={r['status']}")

print("\n=== 2) MX WORKER TEST ===")
try:
    from preflight_gate import query_mx
    for d in ["bluebridgegames.com","guardiangames.com","thecomicskeep.com"]:
        try:
            st,_ = query_mx(d)
            print(f"  {d}: worker status={st}")
        except Exception as e:
            print(f"  {d}: worker EXC {type(e).__name__} {str(e)[:60]}")
except Exception as e:
    print("  import preflight_gate failed:", str(e)[:80])

print("\n=== 3) id=802 + id=701 duplicate ===")
for r in conn.execute("SELECT id,store_name,city,state,email,status,organization_key,auto_sendable FROM leads WHERE id IN (701,802)"):
    print("  ", dict(r))

print("\n=== 4) FINAL_SEND_PLAN status='planned' (queued) ===")
rows = conn.execute("""SELECT id,lead_id,company_name,recipient_email,status,planned_sequence,outreach_batch_date,created_at
    FROM final_send_plan WHERE status='planned' ORDER BY id""").fetchall()
print(f"planned entries={len(rows)}")
for r in rows:
    print(f"  fsp={r['id']:<5} lead={r['lead_id']:<5} {str(r['company_name'])[:26]:<26} {str(r['recipient_email'])[:38]:<38} seq={r['planned_sequence']}")

print("\n=== 4b) any FSP entry for lead 802 (any status) ===")
for r in conn.execute("SELECT id,lead_id,company_name,status FROM final_send_plan WHERE lead_id=802"):
    print("  ", dict(r))

print("\n=== 5) scheduler config ===")
try:
    for r in conn.execute("SELECT key,value FROM system_config WHERE key IN ('scheduler_enabled','manual_pause','execution_mode','standing_authorization','risk_gate_status')"):
        print(f"  {r['key']} = {r['value']}")
except Exception as e:
    print("  system_config read err:", str(e)[:60])
conn.close()
