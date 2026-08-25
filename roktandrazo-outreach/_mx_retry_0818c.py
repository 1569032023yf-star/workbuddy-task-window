import subprocess
def ns(d, server=None):
    cmd = ["nslookup","-type=mx",d] + ([server] if server else [])
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=25)
        txt = (out.stdout or b"").decode("utf-8","replace") + (out.stderr or b"").decode("utf-8","replace")
        for ln in txt.splitlines():
            if "mail exchanger" in ln.lower():
                return "ok", ln.strip()[:80]
        return "NO_MX", txt.strip()[:80]
    except Exception as e:
        return "ERR", str(e)[:60]

for srv in [None, "8.8.8.8", "1.1.1.1"]:
    r, det = ns("doubledragongames.com", srv)
    print(f"server={srv}: {r} | {det}")
# also A record check
try:
    out = subprocess.run(["nslookup","doubledragongames.com"], capture_output=True, timeout=25)
    print("A:", (out.stdout or b"").decode("utf-8","replace")[:200])
except Exception as e:
    print("A ERR", e)
