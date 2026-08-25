import sqlite3, os, hashlib, sys
sys.path.insert(0, os.getcwd())
from timezone_resolver import resolve_timezone
conn = sqlite3.connect(os.path.join("data","bd_leads.db")); conn.row_factory=sqlite3.Row
C = [
 ("The Comics Keep","Bremerton","WA","https://www.thecomicskeep.com","contact@thecomicskeep.com"),
 ("Phantom Zone Comics","Lynnwood","WA","https://www.phantomzonecomics.com","customerservice@phantomzonecomics.com"),
 ("Subspace Comics","Lynnwood","WA","https://www.subspacecomics.com","hq@subspacecomics.com"),
 ("Arcane Comics","Seattle","WA","https://www.arcanecomicbooks.com","info@arcanecomicbooks.com"),
 ("Phoenix Comics & Games","Seattle","WA","https://www.phoenixseattle.com","info@phoenixseattle.com"),
 ("Outsider Comics","Seattle","WA","https://www.outsidercomics.com","info@outsidercomics.com"),
 ("Fantasy Mountain Board Gaming","Signal Mountain","TN","https://www.fantasymountainboardgaming.com","info@fantasymountainboardgaming.com"),
]
for nm,city,st,web,email in C:
    dom = web.lower().replace("https://","").replace("http://","").replace("www.","").split("/")[0]
    dh = hashlib.md5(dom.encode()).hexdigest()[:16]
    edom = email.rsplit("@",1)[-1].lower()
    tz, stt = resolve_timezone(city, st)
    ex = conn.execute("SELECT id,store_name,status FROM leads WHERE domain_hash=? OR email=? OR store_name=?",(dh,email,nm)).fetchone()
    print(f"{nm:28s} {city:12s} {st:3s} tz={tz.split('/')[-1] if tz else 'NONE':9s} match={'Y' if dom==edom else 'N'} -> {'EXISTS id='+str(ex['id'])+' '+ex['store_name']+' '+ex['status'] if ex else 'CLEAN'}")
conn.close()
