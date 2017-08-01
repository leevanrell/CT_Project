#!/usr/bin/python

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement

import datetime
import csv
import os
import requests
import json

def create_table(FOLDER, SESSION, TABLE):
	if not os.path.exists(FOLDER):
	    os.makedirs(FOLDER)
	FILE = FOLDER  + '/table.csv'
	order = 'time, MCC, MNC, LAC, Cell_ID, rxl, arfcn, bsic, lat, lon, satellites, GPS_quality, altitude, altitude_units'
	rows = SESSION.execute('SELECT %s FROM %s' % (order, TABLE)) # gets all data from cassandra
	with open(FILE, 'w') as f:
		writer = csv.writer(f)
		writer.writerow(['time', 'MCC', 'MNC', 'LAC', 'Cell_ID', 'rxl', 'arfcn', 'bsic', 'lat', 'lon', 'satellites', 'GPS_quality', 'altitude', 'altitude_units']) # header row
		writer.writerows(rows) # data from cassandra

def create_towers(FOLDER, SESSION, TABLE):
	FILE = FOLDER + '/towers.csv'
	order = 'MCC, MNC, LAC, Cell_ID, arfcn'
	rows = SESSION.execute('SELECT %s FROM %s' % (order, TABLE)) # gets all data from cassandra
	unique = set()
	for row in rows:
		unique.add(row) # collect all unique towers and adds them into set
	with open(FILE, 'w') as f:
		writer = csv.writer(f)
		writer.writerow(['MCC', 'MNC', 'LAC', 'Cell_ID',  'arfcn','mylnikov', 'lat', 'lon']) # header row
		for row in unique:
			r = requests.get('http://api.mylnikov.org/geolocation/cell?v=1.1&data=open&mcc=%s&mnc=%s&lac=%s&cellid=%s' % (row[0], row[1], int(row[2], 16), int(row[3], 16)))
			response = json.loads(r.text)
			writer.writerow([row[0], row[1], row[2], row[3], row[4], 'PASS', response['data']['lat'], response['data']['lon']]) if response['result'] == 200 else writer.writerow([row[0], row[1], row[2], row[3], row[4], 'FAIL', 'NULL', 'NULL'])
'''
if __name__ == '__main__': # for testing as a standalone script
	FOLDER = 'data/' + str(datetime.date.today())
	cluster_IP = 'localhost'
	KEYSPACE = 'auresearch'
	cluster = Cluster([cluster_IP])
	SESSION = cluster.connect()
	SESSION.set_keyspace(KEYSPACE)
	TABLE = KEYSPACE + '.DetectorData'

	create_table(FOLDER, SESSION, TABLE)
	create_towers(FOLDER, SESSION, TABLE)
'''