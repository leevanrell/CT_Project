# Creates User interface for playing around with Sim900
# For Debuggin
import threading
import serial
import os
import time
from time import sleep

SIM_TTY = '/dev/ttyUSB1'

class SIM_Poller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.SIM_Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        self.SIM_Serial.close()
        self.running = True
        self.go = True
        self.run_time = 0.0
        self.SIM_Output = ''
    
    def run(self):
        while self.running:
            if self.go:
                start = time.time()
                self.SIM_Serial.open() 
                self.SIM_Serial.write('AT+CENG?' + '\r\n')  # Sends Command to Display current engineering mode settings, serving cell and neighboring cells
                sleep(.1) # Need to wait for device to receive commands 
                # Reads in SIM900 output
                self.SIM_Output = ''
                while self.SIM_Serial.inWaiting() > 0:
                    self.SIM_Output += self.SIM_Serial.read(6) 
                self.SIM_Serial.close()
                # Removes Excess Lines and packs into array
                self.SIM_Output = self.SIM_Output.split('\n')
                self.SIM_Output = self.SIM_Output[4:11]
                #self.go = False
                self.run_time = time.time() - start
                self.go = False

def setupSIM():
    try:
        SIM_Serial = serial.Serial(port=SIM_TTY, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
        SIM_Serial.write('AT+CENG=1,1' + '\r\n') # Configures SIM unit to Engineering mode
        sleep(.5) # Need to wait for device to receive commands
        SIM_Serial.close()
    except serial.SerialException as e:
        print('Error: SIM is not plugged in or the SIM_TTY is Incorrect!')
        quit()


def main():
    setupSIM() 
    SIM = SIM_Poller()
    try:
        SIM.start()
        run = True
        while run:
            if not SIM.go:
                cell_towers = SIM.SIM_Output
                for i in range(len(cell_towers)):
                    # Data in first (serving) cell is ordered differently than first cell,
                    # +CENG:0, '<arfcn>, <rxl>, <rxq>, <mcc>, <mnc>, <bsic>, <cellid>, <rla>, <txp>, <lac>, <TA>'
                    cell_tower = cell_towers[i].split(',')
                    #cell_tower = cell_tower.split(',')
                    arfcn = cell_tower[1][1:]         # Absolute radio frequency channel number
                    rxl = cell_tower[2]               # Receive level (signal stregnth)
                    if(i == 0):
                        bsic = cell_tower[6]          # Base station identity code
                        Cell_ID = cell_tower[7]       # Unique Identifier
                        MCC = cell_tower[4]           # Mobile Country Code
                        MNC = cell_tower[5]           # Mobile Network Code
                        LAC = cell_tower[10]          # Location Area code
                    # +CENG:1+,'<arfcn>, <rxl>, <bsic>, <cellid>, <mcc>, <mnc>, <lac>'    
                    else:
                        bsic = cell_tower[3]          # Base station identity code
                        Cell_ID = cell_tower[4]       # Unique Identifier
                        MCC = cell_tower[5]           # Mobile Country Code
                        MNC = cell_tower[6]           # Mobile Network Code
                        LAC = cell_tower[7][:-2]      # Location Area code
                    print i
                    print 'BSIC: ', bsic
                    print 'CellID:', Cell_ID
                    print 'MCC:', MCC
                    print 'MNC: ', MNC
                    print 'LAC: ', LAC
                    print 'rxl: ', rxl
                    print '\n'
                    SIM.go = True
                run = False


    except (KeyboardInterrupt, SystemExit): # when you press ctrl+c
        print '\nKilling Thread...'
        SIM.running = False
        SIM.join()
        quit()
    print 'Done'

if __name__ == "__main__":
    main()

