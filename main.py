import time
import dht
import machine
from machine import Pin
from mqtt import MQTTClient

# Adafruit configuration
AIO_SERVER = "io.adafruit.com"
AIO_PORT = 1883
AIO_USER = "your adafruit username"
AIO_KEY = "your adafruit key"
AIO_TEMP_FEED = "your adafruit username/feeds/temperature"
AIO_HUMID_FEED = "your adafruit username/feeds/humidity"
AIO_LED_FEED = "your adafruit username/feeds/led"

# Setup DHT11
dht11 = dht.DHT11(Pin(15))

# Setup LEDs
temp_leds = [Pin(i, Pin.OUT) for i in range(0, 3)]  # GP0, GP1, GP2 for temperature LEDs (green, yellow, red)
humid_leds = [Pin(i, Pin.OUT) for i in range(3, 6)] # GP3, GP4, GP5 for humidity LEDs (green, yellow, red)

# Variable to keep track of whether LEDs are on or off
leds_on = True

last_temp = 0
last_humid = 0
last_read_time = 0
read_interval = 10  # Read sensor every 10 seconds

def sub_cb(topic, msg):
    global leds_on
    # Callback function to handle messages from Adafruit
    print((topic, msg))
    if topic == bytes(AIO_LED_FEED, 'utf-8'):
        if msg == b'OFF':
            leds_on = False
            for led in temp_leds + humid_leds:
                led.off()
        elif msg == b'ON':
            leds_on = True
            display_temp_leds(last_temp)  # Display LEDs based on the last read temperature
            display_humid_leds(last_humid)  # Display LEDs based on the last read humidity

# Setup MQTT client
client = MQTTClient(AIO_USER, AIO_SERVER, port=AIO_PORT, user=AIO_USER, password=AIO_KEY)
client.set_callback(sub_cb)
client.connect()
client.subscribe(AIO_LED_FEED)

def display_temp_leds(temp):
    if not leds_on:
        return
    # Turn off all temperature LEDs initially
    for led in temp_leds:
        led.off()
    
    # Turn on the appropriate LED based on temperature
    if temp <= 17:
        temp_leds[0].on()  # Green
    elif 18 <= temp <= 22:
        temp_leds[1].on()  # Yellow
    elif temp >= 23:
        temp_leds[2].on()  # Red

def display_humid_leds(humid):
    if not leds_on:
        return
    # Turn off all humidity LEDs initially
    for led in humid_leds:
        led.off()
    
    # Turn on the appropriate LED based on humidity
    if humid < 40:
        humid_leds[0].on()  # Green
    elif 40 <= humid <= 60:
        humid_leds[1].on()  # Yellow
    elif humid > 60:
        humid_leds[2].on()  # Red

def read_sensor_and_publish():
    global last_temp, last_humid
    try:
        # Read DHT11 sensor
        dht11.measure()
        last_temp = dht11.temperature()
        last_humid = dht11.humidity()

        # Publish to Adafruit
        client.publish(AIO_TEMP_FEED, str(last_temp))
        client.publish(AIO_HUMID_FEED, str(last_humid))

        # Display temperature and humidity on LEDs
        display_temp_leds(last_temp)
        display_humid_leds(last_humid)
    except Exception as e:
        print("Error:", e)

while True:
    try:
        current_time = time.time()
        if current_time - last_read_time > read_interval:
            read_sensor_and_publish()
            last_read_time = current_time

        client.check_msg()  # Check for incoming messages
        time.sleep(0.1)

    except Exception as e:
        print("Error:", e)
        time.sleep(10)