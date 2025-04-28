#!/usr/bin/env python3

import os
import json
import subprocess
import time
from pathlib import Path
import shutil
import logging
import zipfile
import os

import inotify.adapters


WATCH_DIR = "/home/drakari/pineapple/tmp";

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

def watch():
    logging.info(f"Watching directory: {WATCH_DIR}")
    inotifyFileChecker = inotify.adapters.Inotify()

    inotifyFileChecker.add_watch(WATCH_DIR)

    for event in inotifyFileChecker.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event
        if "CREATE" in type_names:
            full_path = os.path.join(path, filename)
            logging.info(f"New file detected: {full_path}")
            
            #Get the run data
            with open((os.path.join(path, "Bannana.json")), "r") as data:
                config = json.load(data)
            command = config.get("command")
            match(command):
                case 0:
                     
                    saveStudentGame()
                    break
                case 1:
                    #command 2
                    break
                case 2:
                    #command 3
                    break

def saveStudentGame(path, collectionName, gameName, system):
    romPath = os.path.join("/home/drakari/roms/", collectionName)
    gameDataPath = os.path.join("/home/drakari/gamedata", collectionName)
    
    Path(romPath).mkdir(parents=True, exist_ok=True)
    Path(gameDataPath).mkdir(parents=True, exist_ok=True)
    
    shutil.move("/home/drakari/pineapple/static/upload/game.zip", gameDataPath)
    unzip_file(os.path.join(gameDataPath, "game.zip"), gameDataPath)

    return


if __name__ == "__main__":
    try:
        watch()
    except KeyboardInterrupt:
        logging.info("Bannana stopped by user.")
    except Exception as e:
        logging.exception(f"Bannana failed: {e}")

