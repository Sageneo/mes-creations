' Lanceur Windows SANS fenetre : execute launch.bat en mode cache.
' Double-clique ce fichier pour demarrer le programme sans console noire.
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = dir

' Petit message uniquement lors de la toute premiere installation.
If Not fso.FolderExists(dir & "\.venv") Then
  sh.Popup "Premiere installation en cours (~1 min)...", 4, "Etiquettes QL-570", 64
End If

' 0 = fenetre cachee, False = ne pas attendre la fin.
sh.Run "cmd /c """ & dir & "\launch.bat""", 0, False
