"""P1.8F — validate existing timezone + org_key enrichment on 3 Ithaca leads."""
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

IDS = [1095, 1096, 1101]
conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory = sqlite3.Row

# ---- A. timezone preview (dry run, NY scope) ----
print("=== A. TIMEZONE (apply_timezone_to_leads, state_filter=NY) ===")
pre = apply_timezone_to_leads(conn, dry_run=True, state_filter="NY")
print("dry-run stats:", {k: v for k, v in pre.items() if k != "unresolved_examples"})
if pre.get("unresolved_examples"):
    print("  unresolved examples:", pre["unresolved_examples"])

# ---- B. org_key preview (strictly _gen_organization_key, only if empty) ----
print("\n=== B. ORG_KEY PREVIEW (_gen_organization_key) ===")
for lid in IDS:
    L = dict(conn.execute("SELECT * FROM leads WHERE id=?", (lid,)).fetchone())
    cur = str(L.get("organization_key") or "").strip()
    gen = _gen_organization_key(L) if not cur else cur
    # duplicate cross-check: any SENT lead with same org_key?
    dup = conn.execute(
        "SELECT COUNT(*) FROM send_log sl JOIN leads l ON sl.lead_id=l.id WHERE l.organization_key=? AND sl.status='sent'",
        (gen,)).fetchone()[0]
    print(f"  lead={lid:<5} {L['store_name'][:28]:<28} current={cur!r} generated={gen!r} sent_dup={dup}")
conn.close()
