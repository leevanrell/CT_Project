import configparser
config = configparser.ConfigParser()
config.read('config.txt')

DB_FILE = config['DEFAULT']['DB_FILE']


import sqlite3

conn = sqlite3.connect(DB_FILE)

c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS full_cell(id integer PRIMARY KEY, data_source integer, radio_type text, mcc integer, mnc integer, lac integer, cellid integer, lat float, lon float, range integer, created integer, updated integer)""")

import csv
with open("cell.csv") as f:
	data = csv.reader(f)
	next(data)
	c.executemany("""INSERT INTO full_cell VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", data);
	#print(f.readline())

c.execute("""CREATE TABLE IF NOT EXISTS us_cell(id integer PRIMARY KEY, data_source integer, radio_type text, mcc integer, mnc integer, lac integer, cellid integer, lat float, lon float, range integer, created integer, updated integer)""")

c.execute("""SELECT * FROM full_cell WHERE mcc IN (310, 311, 312, 316);""")
res = c.fetchall()
c.executemany("""INSERT INTO us_cell VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", res);

c.execute("""DROP TABLE IF EXISTS full_cell;""")
conn.commit()
conn.close()

#310, 311, 312, 316