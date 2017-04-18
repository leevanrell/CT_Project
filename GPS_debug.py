import serial
import time

def isValidLocation(output):
    if(len(output) == 0):
        return False

    check = output.split(',')
    # We only want GPGGA sentences;
    # Checks to see if we have a fix; 1 is fix, 2 is a differential fix.
    return check[0] == "$GPGGA" and int(check[6]) == 2

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

