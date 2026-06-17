@echo off
REM Cree un raccourci "Etiquettes QL-570" sur le bureau (lancement sans console).
cd /d "%~dp0"
powershell -NoProfile -Command ^
  "$ws=New-Object -ComObject WScript.Shell;" ^
  "$lnk=$ws.CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Etiquettes QL-570.lnk');" ^
  "$lnk.TargetPath='%~dp0launch.vbs';" ^
  "$lnk.WorkingDirectory='%~dp0';" ^
  "$lnk.IconLocation='%~dp0icon.ico';" ^
  "$lnk.Description='Imprimer des etiquettes sur Brother QL-570';" ^
  "$lnk.Save()"
echo.
echo Raccourci "Etiquettes QL-570" cree sur le bureau.
echo Double-clique dessus pour lancer le programme (sans fenetre noire).
pause
