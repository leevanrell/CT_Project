#!/usr/bin/python
import argparse
import logging
import configparser
import os
import sys
import datetime
import time
import Queue
import urllib2
from time import sleep

import lib.Helper as Helper
from lib.Setup import Setup

LED_gpio = 3# GPIO pin for LED
button_gpio = 23# GPIO pin for Button
LOG_LOCATION = 'data/log/'

os.chdir(os.path.dirname(os.path.abspath(__file__)))

if not os.path.exists('./data'):
    os.makedirs('./data')
if not os.path.exists('./data/log'):
    os.makedirs('./data/log')
if not os.path.exists('./data/backup'):
    os.makedirs('./data/backup')

log = logging.getLogger()
log.setLevel('DEBUG')

LOG_FILE = LOG_LOCATION + str(datetime.date.today()) + '.log'
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter('[%(asctime)s] [Detector.%(message)s'))
log.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s] [Detector.%(message)s'))
log.addHandler(stream_handler)


def main():
    setup = Setup(log)
    setup.setup_TTY()
    if not setup.configured:
        log.info('main] setup failed. exiting.')
        quit()
    if MODE:
        pi(setup)
    else:
        laptop(setup)
    log.info('main] exiting')


def laptop(setup):
    from lib.Logging_Thread import Logging_Thread
    from lib.Data_Thread import Data_Thread

    q = Queue.Queue()
    Data = Data_Thread(log, q, setup.SIM_TTY, setup.GPS_TTY, TIMEOUT, RATE)
    Logger = Logging_Thread(log, q, HTTP_SERVER)
    log.info('main] starting threads')
    Data.start()
    Logger.start()

    try:
        while Data.running and Logger.running:
            pass
        Data.running = False
        Data.join()
        Logger.running = False
        Logger.join()
    except (KeyboardInterrupt, SystemExit):
        log.info('main] detected KeyboardInterrupt: killing threads.')
        Data.running = False
        Logger.running = False
        Data.join()
        Logger.join()


def pi(setup):
    from lib.DetectorLite import DetectorLite
    detector = DetectorLite(log, HTTP_SERVER, setup.SIM_TTY, setup.GPS_TTY, TIMEOUT, RATE)
    try:
        detector.start()
    except (KeyboardInterrupt, SystemExit):
        log.info('main] detected KeyboardInterrupt: stopping job')
        detector.run = False


def isPi():
    try:
        import RPi.GPIO as GPIO
        return True
    except ImportError:
        return False


if __name__ == '__main__':
    if not os.geteuid() == 0:
        log.error('setup] script must be run as root!')
        quit()
    config = configparser.ConfigParser()
    config.read('config.txt')

    HTTP_SERVER = config['DEFAULT']['HTTP_Server']
    TIMEOUT = int(config['DEFAULT']['TIMEOUT'])
    RATE = int(config['DEFAULT']['RATE'])
    MODE = isPi()

    parser = argparse.ArgumentParser(description='SIR Detector')
    parser.add_argument('-s', '--server', default=HTTP_SERVER, help='sets address and port of http server;') #, action='store', dest='mode')
    parser.add_argument('-t', '--timeout', default=TIMEOUT, help='amount of time detector takes to get data before giving up;')
    parser.add_argument('-r', '--rate', default=RATE, help='amount of time detector waits before attempting to collect more data;')
    args = parser.parse_args()

    HTTP_SERVER = 'http://%s:3000/data' % args.server if(args.server[:4] != 'http') else args.server
    TIMEOUT = args.timeout
    RATE = args.rate
    if not Helper.isConnected(HTTP_SERVER):
        log.warning('setup] cannot connect to %s'% HTTP_SERVER)
    log.info('setup] running as: %s, server address: %s' % ("Raspberry Pi" if MODE else "Laptop", HTTP_SERVER))
    main()
