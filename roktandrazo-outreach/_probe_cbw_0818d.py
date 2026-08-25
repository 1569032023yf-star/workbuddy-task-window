import sqlite3, os
conn = sqlite3.connect(os.path.join("data","bd_leads.db"))
print("### Comic Book World rows:")
for r in conn.execute("SELECT id,store_name,city,state,official_website,email,status,email_source_type,mx_provider,timezone_status,auto_sendable,organization_key FROM leads WHERE store_name LIKE '%Comic Book World%' ORDER BY id"):
    print("   ", dict(zip(["id","store","city","st","web","email","status","est","mx","tzst","auto","org"],r)))
print("\n### rows with comicbookworld domain or email:")
for r in conn.execute("SELECT id,store_name,city,state,official_website,email,status FROM leads WHERE official_website LIKE '%comicbookworld%' OR email LIKE '%comicbookworld%'"):
    print("   ", dict(zip(["id","store","city","st","web","email","status"],r)))
conn.close()
