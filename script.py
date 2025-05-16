#!/usr/bin/env python3

import os
import json
import shutil
import logging
import zipfile
from pathlib import Path
import pyinotify
import time
import xml.etree.ElementTree as XML
from xml.dom import minidom


WATCH_DIR = "/home/drakari/pineapple/static/uploads/"
command = None
config = None
config_path = '/home/drakari/pineapple/static/uploads/banana_config.json'

# Setup logging
logging.basicConfig(
    filename="banana.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

Path(WATCH_DIR).mkdir(parents=True, exist_ok=True)

def wait_until_file_size_is_stable(path, timeout=10, interval=0.5):
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

# def unzip_file(zip_path, extract_to):
#     if not zipfile.is_zipfile(zip_path):
#         return

#     with zipfile.ZipFile(zip_path, 'r') as zip_ref:
#         zip_ref.extractall(extract_to)
#         logging.info(f"✅ Extracted '{zip_path}' to '{extract_to}'")

def unzip_and_get_inner_folder(zip_path, extract_to=None):
    if extract_to is None:
        extract_to = os.path.splitext(zip_path)[0]

    # Extract all files
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
        # Get all top-level directories from the ZIP
        names = zip_ref.namelist()

    # Find the top-level folder(s)
    top_dirs = set()
    for name in names:
        parts = name.split('/')
        if parts[0]:  # skip empty strings
            top_dirs.add(parts[0])
    
    if len(top_dirs) == 1:
        inner_folder = os.path.join(extract_to, top_dirs.pop())
        logging.info(f"✅ Extracted '{zip_path}' to '{inner_folder}'")
        return inner_folder
    else:
        # If there's no single top-level folder, return the full extract path
        return extract_to

def saveStudentGame(collectionName, gameName, studentGameEngine, exeName):
    romPath = os.path.join("/home/drakari/roms/", collectionName)
    gameDataPath = os.path.join("/home/drakari/gamedata/", collectionName)
    
    Path(romPath).mkdir(parents=True, exist_ok=True)
    Path(gameDataPath).mkdir(parents=True, exist_ok=True)
    
    shutil.move("/home/drakari/pineapple/static/uploads/game.zip", gameDataPath)

    whereToMoveGame = os.path.join(gameDataPath, "game.zip")

    innerFolder = unzip_and_get_inner_folder(whereToMoveGame, gameDataPath)
    os.remove(whereToMoveGame)

    match studentGameEngine:
        case "code.org":
            logging.info("It's code.org")
            systemPath = '/home/drakari/systems/code.org'
            Path(systemPath).mkdir(parents=True, exist_ok=True)

            os.symlink(innerFolder, os.path.join(systemPath, gameName))
            os.symlink(os.path.join(systemPath, gameName), os.path.join(romPath, gameName))
        case "java":
            logging.info("It's Java")
            systemPath = '/home/drakari/systems/jre'
            Path(systemPath).mkdir(parents=True, exist_ok=True)

            os.symlink(os.path.join(innerFolder, exeName), os.path.join(systemPath, gameName))
            os.symlink(os.path.join(systemPath, gameName), os.path.join(romPath, gameName))
            
        case "native":
            logging.info("It's native")
            systemPath = '/home/drakari/systems/native'
            Path(systemPath).mkdir(parents=True, exist_ok=True)

            os.symlink(os.path.join(innerFolder, exeName), os.path.join(systemPath, gameName))
            os.symlink(os.path.join(systemPath, gameName), os.path.join(romPath, gameName))
    
    #TODO Add xml interface stuff, thats kinda it I think
    
    xmlFile = '/home/drakari/ES-DE/gamelists/{collectionName}/gamelist.xml'

    tree = XML.parse(xmlFile)
    root = tree.getroot()
    game = XML.Element("game")
    global config
    XML.SubElement(game, "path").text = "./{gameName}.game"
    XML.SubElement(game, "name").text = "{gameName}"
    XML.SubElement(game, "desc").text = config["desc"]
    XML.SubElement(game, "developer").text = config["dev"]
   
    root.append(game)

    xml_str = XML.tostring(root, encoding="utf-8")
    
    parsed = minidom.parseString(xml_str)
    with open(xmlFile, "w", encoding="utf-8") as file:
        file.write(parsed.toprettyxml(indent="  "))

    return

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        full_path = event.pathname
        logging.info(f"New file detected: {full_path}")
        try:
            time.sleep(1)
            logging.info(config_path)
            wait_until_file_size_is_stable(full_path)
            with open(config_path, "r") as file:
                global command 
                global config

                contents = file.read()
                logging.info(f"File content: {repr(contents)}")

                config = json.loads(contents)
                command = config.get("command")
            match int(command):
                case 1:
                    logging.info(f"Command 1 triggered.")
                    saveStudentGame(
                        collectionName=config["collection"],
                        gameName=config["gameName"],
                        studentGameEngine=config["studentGameEngine"]
                        exeName=config["exeName"]
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