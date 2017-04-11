# Creates User interface for playing around with Sim900
# For Debugging
def main():
    ser = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=0
    )

    if ser.isOpen() == False:
        print "Port Failed to Open"

    input= ''
    run = True
    while run :
        # get keyboard input
        input = raw_input(">> ")
        if input == 'exit':
            ser.close()
            run = False;
        else:
            # send the character to the device
            ser.write(input + '\r\n')
            output = ''
            time.sleep(.5)
            while ser.inWaiting() > 0:
             output += ser.read(1)

            if output != '':
                print ">>" + output
if __name__ == "__main__":
    main()

