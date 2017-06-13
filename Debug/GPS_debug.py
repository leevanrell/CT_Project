import threading
import serial
import Queue
import pymongo
import os
from pymongo import MongoClient
from time import sleep
from time import gmtime, strftime

class GPS_Poller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.GPS_Output = ''

    def run(self):
        GPS_Serial.open()
        sleep(.5)
        GPS_Output = GPS_Serial.readline()
        print GPS_Output
        '''
        while not self.isValidLocation(GPS_Output):
            sleep(.1) # Need to wait before collecting data
            GPS_Output = GPS_Serial.readline()
        GPS_Serial.close()
        GPS_Output = GPS_Output.split(',')
        self.GPS_Output = GPS_Output
        '''

    def isValidLocation(output):
        check = output.split(',')
        return len(output) != 0 and check[0] == '$GPGGA' and int(check[6]) != 0 # We only want GPGGA sentences with an Actual Fix (Fix != 0)

def main():
    global GPS_Serial
    GPS_Serial = serial.Serial(
        port='/dev/ttyUSB2',
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=0
    )
    GPS_Serial.close()

    GPS = GPS_Poller()
    GPS.start()
    GPS.join()
    print 'Done'

if __name__ == "__main__":
    main()

