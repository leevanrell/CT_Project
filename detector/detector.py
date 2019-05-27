#!/usr/bin/python3
"""

"""

import logging
import configparser
import os
import datetime
import time
import sys
from time import sleep
from pathlib import Path

from lib.create_db import create_db
from lib.DetectorLite import DetectorLite

os.chdir(os.path.dirname(os.path.abspath(__file__)))

root = Path('.')
ROOT_LOCATION = str(root.resolve()) + '/' 
LOG_LOCATION = ROOT_LOCATION + 'log/'
if not os.path.exists(LOG_LOCATION):
    os.makedirs(LOG_LOCATION)

log = logging.getLogger()
log.setLevel('DEBUG')

LOG_FILE1 = LOG_LOCATION + str(datetime.date.today()) + '.info.log'
fh1 = logging.FileHandler(LOG_FILE1)
fh1.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))
fh1.setLevel(logging.INFO)
log.addHandler(fh1)

LOG_FILE2 = LOG_LOCATION + str(datetime.date.today()) + '.debug.log'
fh2 = logging.FileHandler(LOG_FILE2)
fh2.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))
fh2.setLevel(logging.DEBUG)
log.addHandler(fh2)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))
log.addHandler(stream_handler)

def main():
    create_db(DB_FILE, TABLE)
    detector = DetectorLite(log, HTTP_SERVER, DB_FILE, TABLE)
    
    detector.start()
    sleep(5)
    log.info('fin.')

if __name__ == '__main__':
    # if not os.geteuid() == 0:
    #     log.error('script must be run as root!')
    #     quit()
        
    config = configparser.ConfigParser()
    config.read('../config.txt')

    DB_FILE = ROOT_LOCATION + config['DEFAULT']['DB_FILE']
    TABLE = config['DEFAULT']['TABLE']
    HTTP_SERVER = config['DEFAULT']['HTTP_SERVER']
    if HTTP_SERVER[:-1] != '/':
        HTTP_SERVER += '/'

    main()
