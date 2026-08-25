"""One-time fix: correct BDExecutionHost binPath to pywin32 pythonservice host."""
import subprocess
BIN = '"C://Users//15690//.workbuddy//binaries//python//versions//3.13.12//Lib//site-packages//win32//pythonservice.exe" "C://Users//15690//WorkBuddy//2026-06-05-15-31-42//roktandrazo-outreach//bd_execution_host_service.BDExecutionHost"'
r1 = subprocess.run(["sc.exe", "config", "BDExecutionHost", f"binPath={BIN}", "start=auto"],
                    capture_output=True, text=True, encoding="gbk", errors="replace")
print("CONFIG:", r1.returncode, (r1.stdout or r1.stderr).strip()[:200])
r2 = subprocess.run(["sc.exe", "failure", "BDExecutionHost", "reset=86400",
                     "actions=restart/60000/restart/60000/restart/60000"],
                    capture_output=True, text=True, encoding="gbk", errors="replace")
print("FAILURE:", r2.returncode)
