#!/usr/bin/python3

import serial 
import logging
from time import sleep

class TTY():

    def __init__(self, log):
        self.log = log
        self.SIM_TTY = ''
        self.GPS_TTY = ''
        self.configured = False
        self.setup_TTY()

    def reset(self):
        self.configured = False    
        self.SIM_TTY = ''
        self.GPS_TTY = ''
        setup_TTY(self)

    def setup_TTY(self):
        self.log.info('setting TTY connections')
        configured_SIM = False
        configured_GPS = False

        found_SIM = self.find_SIM_TTY()
        if found_SIM:
            configured_SIM = self.config_SIM()

        found_GPS = self.find_GPS_TTY()
        if found_GPS:
            configured_GPS = self.config_GPS()

        if not configured_GPS or not configured_SIM:
            self.log.error('failed to configure TTY: GPS - %s, SIM - %s' % (configured_GPS, configured_SIM))
        else:
            self.configured = True

    def find_SIM_TTY(self):
        for retry in range(0, 6):
            for count in range(0, 10):
                self.SIM_TTY = '/dev/ttyUSB%s' % count
                try:
                    Serial = serial.Serial(port=self.SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
                    Serial.write(b'AT\r\n')
                    sleep(.5)
                    for i in range(0, 5):
                        check = Serial.readline()
                        self.log.debug(check)
                        if check == 'OK\r\n':
                            self.log.info('set SIM_TTY to ' + self.SIM_TTY)
                            return True
                    Serial.close()
                except serial.SerialException as e:
                    pass
        return False

    def config_SIM(self):
        self.log.info('configuring SIM')
        try:
            SIM_Serial = serial.Serial(port=self.SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
            SIM_Serial.write('AT+CENG=1,1' + '\r\n')
            sleep(.5)
            SIM_Serial.close()
        except serial.SerialException as e:
            self.log.error('lost connection to SIM unit')
            return False
        return True

    def find_GPS_TTY(self):
        for retry in range(0, 6):
            for count in range(0, 10):
                self.GPS_TTY = '/dev/ttyUSB%s' % count
                try:
                    if self.test_GPS(9600) or self.test_GPS(115200): 
                        return True
                except serial.SerialException as e:
                    pass
        return False

    def test_GPS(self, baudrate):
        Serial = serial.Serial(port=self.GPS_TTY, baudrate=baudrate, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        sleep(.5)
        check = Serial.readline()
        Serial.close()
        if check[:1] == '$':
            self.log.info('set GPS_TTY to ' + self.GPS_TTY)
            return True
        return False

    def config_GPS(self):
        self.log.info('configuring GPS')
        try:
            GPS_Serial = serial.Serial(port=self.GPS_TTY, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
            sleep(.5)
            GPS_Serial.write(b'$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29<CR><LF> ' + '\r\n') #Configures GPS to only output GPGGA Sentences
            sleep(.5)
            GPS_Serial.write(b'$PMTK220,100*2F<CR><LF>' + '\r\n')
            sleep(.5)
            GPS_Serial.write(b'$PMTK251,115200*1F<CR><LF>' + '\r\n')
            sleep(.5)
            GPS_Serial.close()
        except serial.SerialException as e:
            self.log.error('lost connection to GPS unit')
            return False
        return True
