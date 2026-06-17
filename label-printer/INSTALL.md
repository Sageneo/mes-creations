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

Le programme tourne **sans fenêtre de terminal** (en arrière-plan) : le
client ne risque pas de l'arrêter en fermant une fenêtre. Pour l'arrêter
volontairement, utilise le bouton **« ⏻ Arrêter le programme »** en bas de
l'interface. Relancer = re-cliquer l'icône (si déjà lancé, ça rouvre juste
le navigateur).

> Au 1er double-clic sur l'icône du bureau, certains systèmes demandent
> d'« autoriser le lancement » (clic droit → *Autoriser le lancement* /
> *Allow Launching*).

> Pour imprimer sans `sudo`, ajoute la règle USB (voir README → « Droits
> d'accès USB »).

---

## 🪟 Windows

### 1. Installer Python
Télécharge **Python 3** depuis <https://www.python.org/downloads/> et
**coche « Add Python to PATH »** pendant l'installation.

### 2. Télécharger le programme
Deux façons :

- **Sans Git (le plus simple)** : va sur
  `https://github.com/Sageneo/mes-creations/tree/claude/eager-knuth-1b04mo`,
  bouton vert **« Code » → « Download ZIP »**, puis décompresse. Le dossier
  qui t'intéresse est **`label-printer`**.
- **Avec Git** :
  ```
  git clone https://github.com/Sageneo/mes-creations.git
  cd mes-creations\label-printer
  git checkout claude/eager-knuth-1b04mo
  ```

### 3. Lancer
Dans le dossier `label-printer`, deux possibilités :

- **`launch.vbs`** → lance **sans fenêtre noire** (recommandé pour un poste
  client) et ouvre le navigateur. La 1re fois, l'installation (~1 min) se
  fait en arrière-plan.
- **`run.bat`** → lance **avec** une fenêtre de console (pratique pour voir
  les messages / déboguer).

L'interface s'ouvre sur **http://127.0.0.1:5000**.

### 4. Raccourci sur le bureau (optionnel)
Double-clique **`install-shortcut.bat`** : il crée une icône
**« Étiquettes QL-570 »** sur le bureau qui lance le programme sans console.

### 5. Accès USB
Installe le pilote **WinUSB** pour la QL-570 avec
[Zadig](https://zadig.akeo.ie/) (voir README → installation Windows).

> Pour arrêter le programme (lancé sans console), utilise le bouton
> **« ⏻ Arrêter le programme »** en bas de l'interface.

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
| `Python was not found` / le Store s'ouvre (Windows) | Python n'est pas installé ou pas dans le PATH. Installe-le depuis [python.org](https://www.python.org/downloads/) en cochant **« Add Python to PATH »**. Puis : *Paramètres ▸ Applications ▸ Alias d'exécution d'application* → **désactive** les entrées `python.exe` / `python3.exe` du Microsoft Store. Redémarre la session, relance. |
| `Le chemin d'accès spécifié est introuvable` / `.venv\Scripts\pythonw.exe` absent (Windows) | Conséquence du point ci-dessus : Python manquait, donc `.venv` n'a pas été créé. Corrige Python puis relance `launch.vbs` / `run.bat`. |
| `python : command not found` (Linux) | `sudo apt install python3 python3-venv`. |
| `./run.sh: Permission denied` | `chmod +x run.sh` puis relance. |
| Imprimante non détectée | Vérifie le branchement, et les droits USB (README). |
| Mauvaise numérotation après changement de PC | Exporte/importe le suivi (voir ci-dessus). |
