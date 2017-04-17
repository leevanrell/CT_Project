import time
import serial
import sqlite3
import gps
import os

# Configures Sim900 
# Sets to Engineering mode     
def setup_Sim900():

    if SIM_ser.isOpen() == False:
        print "Port Failed to Open"
        quit()

    # AT+CENG=<mode>.<Ncell> : mode = switch on engineering mode, Ncell = display neighbor cell ID
    SIM_Serial.write('AT+CENG=1,1' + '\r\n')

    # Need to wait for device to receive commands
    time.sleep(.5) 

    SIM_Serial.close()


# Returns Array of Strings
# Each string represents a cell tower and contains the cell tower's Metadata
def getCellTowers():
    
    SIM_Serial.open()

    # Displays current engineering mode settings, serving cell and neighboring cells
    SIM_Serial.write('AT+CENG?' + '\r\n')
    
    # Need to wait for device to receive commands
    time.sleep(.5) 

    # Reads in Sim900 output
    SIM_Output = ''
    while SIM_Serial.inWaiting() > 0:
        SIM_output += SIM_Serial.read(1) 
    
    SIM_Serial.close()

    # Removes Excess Lines and packs into array
    SIM_output = SIM_output.split('\n')
    SIM_output = SIM_output[4:11]

    return SIM_output

def getLocation():
    GPS_Serial.open()

    GPS_Output = ''

    while !isValidLocation(SIM_output) {
        GPS_Output = GPS Serial.readline()
        print Output
    }
    GPS_Output = GPS_Output.split(',')
    return GPS_Output

def isValidLocation(output):
    check = output.split(',')
    return (output[6] == 1 || output[6] == 2);

def main():
    #Creates DB for towers and Gps coords
    conn = sqlite3.connect('celltowers.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS CellTowerData(
        t integer, 
        arfcn integer, 
        rxl integer,
        bsic integer,
        Cell_ID text, 
        MCC integer,
        MNC integer,
        LAC integer,
        lat real,
        lon real,
        satellite integer, 
        gps_quality integer, 
        altitude integer,
        altitude_units text
        );''')
    conn.commit()

    SIM_Serial = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=0
    )

    GPS_Serial = serial.Serial(
        port='/dev/ttyUSB1',
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=0
    )

    location = getLocation();

    '''
    
    setup_Sim900()

    #Returns array of strings
    cell_towers = getCellTowers()

    for i in range(len(cell_towers)):
       
        # Data in first (serving) cell is ordered differently than first cell,
        # +CENG:0, "<arfcn>, <rxl>, <rxq>, <mcc>, <mnc>, <bsic>, <cellid>, <rla>, <txp>, <lac>, <TA>"
        cell = cell_towers[i]
        cell = s.split(',')

        if(i == 0):
            arfcn = cell[1]
            rxl = cell[2]
            bsic = cell[6]
            cellid = cell[7]
            mcc = cell[4]
            mnc = cell[5]
            lac = cell[10]

        # +CENG:1+,"<arfcn>, <rxl>, <bsic>, <cellid>, <mcc>, <mnc>, <lac>"    
        else:
            arfcn = cell[1]
            rxl = cell[2]
            bsic = cell[3]
            cellid = cell[4]
            mcc = cell[5]
            mnc = cell[6]
            lac = cell[7]
        # put into Sql table
    '''


if __name__ == "__main__":
    main()

