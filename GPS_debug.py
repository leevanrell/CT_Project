import serial
import time

def isValidLocation(output):
    # $GPGGA,195718.000,3236.3567,N,08529.2146,W,1,05,1.47,180.6,M,-29.4,M,,*53
    check = output.split(',')
    return len(output) == 0 and check[0] == "$GPGGA" and int(check[6]) == 2



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

    string = ''
    while True:
        string = ser.readline()
        print string
        print isValidLocation(string)
        print ""
        time.sleep(.4)


if __name__ == "__main__":
    main()

