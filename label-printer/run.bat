@echo off
REM Lance l'interface d'impression d'etiquettes Brother QL-570 (avec console).
cd /d "%~dp0"

REM --- Trouver Python : le lanceur "py" d'abord, sinon "python" ---
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY ( python --version >nul 2>&1 && set "PY=python" )

if not defined PY (
  echo.
  echo [ERREUR] Python 3 est introuvable.
  echo Installe-le depuis https://www.python.org/downloads/
  echo en cochant "Add Python to PATH", puis relance ce fichier.
  echo.
  echo Astuce : si "python" ouvre le Microsoft Store, va dans
  echo Parametres ^> Applications ^> Alias d'execution d'application
  echo et desactive les entrees python.exe.
  echo.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creation de l'environnement virtuel...
  %PY% -m venv .venv
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
