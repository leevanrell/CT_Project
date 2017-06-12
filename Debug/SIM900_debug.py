# Creates User interface for playing around with Sim900
# For Debuggin
import serial
from time import sleep

def main():
    SIM_Serial = serial.Serial(
        port='/dev/ttyUSB1',
        baudrate=115200,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,        
        bytesize=serial.EIGHTBITS,
        timeout=0
    )

    if SIM_Serial.isOpen() == False:
        print "Port Failed to Open"

    #SIM_Serial.write('AT+CENG=1,1' + '\r\n')
    #sleep(.5) 


    SIM_Serial.write('AT+CENG?' + '\r\n')
    sleep(.1) 

    SIM_Output = ''
    while SIM_Serial.inWaiting() > 0:
        SIM_Output += SIM_Serial.read(5) 
    SIM_Serial.close()
    print SIM_Output

if __name__ == "__main__":
    main()

