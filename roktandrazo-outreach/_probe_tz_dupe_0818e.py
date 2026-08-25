import sqlite3, os
conn = sqlite3.connect(os.path.join("data","bd_leads.db")); conn.row_factory=sqlite3.Row
# (a) find the lead blocked ONLY by TIMEZONE_UNRESOLVED (email valid, mx ok, not sent...)
print("### leads with email but tz_status != RESOLVED (not sent/suppressed):")
for r in conn.execute("""SELECT id,store_name,city,state,email,status,timezone_status,organization_key,mx_provider
    FROM leads WHERE email IS NOT NULL AND email!='' AND email LIKE '%@%.%'
    AND timezone_status != 'RESOLVED' AND status NOT IN ('sent','bounced','do_not_contact','rejected','failed','delivery_issue','bounce_review','contact_form_pool')"""):
    print("   ", dict(r))
# (b) Grand Adventures 701 vs 802
print("\n### Grand Adventures rows:")
for r in conn.execute("SELECT id,store_name,city,state,email,status,organization_key,official_website FROM leads WHERE store_name LIKE '%Grand Adventure%'"):
    print("   ", dict(r))
conn.close()
