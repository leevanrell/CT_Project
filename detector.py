#!/usr/bin/python3

import logging
import configparser
import os
import sys
import datetime
import time
import Queue
import urllib2
from time import sleep
from pathlib import Path

from lib.Setup import Setup
from lib.DetectorLite import DetectorLite

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

def main():
    setup = Setup(log, DB_FILE, TABLE)
    setup.setup_TTY()
    setup.create_db()

    if not setup.configured:
        log.info('setup failed. exiting.')
        quit()

    detector = DetectorLite(log, DB_FILE, TABLE, setup.SIM_TTY, setup.GPS_TTY)
    
    try:
        detector.start()
    except (KeyboardInterrupt, SystemExit):
        log.info('detected KeyboardInterrupt: stopping job')
        detector.run = False
    sleep(30)

if __name__ == '__main__':
    if not os.geteuid() == 0:
        log.error('script must be run as root!')
        quit()
        
    config = configparser.ConfigParser()
    config.read('config.txt')

    DB_FILE = ROOT_LOCATION + config['DEFAULT']['DB_FILE']
    TABLE = config['DEFAULT']['TABLE']

    log.info('running as: %s, server address: %s' % ("Raspberry Pi" if MODE else "Laptop", HTTP_SERVER))
    main()
