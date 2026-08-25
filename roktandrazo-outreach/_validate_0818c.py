import os, sys, socket, subprocess
sys.path.insert(0, os.getcwd())
from timezone_resolver import resolve_timezone
try:
    from preflight_gate import query_mx
    HAVE_WORKER = True
except Exception as e:
    HAVE_WORKER = False
    print("WARN preflight_gate import failed:", e)

def direct_mx(domain):
    """Fallback: use system nslookup for MX record."""
    try:
        out = subprocess.run(["nslookup","-type=mx",domain], capture_output=True, text=True, timeout=15)
        txt = out.stdout + out.stderr
        for line in txt.splitlines():
            if "mail exchanger" in line.lower() or "MX" in line and "exchange" in line.lower():
                return "ok", line.strip()
        return "no_mail_route", txt.strip()[:120]
    except Exception as e:
        return "dns_error", str(e)[:120]

C = [
    ("Blue Bridge Games","Grand Rapids","MI","http://bluebridgegames.com","info@bluebridgegames.com"),
    ("The Wizard's Chest","Denver","CO","https://www.wizardschest.com","thewizard@thewizardschest.com"),
    ("Total Escape Games","Broomfield","CO","http://totalescapegames.com","info@totalescapegames.com"),
    ("Guardian Games","Portland","OR","https://www.guardiangames.com","ggpInfo@GuardianGames.com"),
    ("The Portland Game Store","Portland","OR","https://www.theportlandgamestore.com","info@theportlandgamestore.com"),
    ("Card Kingdom","Seattle","WA","https://www.cardkingdom.com","contact@cardkingdom.com"),
    ("Double Dragon Games","Denver","CO","http://doubledragongames.com","support@doubledragongames.com"),
    ("Time Warp Comics & Games","Cedar Grove","NJ","https://www.timewarpcomics.com/","friends@timewarpcomics.com"),
]
print(f"HAVE_WORKER={HAVE_WORKER}\n")
for nm,city,st,web,email in C:
    dom = web.split("://")[-1].split("/")[0].lower()
    edom = email.rsplit("@",1)[-1].lower()
    tz, stt = resolve_timezone(city, st)
    if HAVE_WORKER:
        mx, _ = query_mx(dom)
    else:
        mx, _ = direct_mx(dom)
    match = "MATCH" if dom==edom else "MISMATCH"
    print(f"{nm:26s} {city:14s} {st:3s} tz={tz}/{stt:9s} mx={mx:12s} dom={dom:24s} {match}")
