@echo off
REM Lance le serveur SANS fenetre de console (via pythonw) et ouvre le navigateur.
REM Appele en general par launch.vbs (qui masque aussi la phase d'installation).
cd /d "%~dp0"

REM Premiere utilisation : creation de l'environnement + dependances.
if not exist ".venv\" (
  python -m venv .venv
  call .venv\Scripts\python.exe -m pip install --upgrade pip
  call .venv\Scripts\pip.exe install -r requirements.txt
)

REM Deja lance ? (port 5000 ouvert) -> on ouvre juste le navigateur.
powershell -NoProfile -Command "try{(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',5000);exit 0}catch{exit 1}" >nul 2>&1
if %errorlevel%==0 (
  start "" http://127.0.0.1:5000
  exit /b
)

REM Demarrage sans console (pythonw) et detache.
start "" .venv\Scripts\pythonw.exe app.py

REM Attendre que le serveur reponde puis ouvrir le navigateur.
powershell -NoProfile -Command "for($i=0;$i -lt 40;$i++){try{(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',5000);break}catch{Start-Sleep -Milliseconds 500}}" >nul 2>&1
start "" http://127.0.0.1:5000
