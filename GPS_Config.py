import serial
import time
import threading
from time import sleep

def main():
    global ser
    ser = serial.Serial(
        port='/dev/ttyUSB1',
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=0
    )

    if ser.isOpen() == False:
        print "Port Failed to Open"
        quit()

    # $PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*2C<CR><LF> 
    # PMTK_API_SET_NMEA_OUTPUT : only prints GGA (GPS Fix Data) every one fix

    # Possibly set Update Rate
    # $PMTK220,100*2F<CR><LF>
    # PMTK_SET_NMEA_UPDATERATE : position fix interval 100 ms
    # Make to baudrate faster to keep up
    # $PMTK251,115200*27<CR><LF> 
    # PMTK_SET_NMEA_BAUDRATE : sets baudrate to 115200
    Test = TestThread()
    try:
    	Test.start()
    	sleep(5)
    	ser.write('$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29<CR><LF> ' + '\r\n')
    	sleep(1)
    	ser.write('$PMTK220,100*2F<CR><LF>' + '\r\n')
    	sleep(1)
    	ser.write('$PMTK251,115200*1F<CR><LF>' + '\r\n')
    	sleep(1)
    	ser = serial.Serial(
        	port='/dev/ttyUSB1',
        	baudrate=115200,
        	parity=serial.PARITY_NONE,
        	stopbits=serial.STOPBITS_ONE,
        	bytesize=serial.EIGHTBITS,
        	timeout=0
     	) 
 
    	while True:
    		sleep(.4)
    	
    except (KeyboardInterrupt, SystemExit): # when you press ctrl+c
        print '\nKilling Thread...'
        Test.running = False
        ser.close()
    print 'pgm ended'



class TestThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True

    def run(self):
        while self.running:
        	string = ser.readline()
        	print string
        	time.sleep(.1)

if __name__ == "__main__":
    main()

