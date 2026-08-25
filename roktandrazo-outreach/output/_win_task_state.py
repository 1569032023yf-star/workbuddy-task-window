import winreg
ROOT = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache"
names = ["RoktRazo-BD-PreSend", "RoktRazo-BD-Outreach", "RoktRazo-BD-PostSend", "RoktRazo-BD-EndOfDay"]
for n in names:
    try:
        t = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ROOT + r"\Tree" + "\\" + n)
        guid = winreg.QueryValueEx(t, "Id")[0]
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ROOT + r"\Tasks" + "\\" + guid)
        try:
            lrt = winreg.QueryValueEx(k, "LastRunTime")[0]
        except Exception:
            lrt = "N/A"
        try:
            ltr = winreg.QueryValueEx(k, "LastTaskResult")[0]
        except Exception:
            ltr = "N/A"
        try:
            nrt = winreg.QueryValueEx(k, "NextRunTime")[0]
        except Exception:
            nrt = "N/A"
        print(n + " => LastRun=" + str(lrt) + " LastResult=" + str(ltr) + " NextRun=" + str(nrt))
    except Exception as e:
        print(n + " => REG_ERR=" + repr(e))
