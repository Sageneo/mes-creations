@echo off
REM Lance l'interface web d'impression d'etiquettes Brother QL-570 sous Windows.
cd /d "%~dp0"

if not exist ".venv\" (
  echo Creation de l'environnement virtuel...
  python -m venv .venv
  call .venv\Scripts\python.exe -m pip install --upgrade pip
  call .venv\Scripts\pip.exe install -r requirements.txt
)

echo.
echo Interface disponible sur http://127.0.0.1:5000
echo (Fermez cette fenetre pour arreter le programme.)
echo.
start "" http://127.0.0.1:5000
.venv\Scripts\python.exe app.py
pause
