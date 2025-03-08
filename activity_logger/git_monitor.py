import os
import subprocess
import threading
import time


class GitMonitor:
    def __init__(self, directories, log_manager):
        self.directories = directories
        self.log_manager = log_manager
        self.repos = self._find_repos()
        self.running = False
        self.thread = threading.Thread(target=self._run)

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def _run(self):
        while self.running:
            for repo in self.repos:
                self._check_changes(repo)
            time.sleep(60)  # Check every minute

    def _find_repos(self):
        """Find all Git repositories by detecting .git directories."""
        repos = []
        for directory in self.directories:
            for root, dirs, _ in os.walk(directory):
                if ".git" in dirs:
                    repos.append(root)
                    dirs.remove(".git")  # Prevent recursion into .git folder
        return repos

    def _check_changes(self, repo):
        try:
            result = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True)
            changes = []
            for line in result.stdout.splitlines():
                if line:
                    status, path = line.split(maxsplit=1)
                    changes.append({"file": path, "status": status})
            if changes:
                entry = {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "type": "git_change",
                    "repository": repo,
                    "changes": changes,
                }
                self.log_manager.log(entry)
        except Exception as e:
            print(f"Error checking Git repo {repo}: {e}")
