#!/usr/bin/env bash
# Lance le programme EN ARRIÈRE-PLAN (sans fenêtre de terminal).
# - n'ouvre pas de terminal visible
# - survit à la fermeture de toute fenêtre
# - si déjà lancé, ouvre simplement le navigateur (pas de second démarrage)
cd "$(dirname "$0")"

PORT="${PORT:-5000}"
URL="http://127.0.0.1:$PORT"

open_browser() {
  if command -v xdg-open >/dev/null 2>&1; then
    ( sleep 1; xdg-open "$URL" >/dev/null 2>&1 ) &
  fi
}

is_running() {
  ( exec 3<>"/dev/tcp/127.0.0.1/$PORT" ) 2>/dev/null && return 0 || return 1
}

# Déjà lancé ? → on ouvre juste le navigateur.
if is_running; then
  open_browser
  exit 0
fi

# Première utilisation : installation silencieuse des dépendances.
if [ ! -d ".venv" ]; then
  command -v notify-send >/dev/null 2>&1 && \
    notify-send "Étiquettes QL-570" "Installation en cours… (~1 min)"
  python3 -m venv .venv
  ./.venv/bin/pip install --upgrade pip >/dev/null 2>&1
  ./.venv/bin/pip install -r requirements.txt >/dev/null 2>&1
fi

# Démarrage détaché : le serveur tourne sans fenêtre et survit aux fermetures.
mkdir -p .run
setsid ./.venv/bin/python app.py >.run/server.log 2>&1 < /dev/null &
echo $! > .run/server.pid

# Attendre que le serveur réponde, puis ouvrir le navigateur.
for _ in $(seq 1 40); do
  is_running && break
  sleep 0.5
done
open_browser
