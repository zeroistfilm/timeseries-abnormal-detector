import os
import random
import time
import paho.mqtt.client as mqtt_client
import json
from py_singleton import singleton


@singleton
class MqttClient():
    def __init__(self):
        self.broker_address = "haproxy.uniai.co.kr"
        self.broker_port = 31883
        self.client = self.connect_mqtt()
        self.client.loop_start()  # Start the loop

    def connect_mqtt(self) -> mqtt_client:

        def on_connect(client, userdata, flags, reason_code):
            if reason_code == 0:
                print("Connected to MQTT Broker")
            if reason_code > 0:
                print(f"Failed to connect, Returned code: {reason_code}")
                # error processing
                # handle bad identifier

        # error processing
        # handle bad identifier

        def on_disconnect(client, userdata, flags, rc):
            if rc != 0:  # Unexpected disconnection
                print("Unexpected disconnection. Trying to reconnect.")
                while True:
                    try:
                        client.reconnect()
                        break
                    except:
                        print("Failed to reconnect. Trying again in 5 seconds.")
                        time.sleep(5)

        # client 생성 #2
        client_id = f"mqtt_client_{random.randint(0, 1000)}"
        client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, client_id)

        # 콜백 함수 설정 #3
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect

        # broker 연결 #4
        client.connect(host=self.broker_address, port=self.broker_port)
        return client


    def publish(self, topic, msg):

        msg = json.dumps(msg, ensure_ascii=False)

        try:
            result = self.client.publish(topic, msg)
            status = result[0]
            if status == 0:
                print(f"Send `{msg}` to topic `{topic}`")
                pass
            else:
                self.client = self.connect_mqtt()


        except Exception as e:
            print(e)



if __name__ == '__main__':

    import dotenv
    dotenv.load_dotenv()

    while True:
        time.sleep(1)
        mqtt = MqttClient()
        mqtt.publish('dongilps/1/common/1', {'activity': sum([x:=random.randint(0, 100) for _ in range(10)])})
