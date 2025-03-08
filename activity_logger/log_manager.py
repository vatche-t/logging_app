import json
import os
import queue
import threading


class LogManager:
    def __init__(self, destination):
        self.destination = destination
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._worker)
        self.thread.daemon = True
        self.thread.start()

    def log(self, entry):
        self.queue.put(entry)

    def stop(self):
        self.queue.put(None)
        self.thread.join()

    def _worker(self):
        log_dir = os.path.dirname(self.destination)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        with open(self.destination, "a") as f:
            while True:
                entry = self.queue.get()
                if entry is None:
                    break
                json.dump(entry, f)
                f.write("\n")
                f.flush()
