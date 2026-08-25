import sqlite3, os, hashlib
conn = sqlite3.connect(os.path.join("data","bd_leads.db"))
for nm,dom,email in [
    ("Guardian Games","guardiangames.com","ggpInfo@GuardianGames.com"),
    ("Card Kingdom","cardkingdom.com","contact@cardkingdom.com"),
    ("Blue Highway Games","bluehighwaygames.com","contact@bluehighwaygames.com"),
]:
    dh = hashlib.md5(dom.encode()).hexdigest()[:16]
    rows = conn.execute("SELECT id,store_name,status,email,email_source_type,mx_provider,timezone_status,organization_key,auto_sendable FROM leads WHERE domain_hash=? OR email=?",(dh,email)).fetchall()
    print(f"### {nm} (dom={dom}) -> {len(rows)} row(s)")
    for r in rows:
        print("   ", dict(zip(["id","store_name","status","email","est","mx","tzst","org","auto"],r)))
print("\n--- ids 1069-1075 ---")
for r in conn.execute("SELECT id,store_name,city,state,email,mx_provider,recipient_timezone,organization_key,auto_sendable,status FROM leads WHERE id BETWEEN 1069 AND 1075 ORDER BY id"):
    print("   ", dict(zip(["id","store","city","st","email","mx","tz","org","auto","status"],r)))
conn.close()
