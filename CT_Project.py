import time
import serial
import sqlite3
import gps
import os

# Configures Sim900 
# Sets to Engineering mode     
def setup_Sim900():

    if ser.isOpen() == False:
        print "Port Failed to Open"

    # AT+CENG=<mode>.<Ncell> : mode = switch on engineering mode, Ncell = display neighbor cell ID
    SIM_Serial.write('AT+CENG=1,1' + '\r\n')

    # Need to wait for device to receive commands
    time.sleep(.5) 

    SIM_Serial.close()


# Returns Array of Strings
# Each string represents a cell tower and contains the cell tower's information
def getCellTowers():
    
    SIM_Serial.open()

    # Displays current engineering mode settings, serving cell and neighboring cells
    SIM_Serial.write('AT+CENG?' + '\r\n')
    
    # Need to wait for device to receive commands
    time.sleep(.5) 

    # Reads in Sim900 output
    output = ''
    while SIM_Serial.inWaiting() > 0:
        output += SIM_Serial.read(1) 
    SIM_Serial.close()

    # Removes Excess Lines and packs into array
    output = output.split('\n')
    output = output[4:11]

    SIM_Serial.close()

    return output


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


 
    '''
    
    setup_Sim900()

    #Returns array of strings
    cell_towers = getCellTowers()

    for i in range(len(cell_towers)):
       
        # Data in first (serving) cell is ordered differently than first cell,
        # +CENG:0, "<arfcn>, <rxl>, <rxq>, <mcc>, <mnc>, <bsic>, <cellid>, <rla>, <txp>, <lac>, <TA>"
        s = cell_towers[i]
        s = s.split(',')

        if(i == 0):
            arfcn = s[1]
            rxl = s[2]
            bsic = s[6]
            cellid = s[7]
            mcc = s[4]
            mnc = s[5]
            lac = s[10]

        # +CENG:1+,"<arfcn>, <rxl>, <bsic>, <cellid>, <mcc>, <mnc>, <lac>"    
        else:
            arfcn = s[1]
            rxl = s[2]
            bsic = s[3]
            cellid = s[4]
            mcc = s[5]
            mnc = s[6]
            lac = s[7]
        # put into Sql table
    '''


if __name__ == "__main__":
    main()

