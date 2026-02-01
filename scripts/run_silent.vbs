' run_silent.vbs
' Launches the docBrain monitor in the background with a hidden window.
' Usage: Double-click to start monitoring D:\ silently.

Set WshShell = CreateObject("WScript.Shell")

' Get the directory where this script is located
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptPosition)

' Path to the run.bat script
batchPath = chr(34) & scriptDir & "\run.bat" & chr(34)
command = batchPath & " watch"

' 0 = Hide the window, False = Don't wait for completion
WshShell.Run command, 0, False

Set WshShell = Nothing
