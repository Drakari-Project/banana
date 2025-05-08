#!/usr/bin/env python3

import os
import json
import shutil
import logging
import zipfile
from pathlib import Path
import pyinotify


WATCH_DIR = "/home/drakari/pineapple/tmp"

# Setup logging
logging.basicConfig(
    filename="bannana.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

Path(WATCH_DIR).mkdir(parents=True, exist_ok=True)

def unzip_file(zip_path, extract_to):
    if not zipfile.is_zipfile(zip_path):
        return

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
        print(f"✅ Extracted '{zip_path}' to '{extract_to}'")

def saveStudentGame(path, collectionName, gameName, system):
    romPath = os.path.join("/home/drakari/roms/", collectionName)
    gameDataPath = os.path.join("/home/drakari/gamedata", collectionName)
    
    Path(romPath).mkdir(parents=True, exist_ok=True)
    Path(gameDataPath).mkdir(parents=True, exist_ok=True)
    
    shutil.move("/home/drakari/pineapple/static/upload/game.zip", gameDataPath)
    unzip_file(os.path.join(gameDataPath, "game.zip"), gameDataPath)

    return

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        full_path = event.pathname
        logging.info(f"New file detected: {full_path}")

        try:
            # Load the config from Bannana.json in the same directory
            config_path = os.path.join(WATCH_DIR, "Bannana.json")
            with open(config_path, "r") as f:
                config = json.load(f)

            command = config.get("command")
            match command:
                case 0:
                    # You'll need to pass in actual values here
                    saveStudentGame(
                        path=None,  # Placeholder — update as needed
                        collectionName=config.get("collection", "default_collection"),
                        gameName=config.get("gameName", "default_game"),
                        system=config.get("system", "default_system")
                    )
                case 1:
                    logging.info("Command 1 triggered.")
                case 2:
                    logging.info("Command 2 triggered.")
        except Exception as e:
            logging.exception(f"Error handling new file: {e}")

def watch():
    logging.info(f"Watching directory: {WATCH_DIR}")
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_CREATE

    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)
    wm.add_watch(WATCH_DIR, mask, rec=False)

    notifier.loop()

if __name__ == "__main__":
    try:
        watch()
    except KeyboardInterrupt:
        logging.info("Bannana stopped by user.")
    except Exception as e:
        logging.exception(f"Bannana failed: {e}")