#!/usr/bin/python
from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from ConfigParser import SafeConfigParser
import SocketServer
import simplejson
import subprocess
import datetime
import os
import sys
import CasstoCSV
import csv
from time import sleep

# STEVE IRWIN'S REVENGE : SIR
# setting up logging for server
import logging
log = logging.getLogger()
log.setLevel('INFO')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
log.addHandler(handler)

class S(BaseHTTPRequestHandler):
    def set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def set_index(self, FOLDER):
        CasstoCSV.create_table(FOLDER, session, TABLE) # Gets exports cassandra table to csv
        CasstoCSV.create_towers(FOLDER, session, TABLE) # get list and towers and validates them
        subprocess.call('nohup sudo Rscript Analysis.R %s $ %s' % (LOCATION, FOLDER), shell=True) # Generates maps of data
        with open(FOLDER + '/index.html', 'w') as f: # Creates HTML file
            f.write('''<!DOCTYPE html>\n<html>\n<head>\n<title>Lee's HTTP Server</title>\n</head>\n<body bgcolor=white>\n<table border="0" cellpadding="10">\n<tr>\n<td>\n<h1><font color="black">Cell Tower Data</h1>\n</td>\n</tr>\n</table>\n''')
            reader = csv.reader(open(FOLDER + '/towers.csv'), delimiter=',')
            line = '<p>All Cell Data</p>\n<img src="all.png" WIDTH=960 HEIGHT=960>\n' 
            f.write(line)
            first = True
            for MCC, MNC, LAC, Cell_ID, arfcn, mylnikov, lat, lon in sorted(reader, key=lambda row: row[3], reverse=True):
                if first:
                    first = False
                else:
                    line = '<p>Cell Tower: %s-%s-%s-%s</p>\n<p>mymylnikov: %s</p>\n<img src="%s" WIDTH=960 HEIGHT=960>\n' % (MCC, MNC, LAC, Cell_ID, mylnikov, (Cell_ID + '.png'))
                    f.write(line)
            f.write('</body>\n</html>')
        log.info('[HTTP] made new index.html')

    def get_today(self, FOLDER):
        if not os.path.exists(FOLDER): # checks if folder hasn't been created for today
            log.info('[HTTP] creating today\'s folder')
            self.set_index(FOLDER)
        else:
            file = FOLDER + '/table.csv'
            stat = os.stat(file)
            timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(file)) # gets time when table.csv was last edited
            difference = datetime.datetime.now() - timestamp
            if(difference.seconds > 1 * 60): # gets newer data if table.csv is older than 10 minutes old 
                log.info('[HTTP] updating data')
                self.set_index(FOLDER)

    def do_GET(self):
        FOLDER = PATH + str(datetime.date.today())
        if self.path == '/': # Gets most up to date index.html
            self.set_headers()
            self.get_today(FOLDER)
            with open(FOLDER + '/index.html', 'rb') as f:
                self.wfile.write(f.read())
        elif self.path[-4:] == '.png' and (os.path.exists('data' + self.path) or os.path.exists(FOLDER + '/' + self.path[1:])): # Handles png GET requests
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            if os.path.exists('data' + self.path):
                with open('data' + self.path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                with open(FOLDER + '/' + self.path[1:], 'rb') as f:
                    self.wfile.write(f.read())
        elif os.path.exists('data' + self.path + 'index.html'): # Handles index requests from previous days (fmt: 127.0.0.1/YYYY-MM-DD/)
            self.set_headers()
            with open('data' + self.path + 'index.html', 'rb') as f:
                self.wfile.write(f.read())
        elif os.path.exists('data' + self.path + '/index.html'): # Handles index requests from previous days (fmt: 127.0.0.1/YYYY-MM-DD/)
            self.set_headers()
            with open('data' + self.path + '/index.html', 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write('''<html>\n<head>\n<title>Error 404</title>\n</head></html>''')

    def do_HEAD(self):
        self.set_headers()

    def do_POST(self):
        self.data_string = self.rfile.read(int(self.headers['Content-Length']))
        try:
            data = simplejson.loads(self.data_string)
            log.info('[HTTP] adding data..')
            self.send_response(200)
            self.end_headers()
            session.execute('''INSERT INTO DetectorData(time, MCC, MNC, LAC, Cell_ID, rxl, arfcn, bsic, lat, lon, satellites, gps_quality, altitude, altitude_units) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                (data['time'], data['MCC'], data['MNC'], data['LAC'], data['Cell_ID'], data['rxl'], data['arfcn'], data['bsic'], data['lat'], data['lon'], data['satellites'], data['GPS_quality'], data['altitude'], data['altitude_units']))
            log.info('[HTTP] data has been added..')
        except ValueError,e :
            self.send_response(404)
            self.end_headers()
            log.info('[HTTP] Error: bad JSON')
        return

def run():
    httpd = HTTPServer((IP, PORT), S)  
    log.info('[HTTP] starting http server..')
    httpd.serve_forever()

if __name__ == "__main__":
    if not os.geteuid() == 0:
        log.info('[setup] script must be run as root')
        quit()  

    parser = SafeConfigParser()
    parser.read('config.ini')
    CASSANDRA_IP = parser.get('cassandra_server', 'cassandra_ip') 
    KEYSPACE = parser.get('cassandra_server', 'keyspace')
    TABLE = parser.get('cassandra_server', 'table')
    PATH = parser.get('http_server', 'path')
    LOCATION = parser.get('http_server', 'map_location')
    IP = parser.get('http_server', 'ip')
    PORT = int(parser.get('http_server', 'port'))
  
    log.info('[CASS] connecting to cluster')
    cluster = Cluster([CASSANDRA_IP])
    session = cluster.connect()
    session.execute('''CREATE KEYSPACE IF NOT EXISTS %s WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }''' % KEYSPACE)
    log.info('[CASS] connecting to %s' % KEYSPACE)
    session.set_keyspace(KEYSPACE)
    #session.execute('DROP TABLE DetectorData')
    session.execute('''CREATE TABLE IF NOT EXISTS %s(time text,  MCC int, MNC int, LAC text, Cell_ID text, rxl int, arfcn text, bsic text, lat float, lon float, satellites int, gps_quality int, altitude float, altitude_units text,
        PRIMARY KEY(time, MCC, MNC, LAC, Cell_ID, rxl))
        WITH CLUSTERING ORDER BY (MCC DESC, MNC ASC, LAC DESC, Cell_ID ASC, rxl DESC);''' % TABLE)
    run()
