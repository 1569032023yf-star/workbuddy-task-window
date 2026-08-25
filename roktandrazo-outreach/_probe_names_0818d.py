import sqlite3, os
conn = sqlite3.connect(os.path.join("data","bd_leads.db"))
for pat in ["%Guardian%","%Card Kingdom%","%Blue Highway%"]:
    print(f"### LIKE {pat}")
    for r in conn.execute("SELECT id,store_name,city,state,official_website,email,status,email_source_type,mx_provider,timezone_status,auto_sendable FROM leads WHERE store_name LIKE ? ORDER BY id", (pat,)):
        print("   ", dict(zip(["id","store","city","st","web","email","status","est","mx","tzst","auto"],r)))
conn.close()
