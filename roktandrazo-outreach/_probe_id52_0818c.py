import sqlite3, os
DB = os.path.join("data","bd_leads.db")
conn = sqlite3.connect(DB)
r = conn.execute("""SELECT id,store_name,city,state,official_website,email,email_source_type,
    email_verified_on_official_site,organization_key,recipient_timezone,timezone_status,
    mx_provider,auto_sendable,status,confidence_score,evidence_url,evidence_checked_at
    FROM leads WHERE id=52""").fetchone()
cols = ["id","store_name","city","state","official_website","email","email_source_type",
    "verified","org_key","tz","tz_status","mx","auto_send","status","conf","ev_url","ev_checked"]
for c,v in zip(cols,r): print(f"{c:14s}: {v}")
conn.close()
