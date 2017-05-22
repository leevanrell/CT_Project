import serial
import time

def isValidLocation(output):
    # $GPGGA,195718.000,3236.3567,N,08529.2146,W,1,05,1.47,180.6,M,-29.4,M,,*53
    check = output.split(',')
    return len(output) != 0 and check[0] == "$GPGGA" and int(check[6]) == 2



def main():
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


    ser.write('$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*2C<CR><LF> ' + '\r\n')
    print ser.readline()
    string = ''
    while True:
        string = ser.readline()
        print string, isValidLocation(string)
        time.sleep(.4)


if __name__ == "__main__":
    main()

