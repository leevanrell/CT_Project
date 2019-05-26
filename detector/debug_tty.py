import serial
from time import sleep


SIM_TTY = '/dev/ttyUSB0' 
try:
    Serial = serial.Serial(port=SIM_TTY, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
    Serial.write(b'AT\r\n')
    sleep(1)
    for i in range(0, 5):
        check = Serial.readline()
        print(check)
    Serial.close()
except serial.SerialException as e:
    print('no connection')