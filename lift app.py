import network
import socket
import time
from machine import Pin, PWM

# Wi-Fi credentials
SSID = "KLEF-SQ"
PASSWORD = ""  # Add your actual Wi-Fi password

# Initialize floor buttons (outside lift)
floor_buttons = [Pin(i, Pin.IN, pull=Pin.PULL_UP) for i in range(8)]

# Initialize floor select buttons (inside lift)
floor_select_buttons = [Pin(i, Pin.IN, pull=Pin.PULL_UP) for i in range(10, 14)]

# Initialize limit switches for floors
limit_switches = [Pin(i, Pin.IN, pull=Pin.PULL_UP) for i in range(18, 22)]

# Initialize motor control pins
M1_IN = Pin(16, Pin.OUT)  # Motor control pin 1 (for direction)
M2_IN = Pin(26, Pin.OUT)  # Motor control pin 2 (for direction)

# Initialize servo for door
servo = PWM(Pin(28))  # Servo for door control
servo.freq(50)

# Floor constants
floors = [0, 1, 2, 3]

# Connect to Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    print("Connecting to Wi-Fi...")
    while not wlan.isconnected():
        time.sleep(1)
    print("Connected to Wi-Fi:", wlan.ifconfig())
    return wlan.ifconfig()[0]

# Determine the current floor
def get_current_floor():
    for i, switch in enumerate(limit_switches):
        if not switch.value():  # Active low
            print(f"Lift at floor {floors[i]}")
            return floors[i]
    return None  # If no limit switch is activated

# Functions for motor control
def motor_up():
    """Move the lift up."""
    M1_IN.value(1)
    M2_IN.value(0)
    print("Motor running UP.")

def motor_down():
    """Move the lift down."""
    M1_IN.value(0)
    M2_IN.value(1)
    print("Motor running DOWN.")

def motor_stop():
    """Stop the motor."""
    M1_IN.value(0)
    M2_IN.value(0)
    print("Motor stopped.")

# Functions for servo control
def door_open():
    """Simulate door opening."""
    print("Door opening...")
    servo.duty_u16(11000)  # Adjust for continuous rotation clockwise
    time.sleep(3)  # Keep door open for 3 seconds
    servo.duty_u16(0)  # Stop the servo

def door_close():
    """Simulate door closing."""
    print("Door closing...")
    servo.duty_u16(5000)  # Adjust for continuous rotation counter-clockwise
    time.sleep(3)  # Keep door closed for 3 seconds
    servo.duty_u16(0)  # Stop the servo

# Main lift control logic
def move_lift(target_floor):
    """Move the lift to the target floor."""
    current_floor = get_current_floor()
    print(f"Current floor: {current_floor}, Target floor: {target_floor}")

    if current_floor is None:
        print("Error: Unable to determine current floor!")
        return

    if current_floor < target_floor:
        motor_up()
        while get_current_floor() != target_floor:
            time.sleep(0.1)  # Check frequently for floor detection
        motor_stop()
    elif current_floor > target_floor:
        motor_down()
        while get_current_floor() != target_floor:
            time.sleep(0.1)  # Check frequently for floor detection
        motor_stop()

    print(f"Lift reached floor {target_floor}")
    door_open()
    time.sleep(2)  # Simulate the person entering or exiting
    door_close()

# Start HTTP server
def start_server(ip):
    addr = socket.getaddrinfo(ip, 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    print("Server running on:", ip)

    while True:
        cl, addr = s.accept()
        print("Client connected from", addr)
        request = cl.recv(1024)
        print("Request:", request)

        # Determine the current floor
        floor = get_current_floor()
        if floor is None:
            response = "Lift position unknown"
        else:
            response = f"Current floor: {floor}"

        # Send HTTP response
        http_response = f"HTTP/1.1 200 OK\nContent-Type: text/plain\n\n{response}"
        cl.send(http_response)
        cl.close()

# Main loop
if __name__ == "__main__":
    try:
        ip_address = connect_wifi()
        print("Lift system initialized.")
        door_close()  # Ensure door starts closed

        # Start server in a separate thread
        import _thread
        _thread.start_new_thread(start_server, (ip_address,))

        # Monitor button presses
        while True:
            # Check for button presses (outside lift)
            for i, button in enumerate(floor_buttons):
                if not button.value():  # Button pressed
                    print(f"Outside button pressed for floor {floors[i // 2]}")
                    move_lift(floors[i // 2])

            # Check for button presses (inside lift)
            for i, button in enumerate(floor_select_buttons):
                if not button.value():  # Button pressed
                    print(f"Inside button pressed for floor {floors[i]}")
                    move_lift(floors[i])

    except KeyboardInterrupt:
        print("Lift system shutting down.")
        motor_stop()
        door_close()
