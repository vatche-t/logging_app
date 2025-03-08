from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileHandler(FileSystemEventHandler):
    def __init__(self, log_manager):
        self.log_manager = log_manager

    def on_modified(self, event):
        self.log_manager.log({"type": "file_change", "path": event.src_path})


def monitor_files(directories, log_manager):
    observer = Observer()
    handler = FileHandler(log_manager)
    for directory in directories:
        observer.schedule(handler, directory, recursive=True)
    observer.start()
    return observer
