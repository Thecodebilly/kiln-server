import network
import time

ssid = "Billy"
password = "Carrabas4"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

timeout = 15
while not wlan.isconnected() and timeout > 0:
    print("Connecting...")
    time.sleep(1)
    timeout -= 1

if wlan.isconnected():
    print("Connected!", wlan.ifconfig())
else:
    print("Failed to connect to Wi-Fi")
