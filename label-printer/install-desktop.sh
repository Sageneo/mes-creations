#!/usr/bin/env bash
# Crée un raccourci cliquable (fichier .desktop) pour lancer le programme
# depuis le menu des applications ET le bureau — l'équivalent Linux d'un .bat.
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
NAME="Étiquettes QL-570"
DESKTOP_FILE_NAME="etiquettes-ql570.desktop"

chmod +x "$DIR/run.sh" "$DIR/launch.sh"

# Contenu du lanceur (chemins absolus de ce dossier).
read -r -d '' CONTENT <<EOF || true
[Desktop Entry]
Type=Application
Version=1.0
Name=$NAME
Comment=Imprimer des étiquettes sur Brother QL-570
Exec=$DIR/launch.sh
Icon=$DIR/icon.png
Terminal=false
Categories=Utility;Office;
EOF

# 1) Menu des applications
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"
printf '%s\n' "$CONTENT" > "$APPS_DIR/$DESKTOP_FILE_NAME"
chmod +x "$APPS_DIR/$DESKTOP_FILE_NAME"
echo "✓ Raccourci ajouté au menu des applications."
command -v update-desktop-database >/dev/null 2>&1 && \
  update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true

# 2) Bureau (si le dossier existe — gère aussi un bureau localisé)
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Bureau")"
[ -d "$DESKTOP_DIR" ] || DESKTOP_DIR="$HOME/Desktop"
if [ -d "$DESKTOP_DIR" ]; then
  printf '%s\n' "$CONTENT" > "$DESKTOP_DIR/$DESKTOP_FILE_NAME"
  chmod +x "$DESKTOP_DIR/$DESKTOP_FILE_NAME"
  # Marque le lanceur comme « de confiance » (GNOME/Nautilus)
  command -v gio >/dev/null 2>&1 && \
    gio set "$DESKTOP_DIR/$DESKTOP_FILE_NAME" metadata::trusted true >/dev/null 2>&1 || true
  echo "✓ Raccourci ajouté sur le bureau : $DESKTOP_DIR"
fi

echo
echo "Terminé ! Cherche « $NAME » dans tes applications ou double-clique"
echo "l'icône sur le bureau pour lancer le programme."
