import subprocess
DOMS = ["bluebridgegames.com","totalescapegames.com","guardiangames.com",
        "theportlandgamestore.com","cardkingdom.com","doubledragongames.com","timewarpcomics.com"]
for d in DOMS:
    try:
        out = subprocess.run(["nslookup","-type=mx",d], capture_output=True, timeout=25)
        txt = (out.stdout or b"").decode("utf-8","replace") + (out.stderr or b"").decode("utf-8","replace")
        ok = False
        line = ""
        for ln in txt.splitlines():
            if "mail exchanger" in ln.lower():
                ok = True; line = ln.strip(); break
        print(f"{d:26s} mx={'ok ' if ok else 'NO_MX':6s} {line[:70]}")
    except Exception as e:
        print(f"{d:26s} mx=ERR {str(e)[:60]}")
