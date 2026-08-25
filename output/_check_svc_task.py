import winreg, os, glob, json

print("=== SERVICES (HKLM\\SYSTEM\\CurrentControlSet\\Services) ===")
try:
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services")
    i = 0
    found = []
    while True:
        try:
            name = winreg.EnumKey(key, i)
            i += 1
            if any(k in name.lower() for k in ("rokt", "bd", "execution")):
                try:
                    sk = winreg.OpenKey(key, name)
                    img, _ = winreg.QueryValueEx(sk, "ImagePath")
                    st, _ = winreg.QueryValueEx(sk, "Start")
                    found.append((name, img, st))
                    winreg.CloseKey(sk)
                except OSError:
                    found.append((name, "?", "?"))
        except OSError:
            break
    winreg.CloseKey(key)
    for f in found:
        print(f"  {f[0]} | Start={f[2]} | {f[1]}")
    if not found:
        print("  (none matching rokt/bd/execution)")
except Exception as e:
    print("  ERROR:", e)

print()
print("=== SCHEDULED TASKS (C://Windows//System32//Tasks) ===")
tasks_root = r"C:/Windows/System32/Tasks"
try:
    hits = []
    for root, dirs, files in os.walk(tasks_root):
        for fn in files:
            fl = fn.lower()
            if any(k in fl for k in ("rokt", "bd", "outreach", "orchestrat")):
                p = os.path.join(root, fn)
                try:
                    with open(p, "r", encoding="utf-16") as f:
                        content = f.read()
                    hits.append((p, content))
                except Exception:
                    try:
                        with open(p, "r", encoding="utf-8") as f:
                            content = f.read()
                        hits.append((p, content))
                    except Exception as e:
                        hits.append((p, f"<unreadable: {e}>"))
    for p, c in hits:
        print(f"  FOUND: {p}")
        print(f"  LEN: {len(c)}")
except Exception as e:
    print("  ERROR:", e)

print()
print("=== TASKS XML DETAIL (if any) ===")
for p, c in hits:
    if c.startswith("<"):
        print(f"--- {p} ---")
        print(c[:3000])
        print("...")
