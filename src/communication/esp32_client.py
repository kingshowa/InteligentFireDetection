import json
import time
import paho.mqtt.client as mqtt


class ESP32Client:
    """
    Handles communication with ESP32 via MQTT
    """

    def __init__(self,
                 broker="broker.hivemq.com",
                 port=1883,
                 topic_alert="fire/system/alert"):
        self.broker = broker
        self.port = port
        self.topic_alert = topic_alert

        self.client = mqtt.Client()
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def send_fire_alert(self, confidence):
        payload = {
            "event": "FIRE",
            "confidence": confidence,
            "timestamp": time.time()
        }
        self.client.publish(self.topic_alert, json.dumps(payload))
        print("FIRE alert sent")

    def deactivate_buzzer(self):
        payload = {"event": "OFF"}
        self.client.publish(self.topic_alert, json.dumps(payload))
        print("Alarm deactivated")

    def shutdown(self):
        self.client.loop_stop()
        self.client.disconnect()


# -------------------------------------------------
# STANDALONE MQTT TEST
# -------------------------------------------------
# if __name__ == "__main__":
#     esp = ESP32Client()
#
#     try:
#         print("Sending FIRE alert in 3 seconds...")
#         time.sleep(3)
#
#         # 🔥 Trigger fire alarm
#         # esp.send_fire_alert(confidence=0.92)
#
#         # 🔔 Keep alarm active for 10 seconds
#         # time.sleep(10)
#
#         # 🛑 Turn off alarm
#         esp.deactivate_buzzer()
#
#     finally:
#         time.sleep(1)
#         esp.shutdown()
#         print("MQTT test finished")
