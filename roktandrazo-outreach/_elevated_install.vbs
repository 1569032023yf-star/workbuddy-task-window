' BD Execution Host — VBScript Service Installer
' Uses WMI to create service, then starts Python installer for config
Option Explicit

Dim objWMIService, objService, errReturn

' Get WMI service
Set objWMIService = GetObject("winmgmts:{impersonationLevel=impersonate}!\\.\root\cimv2")

' Delete existing service if present
On Error Resume Next
Dim existingService
For Each existingService In objWMIService.ExecQuery("SELECT * FROM Win32_Service WHERE Name = 'BDExecutionHost'")
    existingService.StopService()
    WScript.Sleep 2000
    errReturn = existingService.Delete()
    WScript.Echo "Existing service deleted"
Next
On Error GoTo 0

' Create service via WMI
Dim objNewService
Set objNewService = objWMIService.Get("Win32_Service")

errReturn = objNewService.Create(
    "BDExecutionHost",                                     ' Name
    "BD Execution Host",                                   ' DisplayName
    "C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\bd_execution_host_service.py", ' PathName
    16,                                                     ' ServiceType = Own Process
    2,                                                      ' StartType = Auto
    1,                                                      ' ErrorControl = Normal
    Null,                                                   ' LoadOrderGroup
    Null,                                                   ' TagId
    Null,                                                   ' Dependencies
    "LocalSystem",                                         ' StartName
    ""                                                     ' Password
)

If errReturn = 0 Then
    WScript.Echo "Service BDExecutionHost created successfully"
    
    ' Start the service
    Dim objService2
    Set objService2 = objWMIService.Get("Win32_Service.Name='BDExecutionHost'")
    errReturn = objService2.StartService()
    
    If errReturn = 0 Then
        WScript.Echo "Service started successfully"
    Else
        WScript.Echo "Service start returned: " & errReturn
    End If
Else
    WScript.Echo "Service creation failed with error: " & errReturn
End If

WScript.Echo "Installation complete."
WScript.Sleep 3000
