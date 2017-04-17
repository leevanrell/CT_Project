import time
import serial
import sqlite3
import gps
import os

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
        SIM_Output += SIM_Serial.read(1) 
    
    SIM_Serial.close()

    # Removes Excess Lines and packs into array
    SIM_Output = SIM_Output.split('\n')
    SIM_Output = SIM_Output[4:11]

    return SIM_Output

def getLocation():
    GPS_Serial.open()
    time.sleep(.5)

    GPS_Output = ''
    while isValidLocation(GPS_Output) == False :
        GPS_Output = GPS_Serial.readline()
        print GPS_Output
    
    GPS_Serial.close()

    GPS_Output = GPS_Output.split(',')
    return GPS_Output

def isValidLocation(output):
    check = output.split(',')
    if(output[0] == "$GPGGA"):
        return output[6] == 1 or output[6] == 2;
    else:
        return False;
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

    GPS_Serial.close()


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

