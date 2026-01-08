import cv2
import time
import yt_dlp
import os
import tempfile


class VideoInput:
    """
    Handles video input from:
    - Camera
    - Local video file
    - URL (YouTube, remote)
    """

    def __init__(self, source_type: str, source_value: str, width=640, height=480):
        self.source_type = source_type
        self.source_value = source_value
        self.width = width
        self.height = height

        self.cap = None
        self.running = False
        self.video_path = None

    # ----------------------------
    # INITIALIZATION
    # ----------------------------
    def start(self):
        if self.source_type == "Camera":
            index = int(self.source_value) if self.source_value else 0
            self.cap = cv2.VideoCapture(index)

        elif self.source_type == "Local Video":
            self.cap = cv2.VideoCapture(self.source_value)

        elif self.source_type == "URL":
            self.video_path = self._download_video(self.source_value)
            self.cap = cv2.VideoCapture(self.video_path)

        else:
            raise ValueError("Unsupported video source")

        if not self.cap.isOpened():
            raise RuntimeError("Failed to open video source")

        self.running = True

    # ----------------------------
    # FRAME READING
    # ----------------------------
    def read(self):
        if not self.running:
            return None, False

        ret, frame = self.cap.read()
        if not ret:
            return None, False

        frame = cv2.resize(frame, (self.width, self.height))
        timestamp = time.time()

        return frame, timestamp

    # ----------------------------
    # CLEANUP
    # ----------------------------
    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        if self.video_path and os.path.exists(self.video_path):
            os.remove(self.video_path)

    # ----------------------------
    # URL VIDEO HANDLING
    # ----------------------------
    def _download_video(self, url):
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "video.mp4")

        ydl_opts = {
            "outtmpl": output_path,
            "format": "mp4",
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return output_path
