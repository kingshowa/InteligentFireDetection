import threading
import time
import cv2

from video_input.video_stream import VideoInput
from detection.fire_detector import FireDetector
from ui.dashboard import FireDetectionDashboard
from communication.esp32_client import ESP32Client
from event_logging.event_logger import EventLogger


class FireDetectionController:
    """
    Orchestrates VideoInput, FireDetector, ESP32, Logger, and Dashboard
    """

    def __init__(self, dashboard: FireDetectionDashboard, logger: EventLogger):
        self.dashboard = dashboard
        self.logger = logger

        # Core modules
        self.video_input = None
        self.detector = FireDetector()
        self.esp32_client = ESP32Client()

        # Threading
        self.running = False
        self.worker = None

        # Fire state (prevents alert spam)
        self.fire_active = False

    # -------------------------------------------------
    # LOGGING (CENTRALIZED)
    # -------------------------------------------------
    def log(self, message: str):
        timestamp, msg = self.logger.log(message)
        self.dashboard.display_log(timestamp, msg)

    # -------------------------------------------------
    # START STREAM
    # -------------------------------------------------
    def start_stream(self, source_type, source_value):
        self.stop_stream()

        try:
            self.video_input = VideoInput(source_type, source_value)
            self.video_input.start()
        except Exception as e:
            self.log(f"Stream error: {e}")
            return

        self.running = True
        self.worker = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self.worker.start()

        self.log(f"Stream started ({source_type})")

    # -------------------------------------------------
    # MAIN PROCESSING LOOP
    # -------------------------------------------------
    def _processing_loop(self):
        while self.running:
            frame, timestamp = self.video_input.read()

            if frame is None:
                self.log("Video stream ended")
                break

            fire, confidence, boxes = self.detector.process_frame(frame, timestamp)

            # Draw bounding boxes
            for (x, y, w, h) in boxes:
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 0, 255),
                    2
                )

            # Fire detected (single alert per event)
            if fire and not self.fire_active:
                self.fire_active = True

                cv2.putText(
                    frame,
                    f"FIRE ({confidence:.2f})",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )

                self.dashboard.trigger_fire_from_thread(confidence)
                self.esp32_client.send_fire_alert(confidence)
                self.log(f"Fire detected (confidence={confidence:.2f})")

            # Fire cleared
            if not fire and self.fire_active:
                self.fire_active = False
                self.dashboard.clear_alert()
                self.log("Fire condition cleared")

            self.dashboard.update_frame_from_thread(frame)
            time.sleep(0.03)

        self.stop_stream()

    # -------------------------------------------------
    # STOP STREAM
    # -------------------------------------------------
    def stop_stream(self):
        self.running = False

        if self.video_input:
            self.video_input.stop()
            self.video_input = None

        self.detector.reset()
        self.fire_active = False

    # -------------------------------------------------
    # USER ACTIONS
    # -------------------------------------------------
    def deactivate_buzzer(self):
        self.detector.reset()
        self.fire_active = False

        self.esp32_client.deactivate_buzzer()
        self.dashboard.clear_alert()
        self.log("Buzzer deactivated by user")

    def shutdown(self):
        self.stop_stream()
        self.esp32_client.shutdown()
        self.log("System shutdown complete")

    # -------------------------------------------------
    # CLEANUP
    # -------------------------------------------------
    def __del__(self):
        self.shutdown()


# -------------------------------------------------
# APPLICATION ENTRY POINT
# -------------------------------------------------
def main():
    logger = EventLogger("events_log.csv")
    dashboard = FireDetectionDashboard(event_logger=logger)
    controller = FireDetectionController(dashboard, logger)

    # 🔗 UI → Controller wiring
    dashboard.on_start_stream = controller.start_stream
    dashboard.on_deactivate_buzzer = controller.deactivate_buzzer
    dashboard.on_stop_system = controller.shutdown

    dashboard.mainloop()


if __name__ == "__main__":
    main()
