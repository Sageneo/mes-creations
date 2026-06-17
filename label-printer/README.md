# Impression d'étiquettes — Brother QL-570

Interface web (Flask) pour créer et imprimer des étiquettes sur une
**Brother QL-570** sous Linux. Permet de composer du **texte**, un
**QR code**, un **code-barres** et/ou une **image**, de choisir le format
de rouleau DK, de prévisualiser puis d'imprimer.

## Aperçu

- Choix du format de rouleau (continu 12→62 mm et prédécoupés compatibles QL-570)
- Longueur réglable pour les rouleaux continus
- Texte multi-lignes (taille auto ou fixe, gras, alignement)
- QR code (URL/texte)
- Code-barres (Code128, Code39, EAN-13/8, UPC-A, ISBN-13)
- Import d'image/logo
- Aperçu en direct dans le navigateur
- Détection automatique de l'imprimante USB

## Installation

Prérequis : Python 3.10+ et la bibliothèque `libusb`.

```bash
# Dépendance système (Debian/Ubuntu)
sudo apt install python3-venv libusb-1.0-0

cd label-printer
./run.sh
```

`run.sh` crée un environnement virtuel, installe les dépendances et démarre
le serveur sur <http://127.0.0.1:5000>.

Installation manuelle :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Droits d'accès USB

Par défaut, l'accès USB requiert les droits root. Pour utiliser
l'imprimante sans `sudo`, créez une règle udev :

```bash
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="04f9", ATTRS{idProduct}=="2028", MODE="0666", GROUP="plugdev"' \
  | sudo tee /etc/udev/rules.d/99-brother-ql.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Ajoutez votre utilisateur au groupe `plugdev` puis rebranchez l'imprimante :

```bash
sudo usermod -aG plugdev "$USER"
```

> `idProduct` peut varier (`2028` pour la QL-570). Vérifiez avec `lsusb`
> (« Brother Industries ») et adaptez la règle si besoin.

## Configuration

Variables d'environnement reconnues :

| Variable     | Défaut                        | Description                          |
|--------------|-------------------------------|--------------------------------------|
| `QL_PRINTER` | `usb://0x04f9:0x2028`         | Identifiant brother_ql de l'imprimante |
| `HOST`       | `127.0.0.1`                   | Adresse d'écoute (`0.0.0.0` pour le réseau local) |
| `PORT`       | `5000`                        | Port HTTP                            |
| `DEBUG`      | `0`                           | `1` pour activer le mode debug Flask |

Le champ « Imprimante » de l'interface accepte aussi un backend
`linux_kernel`, par exemple `file:///dev/usb/lp0`.

## Architecture

| Fichier            | Rôle                                                |
|--------------------|-----------------------------------------------------|
| `app.py`           | Serveur Flask + routes API (`/api/preview`, `/api/print`…) |
| `label_maker.py`   | Génération de l'image de l'étiquette (Pillow)       |
| `printer.py`       | Conversion + envoi via `brother_ql`                 |
| `templates/`, `static/` | Interface web                                  |

## Dépannage

- **« Aucune imprimante détectée »** : vérifiez `lsusb`, l'alimentation, et
  les droits udev ci-dessus.
- **Erreur de conversion / format** : certains rouleaux ne sont pas
  compatibles QL-570 ; seuls les formats ≤ 62 mm sont proposés.
- **Image trop grande** : limite de 8 Mo par requête.
