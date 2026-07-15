import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import time
import math
from smbus2 import SMBus

GPIO.setmode(GPIO.BCM)
client = mqtt.Client(CallbackAPIVersion.VERSION2,'Era')
client.connect('localhost', 1883)
client.loop_start()
time.sleep(1)
client.subscribe('warsztat/kod') #WANZNE
pir = 4
gaz = 17
GPIO.setup(pir, GPIO.IN)
GPIO.setup(gaz, GPIO.IN)
redLed = 23
GPIO.setup(redLed,GPIO.OUT)
red = GPIO.PWM(redLed,1000)
whiteLed = 22
GPIO.setup(whiteLed,GPIO.OUT)
white = GPIO.PWM(whiteLed, 1000)
greenLed = 27
GPIO.setup(greenLed,GPIO.OUT)
green = GPIO.PWM(greenLed, 1000)
blueLed = 18
GPIO.setup(blueLed,GPIO.OUT)
blue=GPIO.PWM(blueLed, 1000)



bus=SMBus(1)
bus.write_i2c_block_data(0x38, 0xBE, [0x08, 0x00])
uzbrojony = True
alarmPir = False
ewakuacjaGaz = False

old_time=time.monotonic()
new_time=time.monotonic()
blink_count =0
old_time_led = time.monotonic()
old_color=' '
blinking=False
now = 0.0
data=[1,1]
with open("kod.txt","r", encoding="utf-8") as file:
	kod=file.read().strip()
def on_message(client, userdata, msg):
	global uzbrojony
	if msg.topic == "warsztat/kod":
		if msg.payload.decode('utf-8').strip() == kod:
			print(msg.payload.decode('utf-8'))
			uzbrojony=False
			client.publish('warsztat/uzbrojony', False)
client.on_message = on_message
def publish (client, temp, hum):
	global data
	client.publish('warsztat/temp', float(hum))
	client.publish('warsztat/hum', float(temp))

def rgb (r=0,g=0,b=0,w=0):
	red.start(float(r))
	green.start(float(g))
	blue.start(float(b))
	white.start(float(w))
def pirdef ():
	global alarmPir, old_time, new_time
	pirStan=GPIO.input(pir)
	if pirStan==1 and uzbrojony == True and alarmPir == False:
		alarmPir=True
		old_time=time.monotonic()
	else:
		pass
def alarmdef ():
	global alarmPir, old_time, new_time, blinking, old_color,blink_count, old_time_led
	new_time = time.monotonic()
	if alarmPir == True:
		print('pir')
		if new_time-old_time >= 5 and blinking==False:
			old_color='red'
			old_time_rgb = time.monotonic()
			blinking=True
		now=time.monotonic()
		if blinking == True and now-old_time_led >= 0.5 and blink_count<= 20:
			if old_color == 'red':
				rgb(0,0,100,0)
				old_color='blue'
				old_time_led=time.monotonic()
			elif old_color =='blue':
				rgb(100,0,0,0)
				old_color='red'
				old_time_led=time.monotonic()
			else:
				pass
			blink_count += 1
		if blink_count > 20:
			blinking=False
			blink_count=0
			alarmPir=False
			rgb(100,0,0,0)
		else:
			pass
def gazdef ():
	global ewakuacjaGaz
	obecnoscgazu=GPIO.input(gaz)
	if obecnoscgazu == 1:
		ewakuacjaGaz = True
def ewakuacjadef ():
	global ewakuacjaGaz
	if ewakuacjaGaz == True:
		rgb(70,30,0,0)
def ahtdef():
	bus.write_i2c_block_data(0x38, 0xAC, [0x33, 0x00])
	while True:
		data= bus.read_i2c_block_data(0x38, 0x71, 7)
		if (data[0] & 0x80) != 0:
			pass
		else:
			break
		humidity_raw = ((data[1] << 12) | (data[2] << 4) | (data[3] >> 4))
		humidity = (humidity_raw / pow(2, 20)) * 100
		temp_raw = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
		temperature = (temp_raw / pow(2, 20)) * 200 - 50
		return [humidity,temperature]

# UWAGA dodac obsluge sumy kontrolnej z 7 bajcie z aht20 w wolnym czasie
client.publish('warsztat/uzbrojony', True)
while True:
	pirdef()
	alarmdef()
	gazdef()
	ewakuacjadef()
	data=ahtdef()
	if data:

		publish(client, data[0], data[1])
		time.sleep(3)
	#kolor=input("podaj kolor")
	#kolor=kolor.split(',')
	#rgb(kolor[0], kolor[1], kolor[2], kolor[3])
