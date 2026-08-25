import sqlite3, os
DB = os.path.join("data","bd_leads.db")
conn = sqlite3.connect(DB)
cands = [
    ("bluebridgegames.com","info@bluebridgegames.com","Blue Bridge Games"),
    ("thewizardschest.com","thewizard@thewizardschest.com","The Wizard's Chest"),
    ("totalescapegames.com","info@totalescapegames.com","Total Escape Games"),
    ("guardiangames.com","ggpInfo@GuardianGames.com","Guardian Games"),
    ("theportlandgamestore.com","info@theportlandgamestore.com","The Portland Game Store"),
    ("thecompleatstrategist.com","info@thecompleatstrategist.com","The Compleat Strategist"),
    ("cardkingdom.com","contact@cardkingdom.com","Card Kingdom"),
    ("doubledragongames.com","support@doubledragongames.com","Double Dragon Games"),
    ("timewarpcomics.com","friends@timewarpcomics.com","Time Warp Comics (NJ)"),
    ("time-warp.com","info@time-warp.com","Time Warp (Boulder CO)"),
]
print("=== CANDIDATE DEDUP vs LIVE DB ===")
for dom,email,name in cands:
    dh = __import__("hashlib").md5(dom.encode()).hexdigest()[:16]
    row = conn.execute("SELECT id,store_name,status,email,email_source_type FROM leads WHERE domain_hash=? OR email=?",(dh,email)).fetchone()
    print(f"{name:32s} dom={dom:26s} -> {'EXISTS id='+str(row[0]) if row else 'CLEAN'}")
print()
print("=== CURRENT V2-LIKE FIELD COUNT (heuristic, not gate) ===")
cnt = conn.execute("""SELECT COUNT(*) FROM leads WHERE mx_provider='ok' AND email_source_type='official_page_visible'
    AND email_verified_on_official_site=1 AND timezone_status='RESOLVED' AND auto_sendable=1
    AND status NOT IN ('sent','replied','bounced','unsubscribed','do_not_contact')""").fetchone()[0]
print("heuristic V2-like count =", cnt)
conn.close()
