import os, sys, json, time, logging
from shutil import move
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

class watchdawg(FileSystemEventHandler):
    def __init__(self, folder_to_watch, rules):
        self.folder_to_watch = folder_to_watch
        self.rules = rules
    def on_created(self, event):
        if event.is_directory:
            return
        time.sleep(1)
        filepath = event.src_path
        filename = os.path.basename(filepath)

        try:
            last_size = -1
            stable_checks=3
            while stable_checks<3:
                if not os.path.exists(filepath):
                    logging.info(f"Skipping {filepath}")
                    return
                current_size = os.path.getsize(filepath)
                if current_size==last_size and current_size !=0:
                    stable_checks+=1
                else:
                    stable_checks=0
                last_size=current_size
                time.sleep(0.5)
        except (FileNotFoundError, PermissionError):
            logging.warning(f"Could not access {filename} for sizecheck")
            return
        try:
            _ ,file_extension = os.path.splitext(filename)
            extension = file_extension.lower()

            if not extension:
                return
            destination_folder_name = "Other"
            for folder_name, extensions in self.rules.items():
                if extension in extensions in self.rules.items():
                    destination_folder_name = folder_name
                    break
            dest_folder_path = os.path.join(self.folder_to_watch, destination_folder_name)
            if not os.path.exists(dest_folder_path):
                os.makedirs(dest_folder_path)
                logging.info(f"Create directory: {dest_folder_path}")
            dest_file_path = os.path.join(dest_folder_path, filename)
            if os.path.exists(dest_file_path):
                name, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                new_filename = f"{name}_{timestamp}{ext}"
                dest_file_path = os.path.join(dest_folder_path, new_filename)
                logging.warning(f"'{filename} already exists. renaming...")
            move(event.src_path, dest_file_path)
            logging.info(f"Moved '{filename}' to the '{destination_folder_name}' folder.")
        except Exception as e:
            logging.error(f"Error processing '{filename}': {e}")
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        handlers=[
                            logging.FileHandler("watcher.log"),
                            logging.StreamHandler(sys.stdout)
                        ])
    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
            FOLDER_TO_WATCH = config["folder_to_watch"]
            RULES = config["rules"]
    except FileNotFoundError:
        logging.error("'config.json' not found. Please ensure it exists in the same directory.")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error("'config.json' is not a valid JSON file.'")
        sys.exit(1)
    except KeyError as e:
        logging.error("'config.json' has a missing key.")
        sys.exit(1)
    if not os.path.isdir(FOLDER_TO_WATCH):
        logging.error(f"FATAL: The folder '{FOLDER_TO_WATCH}' does not exist.")
        sys.exit(1)
    logging.info(f"Watchdawg started. Monitoring '{FOLDER_TO_WATCH}'....")

    event_handler = watchdawg(FOLDER_TO_WATCH, RULES)
    observer = Observer()
    observer.schedule(event_handler, FOLDER_TO_WATCH, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        Observer().stop()
        logging.info("Watchdawg stopped by user.")
    observer.join()
