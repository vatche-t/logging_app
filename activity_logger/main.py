import signal
import sys
import time
from config import load_config
from log_manager import LogManager
from browser_monitor import BrowserMonitor
from git_monitor import GitMonitor


class MainApp:
    def __init__(self):
        self.config = load_config()
        self.log_manager = LogManager(self.config["log_destination"])
        self.browser_monitor = BrowserMonitor(self.log_manager)
        self.git_monitor = GitMonitor(self.config["directories"], self.log_manager)

    def run(self):
        self.browser_monitor.start()
        self.git_monitor.start()
        print("Activity logger running on Fedora. Press Ctrl+C to stop.")

        def signal_handler(sig, frame):
            print("Stopping activity logger...")
            self.browser_monitor.stop()
            self.git_monitor.stop()
            self.log_manager.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        while True:
            time.sleep(1)


if __name__ == "__main__":
    app = MainApp()
    app.run()
