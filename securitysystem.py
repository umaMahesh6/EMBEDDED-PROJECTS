import network
import socket
import json
import machine
import time

SSID = "KLEF-SQ"
PASSWORD = ""

# GPIO Pin Configuration
buzzer = machine.Pin(15, machine.Pin.OUT)  # Buzzer on GP15
sensor1 = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_DOWN)  # Sensor 1
sensor2 = machine.Pin(19, machine.Pin.IN, machine.Pin.PULL_DOWN)  # Sensor 2
sensor3 = machine.Pin(20, machine.Pin.IN, machine.Pin.PULL_DOWN)  # Sensor 3

# Emergency mode flag
emergency_mode = False

# Connect to Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

while not wlan.isconnected():
    time.sleep(1)
print("Connected to WiFi:", wlan.ifconfig())

# Function to control buzzer logic
def check_buzzer():
    global emergency_mode
    active_sensors = sensor1.value() + sensor2.value() + sensor3.value()
    inactive_sensors = 3 - active_sensors  # Total sensors - Active ones

    if emergency_mode:
        buzzer.on()  # Emergency mode ON → Buzzer ON
        return True  # Buzzer is ON
    elif active_sensors >= 2:
        buzzer.off()  # 2+ Sensors Active → Buzzer OFF
        return False  # Buzzer is OFF
    elif inactive_sensors >= 2:
        buzzer.on()   # 2+ Sensors Inactive → Buzzer ON
        return True   # Buzzer is ON
    else:
        return False  # Default case

# Create a web server on port 5000
def web_server():
    global emergency_mode

    addr = socket.getaddrinfo("0.0.0.0", 5000)[0][-1]  # Use port 5000
    s = socket.socket()
    s.bind(addr)
    s.listen(5)

    print("Web server running on", addr)

    while True:
        cl, addr = s.accept()
        request = cl.recv(1024).decode()
        print("Request:", request)

        # Extract the URL path
        if "GET /status" in request:
            buzzer_active = check_buzzer()
            response = json.dumps({"buzzer_active": buzzer_active, "emergency_mode": emergency_mode})
            cl.send("HTTP/1.1 200 OK\nContent-Type: application/json\n\n" + response)

        elif "POST /emergency_on" in request:
            emergency_mode = True
            check_buzzer()  # Ensure buzzer turns ON
            response = json.dumps({"message": "Emergency Activated", "buzzer_active": True})
            cl.send("HTTP/1.1 200 OK\nContent-Type: application/json\n\n" + response)

        elif "POST /emergency_off" in request:
            emergency_mode = False
            check_buzzer()  # Ensure buzzer turns OFF based on sensors
            response = json.dumps({"message": "Emergency Deactivated", "buzzer_active": buzzer.value() == 1})
            cl.send("HTTP/1.1 200 OK\nContent-Type: application/json\n\n" + response)

        cl.close()

# Run the web server on port 5000
web_server()
