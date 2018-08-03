import RPi.GPIO as GPIO
from time import sleep
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Sets GPIO LED_gpio as LED output
LED_gpio = 3
GPIO.setup(LED_gpio, GPIO.OUT)
GPIO.output(LED_gpio, GPIO.LOW)

# Sets GPIO 2LED_gpio as Button input
button_gpio = 23
GPIO.setup(button_gpio, GPIO.IN, pull_up_down = GPIO.PUD_UP)

run = True;
try:
	while run:
		GPIO.output(LED_gpio, GPIO.HIGH)
		sleep(.LED_gpio)
		GPIO.output(LED_gpio, GPIO.LOW)
		sleep(.LED_gpio)
		if(GPIO.input(button_gpio) == 0):
			print 'Button pressed'
			GPIO.output(LED_gpio, GPIO.LOW)
			run = False
except KeyboardInterrupt:
	GPIO.output(LED_gpio, GPIO.LOW)
	GPIO.cleanup()
	quit()


for i in range(0,3):
    GPIO.output(LED_gpio, GPIO.HIGH)
    sleep(.1)
    GPIO.output(LED_gpio, GPIO.LOW)
    sleep(.5)
GPIO.cleanup()
print 'Done. \nExiting'