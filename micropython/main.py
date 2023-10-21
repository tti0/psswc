import network
import time
import WIFI_CONFIG
import machine
import rp2
import socket

# Configure onboard LED for status
onboard_LED = machine.Pin("LED", machine.Pin.OUT)
onboard_LED.off()

# initialise WiFi connection
rp2.country(WIFI_CONFIG.COUNTRY)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_CONFIG.SSID, WIFI_CONFIG.PSK)

max_wait = 15   # maximum waiting time for WiFi connection in seconds
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print("Waiting to connect...")
    onboard_LED.on()
    time.sleep(0.5)
    onboard_LED.off()
    time.sleep(0.5)

# Flash onboard LED if Wifi connection fails
if wlan.status() != 3:
    print("Network connection failed\n", wlan.status())
    while True:
        onboard_LED.on()
        time.sleep(0.1)
        onboard_LED.off()
        time.sleep(0.1)

# Network connection succeeded
print("Network connection succeeded\n", wlan.ifconfig())