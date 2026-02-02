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
                 topic_alert="fire/alert"):
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