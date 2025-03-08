import os
import sqlite3
import threading
import time


class BrowserMonitor:
    def __init__(self, log_manager):
        self.log_manager = log_manager
        self.last_timestamp = 0
        self.running = False
        self.thread = threading.Thread(target=self._run)
        # Fedora-specific Edge history path
        self.db_path = os.path.expanduser("~/.config/microsoft-edge/Default/History")

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def _run(self):
        while self.running:
            self._check_history()
            time.sleep(60)  # Check every minute

    def _check_history(self):
        max_retries = 3
        retry_delay = 5  # seconds
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
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
                    entry = {"timestamp": iso_time, "type": "browser_history", "browser": "Edge", "url": url}
                    self.log_manager.log(entry)
                    self.last_timestamp = max(self.last_timestamp, visit_time)
                conn.close()
                break  # Successfully accessed the database
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                print(f"Error accessing browser history: {e} (Is Edge closed?)")
                break  # Give up after max retries

    def _browser_time_to_iso(self, browser_time):
        # Convert browser's timestamp (microseconds since 1601-01-01) to ISO format
        epoch_start = 11644473600000000  # Microseconds from 1601-01-01 to 1970-01-01
        seconds = (browser_time - epoch_start) // 1000000
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(seconds))
