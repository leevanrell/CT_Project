#!/usr/bin/python
cluster_IP = 'localhost'
KEYSPACE = 'auresearch'
TABLE = KEYSPACE + '.DetectorData'
PATH = 'data/'

# setting up logging for cassandra and post requests
import logging
log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
log.addHandler(handler)

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import simplejson
import subprocess
import datetime
import os
import CasstoCSV


class S(BaseHTTPRequestHandler):
    def _set_headers(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

    def _set_index(FOLDER, self):
        FOLDER = PATH + str(datetime.date.today())
        with open('index.html', 'w') as f:
            f.write('''<!DOCTYPE html>\n<html>\n<head>\n<title>Lee's HTTP Server</title>\n</head>\n<body bgcolor=white>\n<table border="0" cellpadding="10">\n<tr>\n<td>\n<h1><font color="black">Cell Tower Data</h1>\n</td>\n</tr>\n</table>\n''')
            for file in os.listdir(str(FOLDER)):
                if file.endswith(".png"):
                    f.write('<p>%s</p>\n<img src="%s" WIDTH=1280 HEIGHT=1280>\n' % (file[:-4], file))
                f.write('</body>\n</html>')

    def _get_data(FOLDER, self)
        CasstoCSV.create_Table() # Gets newest data from cassandra
        subprocess.Popen("nohup sudo Rscript Analysis.R &", shell=True).wait() # does anaylsis of data
        subprocess.Popen("sudo rm nohup.out", shell=True)
        self._set_index(FOLDER) # Creates HTML page

    def do_GET(self):
        FOLDER = PATH + str(datetime.date.today())
        self._set_index(FOLDER)
        # if table.csv hasn't been created for today
        if not os.path.exists(FOLDER):
            log.info('HTTP: Creating Today\'s Folder')
            self._get_data(FOLDER)
        else:
            file = FOLDER + '/table.csv'
            stat = os.stat(file)
            timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(file)) # gets time when table.csv was last edited
            difference = datetime.datetime.now() - timestamp

            # Gets new data if table.csv is older than 10 minutes old
            if(difference.seconds > 10 * 60):
                log.info('HTTP: Updating Data')
                self._get_data(FOLDER)

        if self.path[-4:] == '.png' and os.path.exists(FOLDER + self.path): # and '..' not in self.path  and '/' not in self.path[1:]:
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            with open(FOLDER + self.path, 'rb') as f:
                self.wfile.write(f.read())
        elif self.path == "/":
            self._set_headers()
            with open('index.html', 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        self._set_headers()
        self.data_string = self.rfile.read(int(self.headers['Content-Length']))

        try:
            data = simplejson.loads(self.data_string)
            log.info('HTTP: Adding Data..')
            self.send_response(200)
            self.end_headers()

            session.execute('''INSERT INTO DetectorData(time, MCC, MNC, LAC, Cell_ID, rxl, arfcn, bsic, lat, lon, satellites, gps_quality, altitude, altitude_units) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                (data['time'], data['MCC'], data['MNC'], data['LAC'], data['Cell_ID'], data['rxl'], data['arfcn'], data['bsic'], data['lat'], data['lon'], data['satellites'], data['GPS_quality'], data['altitude'], data['altitude_units']))
            log.info('HTTP: Data has been added..')

        except ValueError,e :
            self.send_response(404)
            self.end_headers()
            log.info('HTTP Error: Bad JSON')

        return

def run(server_class=HTTPServer, handler_class=S, port=80):
    server_address = ('localhost', port)
    httpd = server_class(server_address, handler_class)
    
    log.info('HTTP: Starting http server..')
    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv
    log.info('CASS: Connecting to cluster')
    cluster = Cluster([cluster_IP])
    session = cluster.connect()
    # Creates KEYSPACE if it does not exist (first time setup)
    session.execute('''CREATE KEYSPACE IF NOT EXISTS %s WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }''' % KEYSPACE)
    log.info('CASS: Connecting to %s' % KEYSPACE)
    session.set_keyspace(KEYSPACE)
    #session.execute('DROP TABLE DetectorData')
    # Creates Table if it does not exist (first time setup)
    session.execute('''CREATE TABLE IF NOT EXISTS %s(
        time text,  MCC int, MNC int, LAC text, Cell_ID text, rxl int, arfcn text, bsic text, lat float,
        lon float, satellites int, gps_quality int, altitude float, altitude_units text,
        PRIMARY KEY(time, MCC, MNC, LAC, Cell_ID, rxl))
        WITH CLUSTERING ORDER BY (MCC DESC, MNC ASC, LAC DESC, Cell_ID ASC, rxl DESC);'''% TABLE)

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()