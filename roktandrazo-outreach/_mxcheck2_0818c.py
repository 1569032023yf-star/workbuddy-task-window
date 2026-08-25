import subprocess
for d in ["bluehighwaygames.com","redcastlegames.com"]:
    for srv in [None,"8.8.8.8"]:
        try:
            cmd=["nslookup","-type=mx",d]+([] if srv is None else [srv])
            out=subprocess.run(cmd,capture_output=True,timeout=25)
            txt=(out.stdout or b"").decode("utf-8","replace")
            mx=[ln.strip() for ln in txt.splitlines() if "mail exchanger" in ln.lower()]
            print(f"{d} via {srv}: {'ok -> '+mx[0][:70] if mx else 'NO_MX'}")
        except Exception as e:
            print(f"{d}: ERR {e}")
