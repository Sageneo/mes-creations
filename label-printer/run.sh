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

echo "Interface disponible sur http://127.0.0.1:5000"
exec ./.venv/bin/python app.py
