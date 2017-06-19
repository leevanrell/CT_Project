import threading
import serial
import Queue
import pymongo
import os
from pymongo import MongoClient
from time import sleep
from time import gmtime, strftime


GPS_TTY = '/dev/ttyUSB5'

class GPS_Poller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
        self.GPS_Serial.close()
        self.GPS_Output = ''
        self.running = True

    def run(self):
        while self.running:
            self.GPS_Serial.open()
            sleep(.1)
            GPS_Output = self.GPS_Serial.readline()

            while self.isValidLocation(self.GPS_Output) == False:
                sleep(.1) # Need to wait before collecting data
                self.GPS_Output = self.GPS_Serial.readline()
            self.GPS_Serial.close()
            print self.GPS_Output

    def isValidLocation(self, output):
        check = output.split(',')
        return len(output) != 0 and check[0] == '$GPGGA' and int(check[6]) != 0 # We only want GPGGA sentences with an Actual Fix (Fix != 0)

def setupGPS():
    GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
    sleep(.5)
    GPS_Serial.write('$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29<CR><LF> ' + '\r\n') #Configures GPS to only output GPGGA Sentences
    sleep(.5) # Need to wait for device to receive commands
    GPS_Serial.write('$PMTK220,100*2F<CR><LF>' + '\r\n') # Configures Fix interval to 100 ms
    sleep(.5)
    GPS_Serial.write('$PMTK251,115200*1F<CR><LF>' + '\r\n') # Configures Baud Rate to 115200
    sleep(.5)
    GPS_Serial.close() 


def main():
    #setupGPS()
    
    GPS = GPS_Poller()
    try:
        GPS.start()
        while True:
            pass
    except (KeyboardInterrupt, SystemExit): # when you press ctrl+c
        print '\nKilling Thread...'
        GPS.running = False
        GPS.join()

    print 'Done'




if __name__ == "__main__":
    main()

