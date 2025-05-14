#!/usr/bin/env python3

import os
import json
import shutil
import logging
import zipfile
from pathlib import Path
import pyinotify
import time


WATCH_DIR = "/home/drakari/pineapple/tmp"
command = None
config = None
# Setup logging
logging.basicConfig(
    filename="banana.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

Path(WATCH_DIR).mkdir(parents=True, exist_ok=True)

def wait_until_file_is_stable(path, timeout=10, interval=0.5):
    """Wait until file is no longer changing in size."""
    start_time = time.time()
    last_size = -1

    while time.time() - start_time < timeout:
        try:
            current_size = os.path.getsize(path)
        except FileNotFoundError:
            current_size = -1  # File might not exist yet

        if current_size == last_size and current_size > 0:
            return True  # File is done uploading
        last_size = current_size
        time.sleep(interval)

    return False

def unzip_file(zip_path, extract_to):
    if not zipfile.is_zipfile(zip_path):
        return

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
        print(f"✅ Extracted '{zip_path}' to '{extract_to}'")

def saveStudentGame(collectionName, gameName, studentGameEngine):
    romPath = os.path.join("/home/drakari/roms/", collectionName)
    gameDataPath = os.path.join("/home/drakari/gamedata/", collectionName)
    
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
            time.sleep(1)
            config_path = '/home/drakari/pineapple/tmp/banana_config.json'
            logging.info(config_path)
            wait_until_file_is_stable(full_path)
            with open(config_path, "r") as file:
                global command 
                global config
                contents = file.read()
                logging.info(f"File content: {repr(contents)}")
                config = json.loads(contents)
                command = config.get("command")
            match command:
                case 1:
                    saveStudentGame(
                        collectionName=config.get("collection"),
                        gameName=config.get("gameName"),
                        studentGameEngine=config.get("studentGameEngine")
                    )
                case 2:
                    logging.info("Command 2 triggered.")
                case 3:
                    logging.info("Command 3 triggered.")
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
        logging.info("banana stopped by user.")
    except Exception as e:
        logging.exception(f"banana failed: {e}")