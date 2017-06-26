cluster_IP = 'localhost'
KEYSPACE = 'auresearch'
TABLE = KEYSPACE + '.DetectorData'


#!/usr/bin/python

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

class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        f = open("index.html", "r")
        self.wfile.write(f.read())

    def do_HEAD(self):
        self._set_headers()
    

    def do_POST(self):
        
        self._set_headers()
        self.data_string = self.rfile.read(int(self.headers['Content-Length']))


        try:
            data = simplejson.loads(self.data_string)
            log.info('Adding Data..')
            self.send_response(200)
            self.end_headers()

            '''
            session.execute('INSERT INTO DetectorData(time, arfcn, rxl, bsic, Cell_ID, MCC, MNC, LAC, lat, lon, satellites, gps_quality, altitude, altitude_units) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', 
                (data['time'], data['arfcn'], data['rxl'], data['bsic'], data['Cell_ID'], data['MCC'], data['MNC'], data['LAC'], data['lat'], data['lon'], data['satellites'], data['GPS_quality'], data['altitude'], data['altitude_units']))
            log.info('Data has been added..')
            '''

        except ValueError,e :
            self.send_response(404)
            log.info('Error: Bad JSON')

        return


def run(server_class=HTTPServer, handler_class=S, port=80):
    
    server_address = ('localhost', port)
    httpd = server_class(server_address, handler_class)
    
    log.info('Starting http server..')
    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv

    log.info('Connecting to cluster')
    cluster = Cluster([cluster_IP])
    # Creates KEYSPACE if it does not exist (first time setup)
    session = cluster.connect()
    session.execute('''CREATE KEYSPACE IF NOT EXISTS %s WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }''' % KEYSPACE)
    log.info('Connecting to %s' % KEYSPACE)
    session.set_keyspace(KEYSPACE)
    # session.execute('''DROP TABLE DetectorData''')
    # Creates Table if it does not exist (first time setup)
    session.execute('''CREATE TABLE IF NOT EXISTS DetectorData(
        time float, arfcn text, rxl int, bsic text, Cell_ID text, MCC int, MNC int, 
        LAC text, lat float, lon float, satellites int, gps_quality int, altitude float, 
        altitude_units text, PRIMARY KEY(time, MCC, MNC, LAC, Cell_ID, rxl));''')


    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()