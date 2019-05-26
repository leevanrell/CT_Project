#!/usr/bin/python3

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
LOG_LOCATION = str(ROOT_LOCATION + 'log/')
if not os.path.exists(LOG_LOCATION):
    os.makedirs(LOG_LOCATION)

log = logging.getLogger()
log.setLevel('DEBUG')

LOG_FILE = LOG_LOCATION + str(datetime.date.today()) + '.log'
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))
log.addHandler(file_handler)

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

    main()
