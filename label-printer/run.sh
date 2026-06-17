#!/usr/bin/env bash
# Lance l'interface web d'impression d'étiquettes Brother QL-570.
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Création de l'environnement virtuel…"
  python3 -m venv .venv
  ./.venv/bin/pip install --upgrade pip
  ./.venv/bin/pip install -r requirements.txt
fi

URL="http://127.0.0.1:${PORT:-5000}"
echo "Interface disponible sur $URL"

# Ouvre le navigateur automatiquement (après un court délai, en arrière-plan).
if command -v xdg-open >/dev/null 2>&1; then
  ( sleep 2; xdg-open "$URL" >/dev/null 2>&1 ) &
fi

exec ./.venv/bin/python app.py
