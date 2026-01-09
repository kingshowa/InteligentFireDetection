import threading
import cv2
import time

from video_input.video_stream import VideoInput
from detection.fire_detector import FireDetector
from ui.dashboard import FireDetectionDashboard
from communication.esp32_client import ESP32Client


class FireDetectionController:
    """
    Orchestrates VideoInput, FireDetector, ESP32, and Dashboard
    """

    def __init__(self, dashboard: FireDetectionDashboard):
        self.dashboard = dashboard

        # Core modules
        self.video_input = None
        self.detector = FireDetector()
        self.esp32_client = ESP32Client()

        # Threading
        self.running = False
        self.worker = None

        # Fire state (prevents alert spam)
        self.fire_active = False

    # ---------------------------------------------
    # START STREAM
    # ---------------------------------------------
    def start_stream(self, source_type, source_value):
        self.stop_stream()

        try:
            self.video_input = VideoInput(source_type, source_value)
            self.video_input.start()
        except Exception as e:
            self.dashboard.log_event(f" Stream error: {e}")
            return

        self.running = True
        self.worker = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self.worker.start()

        self.dashboard.log_event(f"▶ Stream started ({source_type})")

    # ---------------------------------------------
    # MAIN LOOP
    # ---------------------------------------------
    def _processing_loop(self):
        while self.running:
            frame, timestamp = self.video_input.read()

            if frame is None:
                self.dashboard.log_event("⚠ Video stream ended")
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

            # Fire event handling (ONE alert per event)
            if fire and not self.fire_active:
                self.fire_active = True

                cv2.putText(
                    frame,
                    f" FIRE ({confidence:.2f})",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )

                self.dashboard.trigger_fire_from_thread(confidence)
                self.esp32_client.send_fire_alert(confidence)

            # Reset fire state when fire disappears
            if not fire and self.fire_active:
                self.fire_active = False

            self.dashboard.update_frame_from_thread(frame)
            time.sleep(0.03)

        self.stop_stream()

    # ---------------------------------------------
    # STOP STREAM
    # ---------------------------------------------
    def stop_stream(self):
        self.running = False

        if self.video_input:
            self.video_input.stop()
            self.video_input = None

        self.detector.reset()
        self.fire_active = False

    # ---------------------------------------------
    # USER ACTIONS
    # ---------------------------------------------
    def deactivate_buzzer(self):
        self.detector.reset()
        self.fire_active = False

        self.esp32_client.deactivate_buzzer()

    def shutdown(self):
        self.stop_stream()
        self.esp32_client.shutdown()
        self.dashboard.log_event("System shutdown complete")


# ---------------------------------------------
# APPLICATION ENTRY POINT
# ---------------------------------------------
def main():
    dashboard = FireDetectionDashboard()
    controller = FireDetectionController(dashboard)

    # 🔗 Proper wiring (Dashboard → Controller)
    dashboard.on_start_stream = controller.start_stream
    dashboard.stop_system = controller.shutdown
    dashboard.on_deactivate_buzzer = controller.deactivate_buzzer

    dashboard.mainloop()


if __name__ == "__main__":
    main()
