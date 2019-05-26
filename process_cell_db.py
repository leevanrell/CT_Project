#!/usr/bin/python3

#downloaded csv from https://www.mylnikov.org/download

import configparser
import sqlite3
import csv

config = configparser.ConfigParser()
config.read('config.txt')
DB_FILE = config['DEFAULT']['DB_FILE']

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS us_cell(id integer PRIMARY KEY, data_source integer, radio_type text, mcc integer, mnc integer, lac integer, cellid integer, lat float, lon float, range integer, created integer, updated integer)""")
first = True
with open("cell.csv") as f:
	data = csv.reader(f)
	next(data)
	for row in data:
		if row[3] in ["310", "311", "312", "316"
			c.execute("""INSERT INTO us_cell VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", row)
conn.commit()
conn.close()
