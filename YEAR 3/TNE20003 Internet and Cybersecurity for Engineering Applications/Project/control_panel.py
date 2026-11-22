"""
Device 2: Smart Building Control Panel (User Interface)
"""

import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime

BROKER_HOST = "192.168.12.100"
BROKER_PORT = 1883
USERNAME    = "104385170"
PASSWORD    = "104385170"

#topics 
SENSOR_TOPIC  = "104385170/building/sensors"   
COMMAND_TOPIC = "104385170/building/commands"  
PUBLIC_TOPIC  = "public/#"                     

mqtt_client = None


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[Device 2] Connected to MQTT broker successfully.")
        client.subscribe(SENSOR_TOPIC)
        print(f"[Device 2] Subscribed to sensor topic:  {SENSOR_TOPIC}")
        client.subscribe(PUBLIC_TOPIC)
        print(f"[Device 2] Subscribed to public topic:  {PUBLIC_TOPIC}")
        print()
        print_menu()
    else:
        print(f"[Device 2] Connection failed. Return code: {rc}")


def on_message(client, userdata, msg):
    topic   = msg.topic
    payload = msg.payload.decode("utf-8", errors="replace")

    # handle sensor data from device 1
    if topic == SENSOR_TOPIC:
        try:
            data = json.loads(payload)
            print(f"\n[Device 2] [SENSOR DATA] Received at {datetime.now().strftime('%H:%M:%S')}")
            print(f"           Device   : {data.get('device_id', 'N/A')}")
            print(f"           Location : {data.get('location', 'N/A')}")
            print(f"           Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"           Temp     : {data.get('temperature', 'N/A')} °C")
            print(f"           Humidity : {data.get('humidity', 'N/A')} %")
            print(f"           CO2      : {data.get('co2_ppm', 'N/A')} ppm")
            print(f"           Alarm    : {'⚠ ACTIVE' if data.get('alarm_active') else 'OK'}")
        except json.JSONDecodeError:
            print(f"[Device 2] [SENSOR DATA] Raw message on '{topic}': {payload}")
        print()

    # handle public topic messages 
    elif topic.startswith("public"):
        print(f"[Device 2] [PUBLIC] Topic: '{topic}' | Message: {payload}")


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"[Device 2] Unexpected disconnection (rc={rc}).")


def print_menu():
    print("-" * 50)
    print("  CONTROL PANEL — Available Commands")
    print("-" * 50)
    print("  1 → Trigger Alarm")
    print("  2 → Reset Sensor")
    print("  3 → Request Status Check")
    print("  4 → Send custom public message")
    print("  q → Quit")
    print("-" * 50)
    print("  Enter a command: ", end="", flush=True)


def publish_command(action: str, extra: dict = None):
    """Publish a JSON command to the command topic."""
    payload = {"action": action, "issued_by": "ControlPanel-02",
               "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    if extra:
        payload.update(extra)
    result = mqtt_client.publish(COMMAND_TOPIC, json.dumps(payload), qos=1)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"[Device 2] Command sent → '{action}' to {COMMAND_TOPIC}")
    else:
        print(f"[Device 2] Failed to send command (rc={result.rc})")


def command_input_loop():
    """Runs in a separate thread — handles keyboard input from the user."""
    while True:
        try:
            choice = input().strip().lower()
        except EOFError:
            break

        if choice == "1":
            publish_command("trigger_alarm")
        elif choice == "2":
            publish_command("reset_sensor")
        elif choice == "3":
            publish_command("status_check")
        elif choice == "4":
            msg = input("  Enter public message: ").strip()
            sub = input("  Enter sub-topic (e.g. alerts): ").strip() or "general"
            topic = f"public/{sub}"
            mqtt_client.publish(topic, msg, qos=1)
            print(f"[Device 2] Published to public topic '{topic}': {msg}")
        elif choice == "q":
            print("[Device 2] Quitting control panel...")
            mqtt_client.disconnect()
            break
        else:
            print("[Device 2] Unrecognised input.")

        print()
        print_menu()


def main():
    global mqtt_client

    mqtt_client = mqtt.Client(client_id="CONTROL-PANEL-02")
    mqtt_client.username_pw_set(USERNAME, PASSWORD)
    mqtt_client.on_connect    = on_connect
    mqtt_client.on_message    = on_message
    mqtt_client.on_disconnect = on_disconnect

    print("=" * 60)
    print("  TNE20003 Project — Device 2: Building Control Panel")
    print("=" * 60)
    print(f"  Broker   : {BROKER_HOST}:{BROKER_PORT}")
    print(f"  Username : {USERNAME}")
    print(f"  Listens  : {SENSOR_TOPIC}")
    print(f"  Publishes: {COMMAND_TOPIC}")
    print(f"  Listens  : {PUBLIC_TOPIC}")
    print("=" * 60)

    try:
        mqtt_client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    except Exception as e:
        print(f"[Device 2] ERROR: Could not connect to broker — {e}")
        return

    mqtt_client.loop_start()

    input_thread = threading.Thread(target=command_input_loop, daemon=True)
    input_thread.start()

    try:
        input_thread.join()
    except KeyboardInterrupt:
        print("\n[Device 2] Shutting down control panel...")
    finally:
        mqtt_client.loop_stop()
        print("[Device 2] Disconnected.")


if __name__ == "__main__":
    main()