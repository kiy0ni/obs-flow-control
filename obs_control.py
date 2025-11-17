# -*- coding: utf-8 -*-
import os
import time
import threading
import logging
from flask import Flask, jsonify
from dotenv import load_dotenv
import obswebsocket.requests as obsrequests
from obswebsocket import ReqClient
from obswebsocket.exceptions import ConnectionError as OBSConnectionError
from waitress import serve

# --- Configuration ---
# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Config de l'application Flask
APP_PORT = int(os.environ.get("APP_PORT", 5987))

# Config OBS WebSocket
OBS_HOST = os.environ.get("OBS_HOST", "127.0.0.1")
OBS_PORT = int(os.environ.get("OBS_PORT", 4455))
OBS_PASSWORD = os.environ.get("OBS_PASSWORD", "")

# Noms des scènes et sources
BRB_SCENE = os.environ.get("BRB_SCENE", "BRB")
MAIN_SCENE = os.environ.get("MAIN_SCENE", "MAIN")
CAMERA_SOURCE_NAME = os.environ.get("CAMERA_SOURCE_NAME", "Flux")

# Seuil de débit (en Kbps)
BITRATE_THRESHOLD = int(os.environ.get("BITRATE_THRESHOLD", 1000))
MONITOR_INTERVAL = 5  # Secondes entre chaque vérification

# --- Setup du Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Initialisation de l'application et du client OBS ---
app = Flask(__name__)

# Le client OBS sera partagé par l'application et le thread de monitoring
obs_client = ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD, timeout=5)

# Variable globale pour suivre le "freeze"
last_cursor_position = None

# --- Fonctions de Monitoring ---

def monitor_stream_health():
    """
    Thread de monitoring qui vérifie le débit et le gel de la source.
    Change de scène si nécessaire.
    """
    global last_cursor_position
    
    while True:
        try:
            # S'assurer que nous sommes connectés
            if not obs_client.is_connected():
                logging.warning("OBS déconnecté, tentative de reconnexion...")
                # La bibliothèque gère la reconnexion au prochain appel
                # Mais nous pouvons forcer une tentative ici si nécessaire
                # Ou simplement attendre le prochain appel
                time.sleep(MONITOR_INTERVAL)
                continue

            # 1. Vérifier si le stream est actif
            stats_response = obs_client.call(obsrequests.GetStreamStatus()).get_response_data()
            is_streaming = stats_response.get('outputActive', False)

            if not is_streaming:
                logging.info("Le stream n'est pas actif. Pause du monitoring.")
                time.sleep(MONITOR_INTERVAL)
                continue

            # Si le stream est actif, vérifier la santé
            health_ok = True
            
            # 2. Vérifier le débit (Bitrate)
            current_bitrate = stats_response.get('outputBitrate', 0)
            if current_bitrate < BITRATE_THRESHOLD:
                health_ok = False
                logging.warning(f"Problème de débit détecté ! Actuel: {current_bitrate} Kbps (Seuil: {BITRATE_THRESHOLD} Kbps)")

            # 3. Vérifier le "Freeze" de la source
            try:
                media_status = obs_client.call(obsrequests.GetMediaInputStatus(inputName=CAMERA_SOURCE_NAME)).get_response_data()
                current_cursor = media_status.get('mediaCursor')
                
                if current_cursor is None:
                    # La source n'est peut-être pas une source média ou a un problème
                    health_ok = False
                    logging.warning(f"Impossible de récupérer le 'mediaCursor' pour '{CAMERA_SOURCE_NAME}'.")
                elif current_cursor == last_cursor_position:
                    health_ok = False
                    logging.warning(f"Source '{CAMERA_SOURCE_NAME}' semble gelée (cursor immobile).")
                
                last_cursor_position = current_cursor # Mettre à jour la position
            
            except Exception as e:
                # Gère les cas où la source n'existe pas ou n'est pas une source média
                health_ok = False
                logging.error(f"Erreur lors de la vérification de la source '{CAMERA_SOURCE_NAME}': {e}")

            # 4. Agir en fonction de la santé
            current_scene_response = obs_client.call(obsrequests.GetCurrentProgramScene()).get_response_data()
            current_scene_name = current_scene_response.get('currentProgramSceneName')

            if not health_ok and current_scene_name != BRB_SCENE:
                logging.info("Problème détecté. Passage à la scène BRB.")
                obs_client.call(obsrequests.SetCurrentProgramScene(sceneName=BRB_SCENE))
            
            elif health_ok and current_scene_name == BRB_SCENE:
                logging.info("La santé du stream est revenue. Retour à la scène MAIN.")
                obs_client.call(obsrequests.SetCurrentProgramScene(sceneName=MAIN_SCENE))
            
            elif health_ok:
                logging.info(f"Stream OK. (Scène: {current_scene_name}, Débit: {current_bitrate} Kbps)")

        except OBSConnectionError:
            logging.error("Impossible de se connecter à OBS WebSocket. Vérifiez l'hôte, le port et le mot de passe.")
            last_cursor_position = None # Réinitialiser en cas de déconnexion
        except Exception as e:
            logging.error(f"Erreur inattendue dans la boucle de monitoring: {e}")
        
        time.sleep(MONITOR_INTERVAL)


# --- Endpoints de l'API Flask ---

@app.route("/start", methods=["GET"])
def start_stream():
    """Démarrer le stream OBS."""
    try:
        obs_client.call(obsrequests.StartStream())
        return jsonify({"status": "ok", "message": "Stream démarré."})
    except Exception as e:
        logging.error(f"Erreur lors du démarrage du stream: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/stop", methods=["GET"])
def stop_stream():
    """Arrêter le stream OBS."""
    try:
        obs_client.call(obsrequests.StopStream())
        return jsonify({"status": "ok", "message": "Stream arrêté."})
    except Exception as e:
        logging.error(f"Erreur lors de l'arrêt du stream: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Vérifier la connexion à OBS."""
    try:
        obs_client.call(obsrequests.GetVersion())
        return jsonify({"status": "ok", "message": "Connecté à OBS WebSocket."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Déconnecté d'OBS: {e}"}), 503

# --- Démarrage de l'application ---

if __name__ == "__main__":
    # Connexion initiale à OBS
    try:
        obs_client.connect()
        obs_client.wait_for_connection() # Attendre que la connexion soit établie
        logging.info(f"Connecté à OBS WebSocket sur {OBS_HOST}:{OBS_PORT}")
    except OBSConnectionError as e:
        logging.critical(f"Échec de la connexion initiale à OBS: {e}")
        logging.critical("Le monitoring et l'API ne fonctionneront pas sans connexion.")
        # On pourrait choisir de quitter ici, mais on laisse l'API tourner
        # au cas où OBS se lancerait plus tard.
    except Exception as e:
        logging.error(f"Erreur de connexion non gérée: {e}")

    # Démarrer le monitoring dans un thread séparé
    monitor_thread = threading.Thread(target=monitor_stream_health, daemon=True)
    monitor_thread.start()
    logging.info("Thread de monitoring démarré.")

    # Démarrer le serveur Flask (en mode production avec Waitress)
    logging.info(f"Serveur Flask démarré sur http://0.0.0.0:{APP_PORT}")
    serve(app, host="0.0.0.0", port=APP_PORT)
