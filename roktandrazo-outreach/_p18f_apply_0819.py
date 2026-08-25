"""P1.8F apply — timezone via apply_timezone_to_leads(NY) + org_key via _gen_organization_key (only if empty)."""
import os, sys, sqlite3
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
def _load_env(p):
    try:
        for line in open(p, encoding="utf-8"):
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,v=line.split("=",1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError: pass
_load_env(os.path.join(BASE,".env"))

from timezone_resolver import apply_timezone_to_leads
from broad_outreach_gate import _gen_organization_key

conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory = sqlite3.Row

# A. timezone apply (NY scope, writes where UNSET)
stats = apply_timezone_to_leads(conn, dry_run=False, state_filter="NY")
print("TIMEZONE APPLY stats:", {k: v for k, v in stats.items() if k != "unresolved_examples"})

# B. org_key apply (only if empty), with dup cross-check
for lid in [1094, 1095, 1096, 1101]:
    L = dict(conn.execute("SELECT * FROM leads WHERE id=?", (lid,)).fetchone())
    cur = str(L.get("organization_key") or "").strip()
    if cur:
        print(f"  lead={lid} org_key already set: {cur} (skip)")
        continue
    gen = _gen_organization_key(L)
    dup = conn.execute(
        "SELECT COUNT(*) FROM send_log sl JOIN leads l ON sl.lead_id=l.id WHERE l.organization_key=? AND sl.status='sent'",
        (gen,)).fetchone()[0]
    if dup:
        print(f"  lead={lid} DUP-ORG {gen} has {dup} sent history — NOT writing sendable")
    else:
        conn.execute("UPDATE leads SET organization_key=? WHERE id=?", (gen, lid))
        print(f"  lead={lid} org_key -> {gen} (no sent dup)")
conn.commit()
print("\n=== POST-APPLY STATE (4 NY leads) ===")
for r in conn.execute("SELECT id,store_name,recipient_timezone,timezone_status,organization_key FROM leads WHERE id IN (1094,1095,1096,1101) ORDER BY id"):
    print(f"  {r['id']:<5} {r['store_name'][:26]:<26} tz={str(r['recipient_timezone'])[:20]:<20} tzst={r['timezone_status']:<10} org={r['organization_key']}")
conn.close()
