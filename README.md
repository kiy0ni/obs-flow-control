# OBSFlowControl

## Description

### FR

Un script Python qui surveille le flux vidéo d'OBS pour détecter des problèmes (flux gelé, faible débit) et change automatiquement les scènes en fonction de l'état du flux.

### EN

A Python script that monitors OBS video streams to detect issues (frozen stream, low bitrate) and automatically switches scenes based on the stream's status.

-----

## Fonctionnalités / Features

### FR

  - Détection des scènes gelées via le WebSocket d'OBS (v5+).
  - **Nouveau :** Surveillance du débit (bitrate) du stream.
  - Changement automatique de scène vers une scène "BRB" si un problème est détecté, et retour automatique à la scène principale lorsque le problème est résolu.
  - Endpoints API pour démarrer (`/start`) et arrêter (`/stop`) le stream OBS.
  - Endpoint API (`/health`) pour vérifier l'état de la connexion au WebSocket d'OBS.
  - Configuration simplifiée via un fichier `.env`.
  - Serveur web robuste (Waitress) prêt pour une utilisation en production.

### EN

  - Detects frozen scenes using OBS WebSocket (v5+).
  - **New:** Monitors the stream's bitrate.
  - Automatically switches to a "BRB" scene if an issue is detected, and automatically returns to the main scene when the issue is resolved.
  - API endpoints to start (`/start`) and stop (`/stop`) the OBS stream.
  - API endpoint (`/health`) to check the connection status to the OBS WebSocket.
  - Simplified configuration via a `.env` file.
  - Robust, production-ready web server (Waitress).

-----

## Prérequis / Prerequisites

### FR

1.  **Python 3**.
2.  **OBS avec WebSocket v5+ activé**.
      - (C'est généralement inclus par défaut dans les versions récentes d'OBS. Allez dans `Outils` -\> `Paramètres du WebSocket` pour l'activer et définir un mot de passe).
3.  Les modules Python listés dans `requirements.txt`.

### EN

1.  **Python 3**.
2.  **OBS with WebSocket v5+ enabled**.
      - (This is usually included by default in recent OBS versions. Go to `Tools` -\> `WebSocket Settings` to enable it and set a password).
3.  The Python modules listed in `requirements.txt`.

-----

## Installation

### FR

1.  Clonez ce dépôt ou téléchargez `app.py`, `requirements.txt` et créez un fichier `.env`.
2.  Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```
3.  Créez un fichier `.env` à la racine du projet (vous pouvez copier/renommer le fichier `.env.example` s'il existe) et remplissez-le avec vos informations :
    ```ini
    # Configuration de l'application
    APP_PORT=5987

    # Configuration OBS WebSocket
    OBS_HOST=127.0.0.1
    OBS_PORT=4455
    OBS_PASSWORD=votremotdepasseobs

    # Noms des scènes et sources
    BRB_SCENE=BRB
    MAIN_SCENE=MAIN
    CAMERA_SOURCE_NAME=Flux

    # Seuil de débit en Kbps
    BITRATE_THRESHOLD=1000
    ```
4.  Assurez-vous que les scènes (`BRB_SCENE`, `MAIN_SCENE`) et la source média (`CAMERA_SOURCE_NAME`) existent dans votre OBS.
5.  Lancez le script Python :
    ```bash
    python app.py
    ```
6.  **OPTIONNEL** : Si vous souhaitez utiliser le serveur à distance, ouvrez le port `APP_PORT` sur votre pare-feu.

### EN

1.  Clone this repository or download `app.py`, `requirements.txt`, and create a `.env` file.
2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Create a `.env` file in the project root (you can copy/rename an `.env.example` file if one exists) and fill it with your information:
    ```ini
    # Application Config
    APP_PORT=5987

    # OBS WebSocket Config
    OBS_HOST=127.0.0.1
    OBS_PORT=4455
    OBS_PASSWORD=yourobs_password

    # Scene and Source Names
    BRB_SCENE=BRB
    MAIN_SCENE=MAIN
    CAMERA_SOURCE_NAME=Flux

    # Bitrate threshold in Kbps
    BITRATE_THRESHOLD=1000
    ```
4.  Ensure the scenes (`BRB_SCENE`, `MAIN_SCENE`) and the media source (`CAMERA_SOURCE_NAME`) exist in your OBS.
5.  Run the Python script:
    ```bash
    python app.py
    ```
6.  **OPTIONAL**: If you want to use the server remotely, open the `APP_PORT` in your firewall.

-----

## Fichiers de Projet / Project Files

### `requirements.txt`

```txt
flask
obs-websocket-py
python-dotenv
waitress
```

### Démarrage du script / Starting the script

```bash
python app.py
```

*Le serveur se lancera sur `http://0.0.0.0:5987` (ou le port défini dans votre `.env`)*

-----

## Accès API / API Access

### Démarrer un stream / Start stream

```bash
GET http://<server-ip>:<port>/start
```

### Arrêter un stream / Stop stream

```bash
GET http://<server-ip>:<port>/stop
```

### Vérifier la santé / Health Check

*Vérifie si le script peut se connecter à OBS WebSocket.*

```bash
GET http://<server-ip>:<port>/health
```

**Réponse (Succès) :**

```json
{
  "status": "ok",
  "message": "Connecté à OBS WebSocket."
}
```

**Réponse (Erreur) :**

```json
{
  "status": "error",
  "message": "Déconnecté d'OBS: [Raison de l'erreur]"
}
```
