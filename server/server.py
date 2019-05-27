#!/usr/bin/python3
"""

"""

import datetime
import logging
import configparser
import sqlite3
import os
import sys

from flask import Flask, abort, request
from pathlib import Path

from lib.helpers import distance, triangulate
from lib.create_db import create_db

os.chdir(os.path.dirname(os.path.abspath(__file__)))

root = Path('.')
ROOT_LOCATION = str(root.resolve()) + '/' 
LOG_LOCATION = ROOT_LOCATION + 'log/'
if not os.path.exists(LOG_LOCATION):
    os.makedirs(LOG_LOCATION)

log = logging.getLogger()
log.setLevel('DEBUG')

LOG_FILE = LOG_LOCATION + str(datetime.date.today()) + '.log'
file_handler = logging.FileHandler(LOG_FILE)
# file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))
log.addHandler(file_handler)

# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))
# log.addHandler(stream_handler)

app = Flask(__name__)

@app.route("/")
def hello():
    return str(datetime.datetime.now())

@app.route("/update")
def update():
    if not request.json:
        abort(400)

    content = request.json

    print(content)

    # conn = sqlite3.connect(DB_FILE)
    # c = conn.cursor()
    # #c.executemany("""INSERT INTO %s VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""" % TABLE, docs)
    # conn.commit()
    # conn.close()

    return datetime.datetime.now()

@app.route("/towers")
def get_towers():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    s = f'SELECT DISTINCT mcc, mnc, lac, Cell_ID FROM {TABLE};'
    c.execute(s)
    rows = c.fetchall()

    towers = [authenticate_towers(conn, row) for row in rows]
    conn.commit()
    conn.close()

    str = ""
    for tower in towers:
        str += tower +'\n'
    return str

def authenticate_towers(conn, row):
    s = time.time()

    id = row[1] + '-' + row[2] + '-' + row[3] + '-' + row[4]
    c = conn.cursor()
    c.execute(f"""SELECT DISTINCT * FROM towers WHERE id = {id};""")
    cell_info = c.fetchall()
    if cell_info:
        in_db = cell_info[1]
        lat = cell_info[2]
        lon = cell_info[3]
        range_ = cell_info[4]
        radio_type = cell_info[5]       
    else:
        c.execute(f"""SELECT DISTINCT * FROM us_cell WHERE mcc = {row[0]} AND mnc = {row[1]} AND lac = {row[2]} AND cell_id = {row[3]};""")
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

    c.execute(f"""SELECT * FROM {TABLE} WHERE mcc = {row[0]} AND mnc = {row[1]} AND lac = {row[2]} AND cell_id = {row[3]};""")
    cell_lookup = c.fetchall()
    est_lat, est_lon = triangulate(cell_lookup)
    delta = distance([est_lat, est_lon], [lat, lon])

    doc = [id, est_lat, est_lon, in_db, lat, lon, delta, range_, radio_type]
    c.execute("""INSERT OR REPLACE INTO towers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", doc);
    conn.commit()
    log.debug(f'{time.time() - s}')
    return doc

if __name__ == '__main__':
    # if not os.geteuid() == 0:
    #     log.error('script must be run as root!')
    #     quit()
        
    config = configparser.ConfigParser()
    config.read('../config.txt')

    DB_FILE = ROOT_LOCATION + config['DEFAULT']['DB_FILE']
    TABLE = config['DEFAULT']['TABLE']

    create_db(DB_FILE, TABLE)
    app.run(host='0.0.0.0',port=5000,debug=True,use_reloader=True)
