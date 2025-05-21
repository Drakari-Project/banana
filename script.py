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
import sys


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

import os
import zipfile
import tempfile
import shutil
import logging

def unzip_and_move_to_game_data(zip_path, gameDataPath, gameName):
    # Create a temporary directory for extraction
    extract_temp = tempfile.mkdtemp(prefix="unzipped_")

    # Extract ZIP contents
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_temp)
        names = [n for n in zip_ref.namelist() if n and not n.startswith("__MACOSX")]

    # Get unique top-level entries
    top_level = set(name.split('/')[0] for name in names)

    # Destination path using gameName
    final_path = os.path.join(gameDataPath, gameName.replace(" ", "_"))

    if len(top_level) == 1:
        # A root folder already exists
        root_candidate = os.path.join(extract_temp, next(iter(top_level)))
        if os.path.isdir(root_candidate):
            shutil.move(root_candidate, final_path)
            logging.info(f"✅ Moved existing root folder to: {final_path}")
            return final_path

    # Otherwise, create a new folder and move all extracted contents into it
    os.makedirs(final_path, exist_ok=True)
    for item in os.listdir(extract_temp):
        item_path = os.path.join(extract_temp, item)
        if os.path.abspath(item_path) != os.path.abspath(final_path):
            shutil.move(item_path, final_path)

    logging.info(f"📁 Created and moved new root folder to: {final_path}")
    return final_path

    
def saveGameListXML(collectionName, gameName):
    xmlPath = f"/home/drakari/ES-DE/gamelists/{collectionName}/"
    xmlFile = os.path.join(xmlPath, "gamelist.xml")

    Path(xmlPath).mkdir(parents=True, exist_ok=True)
    
    if os.path.exists(xmlFile):
        tree = XML.parse(xmlFile)
        root = tree.getroot()
    else:
        root = XML.Element("gameList")  # Create root element
        tree = XML.ElementTree(root)
        tree.write(xmlFile, encoding="utf-8", xml_declaration=True)  # Save the empty XML file

    game = XML.Element("game")
    XML.SubElement(game, "path").text = f"./{gameName}.game".replace(" ", "_")
    XML.SubElement(game, "name").text = f"{gameName}"
    XML.SubElement(game, "desc").text = config["desc"]
    XML.SubElement(game, "developer").text = config["dev"]
   
    root.append(game)

    xml_str = XML.tostring(root, encoding="utf-8")
    
    parsed = minidom.parseString(xml_str)
    
    pretty_xml = parsed.toprettyxml(indent="  ")
    # Remove lines that are just whitespace
    pretty_xml = "\n".join([line for line in pretty_xml.splitlines() if line.strip()])

    with open(xmlFile, "w", encoding="utf-8") as file:
        file.write(pretty_xml)
    return

def saveSystemListXML(collectionName):
    #System file
    xmlPath = f"/home/drakari/ES-DE/custom_systems/"
    xmlFile = f"/home/drakari/ES-DE/custom_systems/es_systems.xml"

    Path(xmlPath).mkdir(parents=True, exist_ok=True)
    
    if os.path.exists(xmlFile):
        tree = XML.parse(xmlFile)
        root = tree.getroot()
    else:
        root = XML.Element("systemList")  # Create root element
        tree = XML.ElementTree(root)
        tree.write(xmlFile, encoding="utf-8", xml_declaration=True)  # Save the empty XML file

    for system in root.findall("system"):
        name_element = system.find("name")
        if name_element is not None and name_element.text == collectionName.replace(" ", "_"):
            break

    system = XML.Element("system")
    XML.SubElement(system, "name").text = collectionName.replace(" ", "_")
    XML.SubElement(system, "fullname").text = collectionName
    XML.SubElement(system, "path").text = f"%ROMPATH%/{collectionName.replace(" ", "_")}"
    XML.SubElement(system, "extension").text = ".game"
    XML.SubElement(system, "command").text = "/usr/bin/bash /home/drakari/launchers/launch.bash %ROM%"
   
    root.append(system)

    xml_str = XML.tostring(root, encoding="utf-8")
    
    parsed = minidom.parseString(xml_str)

    pretty_xml = parsed.toprettyxml(indent="  ")
    # Remove lines that are just whitespace
    pretty_xml = "\n".join([line for line in pretty_xml.splitlines() if line.strip()])

    with open(xmlFile, "w", encoding="utf-8") as file:
        file.write(pretty_xml)
    return

def saveStudentGame(collectionName, gameName, studentGameEngine):
    global config
    romPath = os.path.join("/home/drakari/roms/", collectionName.replace(" ", "_"))
    gameDataPath = os.path.join("/home/drakari/gamedata/", collectionName.replace(" ", "_"))
    
    Path(romPath).mkdir(parents=True, exist_ok=True)
    Path(gameDataPath).mkdir(parents=True, exist_ok=True)
    
    shutil.move("/home/drakari/pineapple/static/uploads/game.zip", gameDataPath)

    whereToMoveGame = os.path.join(gameDataPath, "game.zip")

    innerFolder = unzip_and_move_to_game_data(whereToMoveGame, gameDataPath, gameName)
    os.remove(whereToMoveGame)

    match studentGameEngine:
        case "code.org":
            logging.info("It's codeorg")
            systemPath = '/home/drakari/systems/codeorg'
            Path(systemPath).mkdir(parents=True, exist_ok=True)

            os.symlink(os.path.join(innerFolder, "index.html"), os.path.join(systemPath, f"{gameName}.game".replace(" ", "_")))
            os.symlink(os.path.join(systemPath, f"{gameName}.game".replace(" ", "_")), os.path.join(romPath, f"{gameName}.game".replace(" ", "_")))
        case "java":
            logging.info("It's Java")
            systemPath = '/home/drakari/systems/jre'
            Path(systemPath).mkdir(parents=True, exist_ok=True)

            logging.info(innerFolder)

            os.chmod(os.path.join(innerFolder, config["exeName"]), 0o755)
            os.symlink(os.path.join(innerFolder, config["exeName"]), os.path.join(systemPath, f"{gameName}.game").replace(" ", "_"))
            os.symlink(os.path.join(systemPath, f"{gameName}.game".replace(" ", "_")), os.path.join(romPath, f"{gameName}.game").replace(" ", "_"))
            
        case "native":
            logging.info("It's native")
            systemPath = '/home/drakari/systems/native'
            Path(systemPath).mkdir(parents=True, exist_ok=True)

            logging.info(innerFolder)

            os.chmod(os.path.join(innerFolder, config["exeName"]), 0o755)
            os.symlink(os.path.join(innerFolder, config["exeName"]), os.path.join(systemPath, f"{gameName}.game".replace(" ", "_")))
            os.symlink(os.path.join(systemPath, f"{gameName}.game".replace(" ", "_")), os.path.join(romPath, f"{gameName}.game".replace(" ", "_")))
    
    saveGameListXML(collectionName, gameName)

    saveSystemListXML(collectionName)

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
                    )
                case 2:
                    logging.info("Command 2 triggered.")
                case 3:
                    logging.info("Command 3 triggered.")
            os.remove(config_path)
            sys.exit(0)
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
        sys.exit(1)