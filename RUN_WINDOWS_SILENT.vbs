Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "RUN_WINDOWS.bat" & chr(34), 0
Set WshShell = Nothing
