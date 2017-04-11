import os ## allows us to talk to the system like in the terminal
from gps import * ## import the gps module
from time import * ## import time for sleeping
import threading ## import threading
from sys import exit ## allows us to use "exit"
import RPi.GPIO as GPIO ## library that lets you control the Pi's GPIO pins
from ISStreamer.Streamer import Streamer ## import the Initial State streamer
from geopy.geocoders import Nominatim ## import the Geopy geocoder
from geopy.exc import GeocoderTimedOut ## import GeocoderTimedOut so we can handle Geopy timeouts
import sys, traceback ## import sys and traceback for exception handling
 
geolocator=Nominatim() ## call the geocoder "geolocator"
 
gpsd = gps(mode=WATCH_ENABLE) ## set gpsd to start gps info
 
prev_input=0 ## set prev_input's initial value to 0
btn_pressed=False ## set btn_pressed's initial value to False
 
## designate bucket name and individual access_key
## a new bucket will be created with every script run
## the access_key tells Initial State which account to send the data to
logger=Streamer(bucket_name="Pi GPS",access_key="[Your Access Key Here]")
 
GPIO.setwarnings(False) ## disables messages about GPIO pins already being in use
GPIO.setmode(GPIO.BOARD) ## indicates which pin numbering configuration to use
 
GPIO.setup(16, GPIO.IN) ## tells it that pin 16 (button) will be giving input
 
GPIO.setup(7, GPIO.OUT) ## tells it that pin 7 (LED) will be outputting
GPIO.output(7, GPIO.HIGH) ## sets pin 7 (LED) to "HIGH" or off
 
## this function will handle any exceptions we don't account for below
## the LED will turn off to tell us that the script has exited
def handleTheUnhandled(type, value, traceback):
    logger.log("msg","The Unhandled was handled") ## stream that an unexpected     exception occured
    GPIO.output(7,GPIO.HIGH) ## turn off the LED
    exit() ## exit the script
 
## when an exception happens that we don't account for, call our script
sys.excepthook = handleTheUnhandled
 
## this thread will look for and collect gpsd info
class GpsPoller(threading.Thread):
 
def __init__(self):
    threading.Thread.__init__(self)
    global gpsd ## bring gpsd in scope
    self.current_value = None
    self.running = True ## setting the thread running to true
 
def run(self):
    global gpsd
    while gpsd.running:
    gpsd.next()
    sleep(10)
 
## this while loop constantly looks for button input
while True:
    ## if no button press
    if (GPIO.input(16) == False and prev_input!=1):
        logger.log("Button 1","Looking for Input") ## stream that button is ready to press
        GPIO.output(7,True) ## switch on pin 7 (LED)
        sleep(0.5) ## wait for 0.5 second
        GPIO.output(7,False) ## switch off pin 7 (LED)
        sleep(1) ## wait for 1 second
    ## when button is pressed
    else:
        if btn_pressed==False:
            logger.log("Button 1","Pressed") ## stream that button has been pressed
            btn_pressed=True ## change btn_pressed so "Pressed" only streams once
            GPIO.output(7,GPIO.LOW) ## turn pin 7 (LED) on
            prev_input=1 ## keep the if statement from executing again
        ## start thread
        if __name__ == '__main__':
            try:
                while True:
                    gpsd.next()
 
                    os.system('clear') ## clear the terminal window to display GPS data
 
                    ## this is handy to see when making sure the script works
                    print
                    print ' GPS reading'
                    print '----------------------------------------'
                    print 'latitude ' , gpsd.fix.latitude
                    print 'longitude ' , gpsd.fix.longitude
                    print 'time utc ' , gpsd.utc,' + ', gpsd.fix.time
                    print 'altitude (m)' , gpsd.fix.altitude
                    print 'eps ' , gpsd.fix.eps
                    print 'epx ' , gpsd.fix.epx
                    print 'epv ' , gpsd.fix.epv
                    print 'ept ' , gpsd.fix.ept
                    print 'speed (m/s) ' , gpsd.fix.speed
                    print 'climb ' , gpsd.fix.climb
                    print 'track ' , gpsd.fix.track
                    print 'mode ' , gpsd.fix.mode
                    print
                    print 'sats ' , gpsd.satellites
 
                    ## the geolocator requires a string so we turn lat and long into one
                    coordinates = str(gpsd.fix.latitude) + "," + str(gpsd.fix.longitude)
 
                    ## stream whatever you'd like to collect from the gps
                    logger.log("Coordinates",coordinates)
                    logger.log("Reported Time",gpsd.utc,)
                    logger.log("Altitude (m)",gpsd.fix.altitude)
                    logger.log("Climb (m/s)",gpsd.fix.climb)
                    logger.log("Lat Error",gpsd.fix.epy)
                    logger.log("Long Error",gpsd.fix.epx)
                    logger.log("Timestamp Error",gpsd.fix.ept)
                    logger.log("Speed (m/s)",gpsd.fix.speed)
                    logger.log("Speed Error",gpsd.fix.eps)
 
                    location=geolocator.reverse(coordinates,timeout=10) ## reverse geocode coordinates
                    logger.log("Location",location.address)
 
            ## if the geocoder times out, stream a message and keep looping
            except GeocoderTimedOut as e:
                logger.log("msg","Geocoder Timeout")
                pass
 
            ## if you press CTRL-C or the systeme exits, print a message and close everything
            except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
                print "\nKilling Thread..."
                GPIO.output(7,GPIO.HIGH) ## turn LED off
                logger.close() ## send any messages left in the streamer
                gpsd.running = False
                gpsd.join() ## wait for the thread to finish what it's doing
                print "Done.\nExiting."
                exit() ## exit the script