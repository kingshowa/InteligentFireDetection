import csv
import os
from datetime import datetime
from threading import Lock


class EventLogger:
    """
    Handles persistent event logging using CSV.
    """

    def __init__(self, log_file="events_log.csv"):
        self.log_file = log_file
        self.lock = Lock()
        self._ensure_file_exists()

    # -------------------------------------------------
    # FILE INIT
    # -------------------------------------------------
    def _ensure_file_exists(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "event"])

    # -------------------------------------------------
    # WRITE EVENT
    # -------------------------------------------------
    def log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.lock:
            with open(self.log_file, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, message])

        return timestamp, message

    # -------------------------------------------------
    # READ EVENTS
    # -------------------------------------------------
    def read_all(self, limit: int | None = None):
        """
        Returns a list of (timestamp, message).
        If limit is provided, returns last N entries.
        """
        if not os.path.exists(self.log_file):
            return []

        with open(self.log_file, mode="r", encoding="utf-8") as f:
            reader = list(csv.reader(f))[1:]  # skip header

        if limit:
            reader = reader[-limit:]

        return [(row[0], row[1]) for row in reader]
