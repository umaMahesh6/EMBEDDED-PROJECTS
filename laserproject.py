from machine import Pin
import time

relay = Pin(16, Pin.OUT)
ldr = Pin(14, Pin.IN, Pin.PULL_DOWN)
laser = Pin(17, Pin.OUT)
laser.value(0)  # Initially turn off the laser

while True:
    if ldr.value():  # If light is detected by LDR
        laser.value(1)  # Turn on the laser
        relay.value(1)  # Turn on the relay
    else:
        laser.value(1)  # Turn off the laser
        relay.value(0)  # Turn off the relay
    time.sleep(0.5)