#!/usr/bin/python
#TODO: add GPIO functionality if possible ?
# need to test detector on pi to see if runs well
LED_gpio = 3 # GPIO pin for LED 
button_gpio = 23 # GPIO pin for Button

import os
import argparse
import modules.setup
import modules.Detector
import modules.DetectorLite

def main():
    addresses = modules.setup.run(log) # gets addresses of sim and gps devices
    log.info('main] running w/config: mode - %s, server - %s, rate - %ss, gps address - %s, sim address - %s' % (MODE, HTTP_SERVER, RATE, addresses['SIM_TTY'], addresses['GPS_TTY']))       
    detector = modules.DetectorLite.Detector(log, HTTP_SERVER, addresses['SIM_TTY'], addresses['GPS_TTY'], RATE) if MODE else modules.Detector.Detector(log, HTTP_SERVER, addresses['SIM_TTY'], addresses['GPS_TTY'], RATE)
    detector.run() # starts detector script
    log.info('main] exit complete.')

if __name__ == '__main__':
    import logging
    log = logging.getLogger()
    log.setLevel('DEBUG')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s] [Detector.%(message)s'))
    log.addHandler(handler)

    if not os.geteuid() == 0:
        log.info('setup] Error: script must be run as root!')
        quit()
    parser = argparse.ArgumentParser(description='SIRtector')
    parser.add_argument('-m', '--mode', default='laptop', help='configures detector to run on laptop/pi; options: pi/laptop') #, action='store', dest='mode')
    parser.add_argument('-l', '--lite', default=False, help='runs lite version of detector', action='store_true') #, action='store', dest='mode')
    parser.add_argument('-s', '--server', default='http://localhost:80', help='sets address and port of http server;') #, action='store', dest='mode')
    parser.add_argument('-r', '--rate', default=5, help='delay between successfully finding a data point and attempting to find another') #, action='store', dest='mode')  
    args = parser.parse_args()

    HTTP_SERVER = 'http://%s:80' % args.server if args.server[:4] != 'http' else args.server
    MODE = True if args.mode == 'pi' else False
    RATE = int(args.rate)
    main()


