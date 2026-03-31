Set WshShell = CreateObject("WScript.Shell")
WshShell.Run Chr(34) & WScript.ScriptFullName & Chr(34), 0, False

Dim scriptDir
scriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

WshShell.Run "cmd /c cd /d """ & scriptDir & """ && set PYTHONUTF8=1 && python bot.py", 0, False
