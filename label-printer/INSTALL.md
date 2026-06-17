# Installation — pas à pas

Le programme installe **automatiquement** ses dépendances au premier
lancement (via un environnement virtuel Python). Tu n'as donc qu'à
installer Python, puis lancer le script fourni.

---

## 🐧 Linux (Debian / Ubuntu / Mint…)

1. Installe Python et les bibliothèques système (une seule fois) :
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv libusb-1.0-0
   ```
2. Récupère le programme :
   ```bash
   git clone https://github.com/Sageneo/mes-creations.git
   cd mes-creations/label-printer
   ```
   *(ou copie simplement le dossier `label-printer` sur le PC).*
3. Lance :
   ```bash
   ./run.sh
   ```
4. Ouvre **http://127.0.0.1:5000** dans le navigateur (`run.sh` l'ouvre
   automatiquement s'il le peut).

### Raccourci cliquable (comme un .bat Windows)

Pour lancer le programme d'un double-clic, sans terminal, crée un raccourci :

```bash
./install-desktop.sh
```

Cela ajoute **« Étiquettes QL-570 »** dans le menu des applications **et** une
icône sur le bureau. Ensuite, un simple double-clic lance le programme et
ouvre le navigateur.

> Au 1er double-clic sur l'icône du bureau, certains systèmes demandent
> d'« autoriser le lancement » (clic droit → *Autoriser le lancement* /
> *Allow Launching*).

> Pour imprimer sans `sudo`, ajoute la règle USB (voir README → « Droits
> d'accès USB »).

---

## 🪟 Windows

1. Installe **Python 3** depuis <https://www.python.org/downloads/> en
   cochant **« Add Python to PATH »** pendant l'installation.
2. Récupère le programme : télécharge le dossier `label-printer`
   (ou `git clone` si tu as Git).
3. Double-clique sur **`run.bat`**. La première fois, il installe tout
   (≈ 1 min), puis ouvre le navigateur sur **http://127.0.0.1:5000**.
4. **Accès USB** : installe le pilote **WinUSB** pour la QL-570 avec
   [Zadig](https://zadig.akeo.ie/) (voir README → installation Windows).

---

## 📦 Mettre le programme sur un autre PC

1. Copie le dossier **`label-printer`** sur l'autre PC
   (inutile de copier `.venv/`, il se recrée tout seul).
2. Installe Python (voir ci-dessus) puis lance `run.sh` / `run.bat`.
3. **Numérotation** : pour repartir du bon numéro, transfère le suivi :
   - Sur le 1er PC : page **« 📊 Suivi des codes »** → **Exporter**.
   - Copie le fichier `.json` téléchargé sur le 2e PC.
   - Sur le 2e PC : page **« 📊 Suivi des codes »** → choisis le fichier →
     **Importer** (fusion par défaut).

> 💡 Le suivi est stocké dans `label-printer/registry.json`. Tu peux aussi
> ranger ce fichier dans un dossier synchronisé et pointer dessus via la
> variable d'environnement `QL_REGISTRY` (voir README → Configuration).

---

## Dépannage rapide

| Problème | Solution |
|---|---|
| `python : command not found` (Windows) | Réinstalle Python en cochant « Add to PATH ». |
| `./run.sh: Permission denied` | `chmod +x run.sh` puis relance. |
| Imprimante non détectée | Vérifie le branchement, et les droits USB (README). |
| Mauvaise numérotation après changement de PC | Exporte/importe le suivi (voir ci-dessus). |
