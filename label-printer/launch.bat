@echo off
REM Lance le serveur SANS fenetre de console (via pythonw) et ouvre le navigateur.
REM Appele en general par launch.vbs (qui masque aussi la phase d'installation).
cd /d "%~dp0"

REM --- Trouver Python : le lanceur "py" d'abord, sinon "python" ---
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY ( python --version >nul 2>&1 && set "PY=python" )

if not defined PY (
  powershell -NoProfile -Command "Add-Type -AssemblyName PresentationFramework;[void][System.Windows.MessageBox]::Show('Python 3 est introuvable.' + [char]10 + [char]10 + 'Installe-le depuis https://www.python.org/downloads/ en cochant ''Add Python to PATH'', puis relance.' + [char]10 + [char]10 + 'Astuce : Parametres > Applications > Alias d''execution d''application > desactive les entrees python.exe du Microsoft Store.','Etiquettes QL-570','OK','Warning')"
  exit /b 1
)

REM --- Premiere utilisation : creation de l'environnement + dependances ---
if not exist ".venv\Scripts\pythonw.exe" (
  %PY% -m venv .venv
  call .venv\Scripts\python.exe -m pip install --upgrade pip
  call .venv\Scripts\pip.exe install -r requirements.txt
)

if not exist ".venv\Scripts\pythonw.exe" (
  powershell -NoProfile -Command "Add-Type -AssemblyName PresentationFramework;[void][System.Windows.MessageBox]::Show('La creation de l''environnement Python a echoue. Verifie l''installation de Python.','Etiquettes QL-570','OK','Error')"
  exit /b 1
)

REM --- Deja lance ? (port 5000 ouvert) -> on ouvre juste le navigateur ---
powershell -NoProfile -Command "try{(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',5000);exit 0}catch{exit 1}" >nul 2>&1
if %errorlevel%==0 (
  start "" http://127.0.0.1:5000
  exit /b
)

REM --- Demarrage sans console (pythonw) et detache ---
start "" .venv\Scripts\pythonw.exe app.py

REM --- Attendre que le serveur reponde puis ouvrir le navigateur ---
powershell -NoProfile -Command "for($i=0;$i -lt 40;$i++){try{(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',5000);break}catch{Start-Sleep -Milliseconds 500}}" >nul 2>&1
start "" http://127.0.0.1:5000
