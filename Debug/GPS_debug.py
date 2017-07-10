import threading
import serial
import os
import time
from time import sleep


GPS_TTY = '/dev/ttyUSB0'

class GPS_Poller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
        self.GPS_Serial.close()
        self.running = True
        self.go = True
        self.run_time = 0.0
        self.GPS_Output = ''

    def run(self):
        while self.running:
            # Runs when Data thread tells it to
            if self.go:
                start = time.time()
                self.GPS_Serial.open()
                sleep(.1)
                self.GPS_Output = self.GPS_Serial.readline()
                # Loops until has a valid GPS fix or until script has run 10 secs (~50 loops)
                while not self.isValidLocation(self.GPS_Output) and time.time() - start < 10.0:
                    sleep(.1) # Need to wait before collecting data
                    self.GPS_Output = self.GPS_Serial.readline()
                self.GPS_Serial.close()
                #self.GPS_Output = self.GPS_Output.split(',')
                #self.go = False;
                self.run_time = time.time() - start
                print self.GPS_Output
                print self.run_time

    def isValidLocation(self, output):
        check = output.split(',')
        return len(output) != 0 and check[0] == '$GPGGA' and int(check[6]) != 0 # We only want GPGGA sentences with an Actual Fix (Fix != 0)

def setupGPS():
    try:
        GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
        sleep(.5)
        GPS_Serial.write('$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29<CR><LF> ' + '\r\n') #Configures GPS to only output GPGGA Sentences
        sleep(.5) # Need to wait for device to receive commands
        GPS_Serial.write('$PMTK220,100*2F<CR><LF>' + '\r\n') # Configures Fix interval to 100 ms
        sleep(.5)
        GPS_Serial.write('$PMTK251,115200*1F<CR><LF>' + '\r\n') # Configures Baud Rate to 115200
        sleep(.5)
        GPS_Serial.close() 
    except serial.SerialException as e:
        print('Error: GPS is not plugged in or the GPS_TTY is Incorrect!')
        quit()  

def main():
    setupGPS() 
    GPS = GPS_Poller()
    try:
        GPS.start()
        while True:
            pass
    except (KeyboardInterrupt, SystemExit): # when you press ctrl+c
        print '\nKilling Thread...'
        GPS.running = False
        GPS.join()
        quit()
    print 'Done'




if __name__ == "__main__":
    main()

