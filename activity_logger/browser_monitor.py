import os
import sqlite3
import threading
import time
import shutil
import tempfile
import sys


class BrowserMonitor:
    def __init__(self, log_manager):
        self.log_manager = log_manager
        self.last_timestamp = 0
        self.running = False
        self.thread = threading.Thread(target=self._run)
        self.db_path = os.path.expanduser("/home/vatche/.config/microsoft-edge/Default/History")

        if not os.path.exists(self.db_path):
            print(f"Browser history database not found: {self.db_path}")
            sys.exit(1)

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def _run(self):
        while self.running:
            self._safe_check_history()
            time.sleep(60)  # Check every minute

    def _safe_check_history(self):
        # Step 1: Copy to a temporary file
        with tempfile.NamedTemporaryFile(delete=True) as tmpfile:
            try:
                shutil.copy2(self.db_path, tmpfile.name)
                self._check_history(tmpfile.name)
            except Exception as e:
                print(f"Failed to copy browser database: {e}")

    def _check_history(self, copied_db_path):
        try:
            conn = sqlite3.connect(f"file:{copied_db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT urls.url, visits.visit_time
                FROM visits
                JOIN urls ON visits.url = urls.id
                WHERE visits.visit_time > ?
                ORDER BY visits.visit_time ASC
                """,
                (self.last_timestamp,),
            )
            visits = cursor.fetchall()
            for url, visit_time in visits:
                iso_time = self._browser_time_to_iso(visit_time)
                entry = {
                    "timestamp": iso_time,
                    "type": "browser_history",
                    "browser": "Edge",
                    "url": url,
                }
                self.log_manager.log(entry)
                self.last_timestamp = max(self.last_timestamp, visit_time)
            conn.close()
        except sqlite3.Error as e:
            print(f"Error reading copied browser history: {e}")

    def _browser_time_to_iso(self, browser_time):
        epoch_start = 11644473600000000
        seconds = (browser_time - epoch_start) // 1000000
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(seconds))
