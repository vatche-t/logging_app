import os
import sqlite3
import threading
import time
import shutil
import tempfile
import sys
from datetime import datetime, timezone, timedelta

class BrowserMonitor:
    def __init__(self, log_manager):
        self.log_manager = log_manager
        # Initialize last_timestamp as start of today in Chromium format
        self._set_today_start_timestamp()
        print(f"Initial last_timestamp (Chromium): {self.last_timestamp}")
        self.running = False
        self.thread = threading.Thread(target=self._run)
        self.db_path = os.path.expanduser("~/.config/microsoft-edge/Default/History")

        if not os.path.exists(self.db_path):
            print(f"Browser history database not found: {self.db_path}")
            sys.exit(1)

    def _set_today_start_timestamp(self):
        # Start of today in UTC, converted to Chromium timestamp (microseconds since 1601-01-01)
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        chromium_epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
        self.last_timestamp = int((today - chromium_epoch).total_seconds() * 1_000_000)

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
        # Use tempfile to copy the database safely while Edge is running
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

            # Calculate end of today for filtering
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            chromium_epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
            start_of_today = int((today_start - chromium_epoch).total_seconds() * 1_000_000)
            end_of_today = start_of_today + (24 * 60 * 60 * 1_000_000) - 1

            # Query for today's visits only
            cursor.execute(
                """
                SELECT urls.url, visits.visit_time
                FROM visits
                JOIN urls ON visits.url = urls.id
                WHERE visits.visit_time BETWEEN ? AND ?
                ORDER BY visits.visit_time ASC
                """,
                (start_of_today, end_of_today),
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
                # Update last_timestamp to the latest visit time (optional, if tracking beyond today)
                self.last_timestamp = max(self.last_timestamp, visit_time)

            conn.close()
        except sqlite3.Error as e:
            print(f"Error reading copied browser history: {e}")

    def _browser_time_to_iso(self, browser_time):
        # Convert Chromium timestamp (microseconds since 1601-01-01) to ISO format
        chromium_epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
        visit_datetime = chromium_epoch + timedelta(microseconds=browser_time)
        return visit_datetime.isoformat()

# Example usage (assuming log_manager is defined)
class DummyLogManager:
    def log(self, entry):
        print(entry)

if __name__ == "__main__":
    log_manager = DummyLogManager()
    monitor = BrowserMonitor(log_manager)
    monitor.start()
    try:
        time.sleep(300)  # Run for 5 minutes
    except KeyboardInterrupt:
        monitor.stop()