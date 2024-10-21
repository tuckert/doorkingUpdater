import os
import time
import subprocess
import random
import psutil
import shutil
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, DirCreatedEvent, FileCreatedEvent, FileSystemEvent
from dotenv import load_dotenv

load_dotenv()

csv_dir = os.getenv("CSV_DIR")
doorking_path = os.getenv("DOORKING_PATH")

queue = []

def generate_unique_filename():
    # Generate a unique name based on the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"update_{timestamp}.csv"


def rename_csv_file():
    original_csv = os.path.join(csv_dir, "update.csv")
    if os.path.exists(original_csv):
        unique_name = generate_unique_filename()
        unique_csv = os.path.join(csv_dir, unique_name)
        os.rename(original_csv, unique_csv)
        shutil.copy(unique_csv, os.path.join(csv_dir, 'backups', unique_name))
        queue.append(unique_csv)
        return unique_csv
    else:
        print(f"No file named 'update.csv' found in {csv_dir}")
        return None


class DoorKingUpdater:


    def is_doorking_running(self):
        # Check if doorking32.exe is running
        for process in psutil.process_iter(['name']):
            if process.info['name'] == 'doorking32.exe':
                return True
        return False

    def wait_for_doorking_to_finish(self):
        while self.is_doorking_running():
            # Random wait time between 5 and 10 seconds
            wait_time = random.randint(5, 10)
            print(f"Doorking is running. Waiting for {wait_time} seconds...")
            time.sleep(wait_time)

    def run_doorking(self, unique_csv):
        # Run doorking32.exe with the unique CSV file
        try:
            subprocess.run([doorking_path, unique_csv, "/u", "/a"], check=True)
            print(f"Doorking executed successfully with {unique_csv}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to run Doorking: {e}")


    def check_queue(self):
        if queue:
            for unique_csv in queue:
                self.wait_for_doorking_to_finish()
                self.run_doorking(unique_csv)
                queue.remove(unique_csv)

    def run(self):
        while True:
            self.check_queue()
            time.sleep(5)

    class UpdateFileScanner(FileSystemEventHandler):
        def on_created(self, event):
            if not event.is_directory and event.src_path.endswith("update.csv"):
                print("New update file detected")
                unique_csv = rename_csv_file()
                print(unique_csv)


def main():
    observer = Observer()
    updater = DoorKingUpdater()
    event_handler = updater.UpdateFileScanner()
    observer.schedule(event_handler, csv_dir, recursive=False)
    
    observer.start()
    updater.run()

if __name__ == "__main__":
    main()
