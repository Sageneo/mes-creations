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
- Rotation du contenu à 90° (étiquettes prédécoupées)
- **Suivi des codes matériel** (numérotation suivie, anti-doublon, séries)

## Suivi / Code matériel

Section « 📋 Suivi / Code matériel » pour étiqueter du matériel avec une
numérotation suivie et **éviter les doublons**.

**Structure du code : `PREFIXE-AA-NNNN`** (ex. `ECR-26-1000`)

- **Préfixe** (liste fermée) : `PC` (ordinateur), `PCF` (fixe),
  `PCP` (portable), `ECR` (écran), `DCK` (docking), `TAB` (tablette).
  Tout autre préfixe est rejeté.
- **Année** (`AA`) : 2 chiffres, par défaut l'année courante (2026 → `26`).
- **Numéro** (`NNNN`) : 4 chiffres, de `1000` à `9999`. Compteur
  **indépendant par couple (préfixe + année)** ; il redémarre à `1000`
  à chaque nouvelle année.

Fonctionnement :

- Le bouton **« Prochain libre »** propose le prochain numéro non utilisé.
- Cochez **QR code** et/ou **Code-barres** pour choisir l'encodage du code
  (le code apparaît aussi en texte lisible). Code-barres en Code128.
- **Série** : imprime une plage de numéros consécutifs (ex. `1000` → `1010`
  = 11 étiquettes), **chacune découpée séparément**.
- **Anti-doublon** : un code déjà imprimé est refusé, sauf si vous cochez
  **« ♻️ Réimpression »** (cas d'une étiquette perdue ou abîmée).

Les codes imprimés sont mémorisés dans `registry.json` (local, non suivi
par git).

### Base de suivi (page « 📊 Suivi des codes »)

Accessible via le lien en haut de l'interface. Elle affiche :

- **l'état de la numérotation** : dernier et prochain numéro libre par
  préfixe/année ;
- **la liste des codes imprimés** (date, nombre d'impressions), avec
  filtre et suppression d'une entrée erronée ;
- **Exporter / Importer** le suivi (fichier `.json`) pour transférer la
  numérotation vers un autre PC. L'import **fusionne** par défaut (option
  « Remplacer » disponible).

> Pour partager la numérotation entre PC, voir `INSTALL.md`. Le fichier de
> suivi peut aussi être placé dans un dossier synchronisé via la variable
> d'environnement `QL_REGISTRY`.

## Installation

Voir **`INSTALL.md`** pour un guide pas à pas (Linux et Windows) et le
transfert vers un autre PC.

Prérequis : Python 3.10+.

### Linux

```bash
# Dépendance système (Debian/Ubuntu)
sudo apt install python3-venv libusb-1.0-0

cd label-printer
./run.sh
```

`run.sh` crée un environnement virtuel, installe les dépendances et démarre
le serveur sur <http://127.0.0.1:5000>.

### Windows

1. Installe [Python 3](https://www.python.org/downloads/) en cochant
   **« Add Python to PATH »**.
2. Double-clique sur **`run.bat`** (dans le dossier `label-printer`). Il crée
   l'environnement, installe les dépendances, ouvre le navigateur sur
   <http://127.0.0.1:5000> et démarre le serveur.
3. **Accès USB sous Windows** : `brother_ql` parle à l'imprimante en USB
   « brut » via libusb. Il faut donc remplacer le pilote USB de la QL-570 par
   **WinUSB** à l'aide de [Zadig](https://zadig.akeo.ie/) : lance Zadig →
   *Options ▸ List All Devices* → sélectionne la QL-570 → choisis **WinUSB** →
   *Replace Driver*. L'imprimante n'apparaîtra alors plus comme imprimante
   Windows classique, mais sera pilotable par ce programme.
   *(Pour revenir au pilote Brother, désinstalle le périphérique dans le
   Gestionnaire de périphériques et rebranche-le.)*

### Installation manuelle (toutes plateformes)

```bash
python3 -m venv .venv
# Linux/macOS : source .venv/bin/activate
# Windows     : .venv\Scripts\activate
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
| `QL_REGISTRY`| `registry.json` (local)       | Chemin du fichier de suivi (ex. dossier synchronisé) |

Le champ « Imprimante » de l'interface accepte aussi un backend
`linux_kernel`, par exemple `file:///dev/usb/lp0`.

## Détection de l'étiquette chargée

Le bouton **« 🔎 Détecter l'étiquette dans la machine »** interroge la QL-570
(commande de statut Brother) et lit le média réellement inséré : largeur en
mm, longueur (0 = rouleau continu) et type. Le format de rouleau
correspondant est alors **sélectionné automatiquement** dans la liste. Cela
évite d'imprimer avec un mauvais format. La QL-570 doit être branchée,
allumée et accessible (mêmes prérequis USB que pour l'impression).

## Sauvegarde de la configuration

Le bouton **« 💾 Enregistrer comme défaut »** mémorise les réglages courants
(format de rouleau, imprimante, tailles de police/QR, alignement, coupe…)
dans un fichier `config.json` à côté du programme. Ces valeurs sont
rechargées automatiquement au prochain lancement. La configuration est aussi
sauvegardée à chaque impression. Le fichier `config.json` est local et n'est
pas suivi par git.

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
