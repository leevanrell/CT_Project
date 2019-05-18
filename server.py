#!/usr/bin/python3

import urllib2
import datetime
import logging
import psutil
import configparser
import sqlite3

from flask import Flask
from pathlib import Path

root = Path('.')
ROOT_LOCATION = root.resolve()
LOG_LOCATION = root / 'log'
LOG_LOCATION = LOG_LOCATION.resolve()
if not os.path.exists(LOG_LOCATION ):
    os.makedirs(LOG_LOCATION )
os.chdir(ROOT_LOCATION)

log = logging.getLogger()
log.setLevel('DEBUG')

LOG_FILE = LOG_LOCATION + str(datetime.date.today()) + '.log'
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
log.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
log.addHandler(stream_handler)
app = Flask(__name__)

@app.route("/")
def hello():
    self.log.debug("received hello request")
    return datetime.datetime.now()

@app.route("/status")
def get_detector_status():
    self.log.debug("received status request")
    for pid in psutil.pids():
    p = psutil.Process(pid)
    if p.name() == "python" and len(p.cmdline()) > 1 and "detector.py" in p.cmdline()[1]:
        return "running"
    else:
        return "crashed"

@app.route("/towers")
def get_towers():
    self.log.debug("received towers request")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""SELECT DISTINCT mcc,mnc,lac,Cell_ID FROM %s""" % TABLE)
    rows = cur.fetchall()

    towers = [authenticate_towers(conn, row) for row in rows]
    conn.commit()
    conn.close()

    str = ""
    for tower in towers:
        str += tower +'\n'
    return str

def authenticate_towers(conn, row):
    id = row[1] + '-' + row[2] + '-' + row[3] + '-' + row[4]
    #mcc, mnc, lac, Cell_ID
    c = conn.cursor()
    c.execute("""SELECT DISTINCT * FROM towers WHERE id = %s;""" % (id))
    cell_info = c.fetchall()

    if cell_info:
        in_db = cell_info[1]
        lat = cell_info[2]
        lon = cell_info[3]
        range_ = cell_info[4]
        radio_type = cell_info[5]       
    else:
        c.execute("""SELECT DISTINCT * FROM us_cell WHERE mcc = %s AND mnc = %s AND lac = %s AND cell_id = %s;""" % (row[0], row[1], row[2], row[3]))
        cell_lookup = c.fetchall()

        if cell_lookup:
            in_db = True
            lat = cell_lookup[7]
            lon = cell_lookup[8]
            range_ = cell_lookup[9]
            radio_type = cell_lookup[2]
        else:
            in_db = False
            lat = NULL
            lon = NULL
            range_ = NULL
            radio_type = NULL

    c.execute("""SELECT * FROM %s WHERE mcc = %s AND mnc = %s AND lac = %s AND cell_id = %s;""" % (TABLE, row[0], row[1], row[2], row[3]))
    cell_lookup = c.fetchall()
    est_lat, est_lon = triangulate(cell_lookup)

    doc = [id, est_lat, est_lon, in_db, lat, lon, range_, radio_type]
    c.execute("""INSERT OR REPLACE INTO towers VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", doc);
    conn.commit()
    return doc

#http://pythonfiddle.com/python-triangulation-implementati/
def triangulate(points):
    """ Given points in (x,y, signal) format, approximate the position (x,y).

        Reading:
        * http://stackoverflow.com/questions/10329877/how-to-properly-triangulate-gsm-cell-towers-to-get-a-location
        * http://www.neilson.co.za/?p=364
        * http://gis.stackexchange.com/questions/40660/trilateration-algorithm-for-n-amount-of-points
        * http://gis.stackexchange.com/questions/2850/what-algorithm-should-i-use-for-wifi-geolocation
    """
    # Weighted signal strength
    ws = sum(p[2] for p in points)
    points = tuple( (x,y,signal/ws) for (x,y,signal) in points )

    # Approximate
    return (
        sum(p[0]*p[2] for p in points), # x
        sum(p[1]*p[2] for p in points) # y
    )

if __name__ == '__main__':
    if not os.geteuid() == 0:
        log.error('script must be run as root!')
        quit()
        
    config = configparser.ConfigParser()
    config.read('config.txt')

    DB_FILE = ROOT_LOCATION + config['DEFAULT']['DB_FILE']
    TABLE = config['DEFAULT']['TABLE']

    setup = Setup(log, DB_FILE, TABLE)
    setup.create_db()

    app.run(debug=True, use_reloader=True)
