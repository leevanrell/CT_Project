#!/usr/bin/python
cluster_IP = 'localhost'
KEYSPACE = 'auresearch'
TABLE = KEYSPACE + '.DetectorData'
PATH = 'data/'

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
import datetime
import csv
import os

def create_Table():
	cluster = Cluster([cluster_IP])
	session = cluster.connect()
	session.set_keyspace(KEYSPACE)

	FOLDER = PATH + '/' + str(datetime.date.today()) + '/'
	if not os.path.exists(FOLDER):
	    os.makedirs(FOLDER)

	# File is named after current date in form YYYY-MM-DD.csv
	file = FOLDER  + 'table.csv'
	order = 'time, MCC, MNC, LAC, Cell_ID, rxl, arfcn, bsic, lat, lon, satellites, GPS_quality, altitude, altitude_units'
	rows = session.execute('SELECT %s FROM %s' % (order, TABLE))
	csvWriter = csv.writer(open(file, 'w'))
	first = ['time', 'MCC', 'MNC', 'LAC', 'Cell_ID', 'rxl', 'arfcn', 'bsic', 'lat', 'lon', 'satellites', 'GPS_quality', 'altitude', 'altitude_units']
	csvWriter.writerow(first) # header row
	csvWriter.writerows(rows) # data from cassandra
	

if __name__ == '__main__':
    create_Table()