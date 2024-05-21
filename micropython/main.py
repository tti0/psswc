import network
import time
import WIFI_CONFIG
import machine
import rp2
import os
from lib.generateIndexHTML import generateIndexHTMLString
import _thread
import sys
import uasyncio as asyncio

def fatalError(err):
    for i in range(1, 20):
        onboard_LED.on()
        time.sleep(0.1)
        onboard_LED.off()
        time.sleep(0.1)
    raise Exception("psswc fatal error: " + err)
    sys.exit()

async def serve_client(reader, writer):
    # This function runs on each TCP request to the server
    
    # Declare global variables
    global startupAnimationName
    
    # Start handling the request with no error
    thisRequestError = False
    
    # Read 1 KiB from the request stream
    print("Client connected")
    request = await reader.read(1024)
    request = str(request)

    needToResetFlag = False

    # If request is to change the animation, attempt to update currentAnimation.txt
    # If this update is successful, raise flag to reset chip
    if "POST /changeStartupAnimation" in request:
        startOfParam = request.find("newStartupAnimation")
        if startOfParam == -1:
            thisRequestError = "Please make a choice for startup animation"
        else:
            requestedStartupAnimation = request[startOfParam + len("newStartupAnimation") + 1:-1]
            if requestedStartupAnimation != "":
                if requestedStartupAnimation in animationChoices:
                    startupAnimationFile = open("userscripts/startupAnimation.txt", "w")
                    startupAnimationName = startupAnimationFile.write(requestedStartupAnimation)
                    startupAnimationFile.close()
                    startupAnimationName = requestedStartupAnimation
                    needToResetFlag = True
                else:
                    thisRequestError = "Requested animation file does not exist"
            else:
                thisRequestError = "Please make a choice for startup animation"

    # Generate the HTML to send to the client, based on any updates to parameters from attempted changes
    responseHTML = generateIndexHTMLString(startupAnimationName, animationChoices, thisRequestError)
   
    # Set appropriate HTTP status code and send response
    if thisRequestError == False:
        writer.write("HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n")
    else:
        writer.write("HTTP/1.1 400 Bad Request\r\nContent-type: text/html\r\n\r\n")
    writer.write(responseHTML)
    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")
    
    if needToResetFlag:
        print("Animation changed: soft resetting...")
        machine.soft_reset()
    
async def main():
    # Configure onboard LED for status
    onboard_LED = machine.Pin("LED", machine.Pin.OUT)
    onboard_LED.off()

    # Declare global variables
    global animationChoices
    global currentAnimationThread
    global startupAnimationName

    # Read startup animation file and play if it exists
    try:
        startupAnimationFile = open("userscripts/startupAnimation.txt", "r")
        startupAnimationName = startupAnimationFile.readline()
        startupAnimationFile.close()
        
        if startupAnimationName != "":
            try:
                exec("from userscripts." + startupAnimationName[:-3] + " import main as currentAnimationModule")
                currentAnimationThread = _thread.start_new_thread(currentAnimationModule, ())
            except ImportError:
                startupAnimationName = "NOT SET"
        else:
            startupAnimationName = "NOT SET"
    except OSError:
        startupAnimationName = "NOT SET"

    # Initialise WiFi connection
    rp2.country(WIFI_CONFIG.COUNTRY)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # Disable power-saving mode for wireless chip, to ensure server responsiveness
    wlan.config(pm = 0xa11140)
    # Set static IP
    wlan.ifconfig((WIFI_CONFIG.STATIC_IP, WIFI_CONFIG.STATIC_SUBNET_MASK, WIFI_CONFIG.STATIC_GATEWAY, WIFI_CONFIG.STATIC_DNS_SERVER))
    # Attempt WiFi connection
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
        fatalError("Network connection failed, status: " + wlan.status())

    # Network connection succeeded
    print("Network connection succeeded\n", wlan.ifconfig())
    # Load userscripts
    try:
        animationChoices = list(filter(lambda i: i != "startupAnimation.txt", os.listdir("userscripts")))
    except OSError:
        fatalError("`/userscripts` directory could not be found")
    if len(animationChoices) == 0:
        fatalError("`/userscripts` directory is empty")

    # Start web server on port 80
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    while True:
        await asyncio.sleep(0.5)
        
try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
