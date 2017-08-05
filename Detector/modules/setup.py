#!/usr/bin/python
import serial
import logging
from time import sleep 

def run(log_in):
    global log, GPS_TTY, SIM_TTY
    GPS_TTY = ''
    SIM_TTY = ''
    log = log_in
    setup_TTY() # configures TTY addresses for SIM and GPS
    setup_SIM() # configures SIM module to output cell tower meta data
    setup_GPS() # configures GPS module to only output GPGGA Sentences and increases operating speed
    return {'SIM_TTY': SIM_TTY, 'GPS_TTY': GPS_TTY}


def setup_TTY(): # finds the TTY addresses for SIM and GPS unit if available 
    log.info('setup] setting TTY connections')
    retry = 0 
    configured_SIM = setup_SIM_TTY() # tries to figure out tty address for SIM
    while not configured_SIM and retry < 5: # setup_SIM_TTY is buggy so its worth trying again to find the correct address
        retry += 1
        log.info('setup] retrying SIM TTY config')
        configured_SIM = setup_SIM_TTY() 
    retry = 0
    configured_GPS = setup_GPS_TTY()
    while not configured_GPS and retry < 5: # setup_SIM_TTY is also inconsistent -- running a few times guarantees finding the correct address if its exists
        retry += 1
        log.info('setup] retrying GPS TTY config')
        configured_GPS = setup_GPS_TTY() 
    if not configured_GPS or not configured_SIM: # if gps or sim fail then program gives up
        log.info('setup] Error: failed to configure TTY: GPS - %s, SIM - %s' % (configured_GPS, configured_SIM))
        quit()

def setup_SIM_TTY(): # finds the correct tty address for the sim unit 
    count = 0
    global SIM_TTY
    while count < 10: # iterates through the first 10 ttyUSB# addresses until it finds the correct address
        SIM_TTY = '/dev/ttyUSB%s' % count 
        try:
            Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
            Serial.write('AT' + '\r\n') # sends AT command
            sleep(.5)
            for i in range(0, 5):
                check = Serial.readline()
                if check == 'OK\r\n':
                    log.info('setup] set SIM_TTY to ' + SIM_TTY)
                    return True
            Serial.close()
        except serial.SerialException as e:# throws exception if there is no tty device on the current address
                count += 1
        count += 1  
    return False

def setup_GPS_TTY(): # finds the correct tty address for the GPS unit
    count = 0
    global GPS_TTY
    while count < 10:
        GPS_TTY = '/dev/ttyUSB%s' % count
        try:
            check = test_GPS(9600) # tries default baud rate first         
            if check:
                return True
            else:
                check = test_GPS(115200) # tries configured baud rate 
                if check: 
                    return True
                else:
                    count += 1
        except serial.SerialException as e:
            count += 1 
    return False

def test_GPS(baudrate):
    Serial = serial.Serial(port=GPS_TTY, baudrate=baudrate, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
    sleep(.5)
    check = Serial.readline()
    Serial.close()
    
    if check[:1] == '$': # looks for $
        log.info('setup] set GPS_TTY to ' + GPS_TTY)
        return True
    return False

def setup_SIM(): # configures sim unit to engineering mode -- outputs cell tower meta data
    log.info('setup] configuring SIM')
    try:
        SIM_Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        SIM_Serial.write('AT+CENG=1,1' + '\r\n') # command to set to eng mode
        sleep(.5) # need to wait for device to receive commands
        SIM_Serial.close()
    except serial.SerialException as e:
        log.info('setup] Error: lost connection to SIM unit')
        quit()

def setup_GPS(): # configures gps unit; increase baudrate, output fmt, and output interval
    log.info('setup] configuring GPS')
    try:
        GPS_Serial = serial.Serial(port=GPS_TTY, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)  
        sleep(.5)
        GPS_Serial.write('$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29<CR><LF> ' + '\r\n') #Configures GPS to only output GPGGA Sentences
        sleep(.5) # need to wait for device to receive commands
        GPS_Serial.write('$PMTK220,100*2F<CR><LF>' + '\r\n') # configures fix interval to 100 ms
        sleep(.5)
        GPS_Serial.write('$PMTK251,115200*1F<CR><LF>' + '\r\n') # configures Baud Rate to 115200
        sleep(.5)
        GPS_Serial.close() 
    except serial.SerialException as e:
        log.info('setup] Error: lost connection to GPS unit')
        quit()  