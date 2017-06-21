import RPi.GPIO as GPIO
from time import sleep
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Sets GPIO 3 as LED output
GPIO.setup(3, GPIO.OUT)
GPIO.output(3, GPIO.LOW)

# Sets GPIO 23 as Button input
button_gpio = 23
GPIO.setup(button_gpio, GPIO.IN, pull_up_down = GPIO.PUD_UP)

run = True;
try:
	while run:
		GPIO.output(3, GPIO.HIGH)
		sleep(.3)
		GPIO.output(3, GPIO.LOW)
		sleep(.3)
		if(GPIO.input(button_gpio) == 0):
			print 'Button pressed'
			GPIO.cleanup()

except KeyboardInterrupt:
	GPIO.cleanup()
	quit()
