import threading
import serial
import os
import time
import sys
from time import sleep
sys.path.append('../')
from  lib.Setup import Setup

import logging
log = logging.getLogger()
log.setLevel('DEBUG')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s] [Detector.%(message)s'))
log.addHandler(stream_handler)


class GPS_Poller(threading.Thread):
    def __init__(self, GPS_TTY):
        threading.Thread.__init__(self)
        self.GPS_TTY = GPS_TTY
        self.running = True
        self.go = True
        self.run_time = 0.0
        self.GPS_Output = ''

    def run(self):
        while self.running:
            # Runs when Data thread tells it to
            if self.go:
                try:
                    self.GPS_Serial = serial.Serial(port=self.GPS_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
                    start = time.time()
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
                    print self.GPS_Output[:-2]
                    print self.run_time
                except serial.SerialException as e:
                    running = False;
                    log.error('GPS disconnected')
                    sleep(1)
                    setup = Setup(log)
                    setup.setup_TTY();
                    count = 0
                    while not setup.configured and count < 10:
                        setup.setup_TTY();
                        count += 0
                        log.error('Retrying setup: %s', count)
                    if not setup.configured:
                        log.error('setup failed')
                        quit()
                    self.GPS_TTY = setup.GPS_TTY

    def isValidLocation(self, output):
        check = output.split(',')
        return len(output) != 0 and check[0] == '$GPGGA' and int(check[6]) != 0 # We only want GPGGA sentences with an Actual Fix (Fix != 0) 

def main():
    setup = Setup(log)
    setup.setup_TTY();
    if not setup.configured:
        log.error('setup failed')
        quit()
    GPS = GPS_Poller(setup.GPS_TTY)
    try:
        GPS.start()
        while GPS.running:
            pass
    except (KeyboardInterrupt, SystemExit): # when you press ctrl+c
        print '\nKilling Thread...'
        GPS.running = False
        GPS.join()
        quit()
    print 'Done'




if __name__ == "__main__":
    if not os.geteuid() == 0:
        log.error('setup] script must be run as root!')
        quit()
    main()

