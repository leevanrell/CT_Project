#!/usr/bin/python
#TODO: add GPIO functionality if possible ?
# need to test detector on pi to see if runs well
LED_gpio = 3 # GPIO pin for LED 
button_gpio = 23 # GPIO pin for Button

import logging
import os
import argparse 
import modules.setup
import modules.Detector
import modules.DetectorLite

def main():
    addresses = modules.setup.run(log)
    log.info('main] running w/config: mode - %s, server - %s, rate - %ss, gps address - %s, sim address - %s' % (MODE, HTTP_SERVER, RATE, addresses['SIM_TTY'], addresses['GPS_TTY']))       
    detector = modules.DetectorLite.Detector(log, HTTP_SERVER, addresses['SIM_TTY'], addresses['GPS_TTY']) if MODE else modules.Detector.Detector(log, HTTP_SERVER, addresses['SIM_TTY'], addresses['GPS_TTY'])
    detector.run()
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
    parser.add_argument('-l', '--lite', default=False, help='configures detector to run on laptop', action='store_true') #, action='store', dest='mode')
    parser.add_argument('-s', '--server', default="http://localhost:80", help='sets address and port of http server;') #, action='store', dest='mode')
    parser.add_argument('-r', '--rate', default=5, help='delay between successfully finding a data point and attempting to find another') #, action='store', dest='mode')  
    args = parser.parse_args()
    if args.lite:
        LITE = True
    if(args.server[:4] != 'http'):#can just list ip and it'll default to port 80, may change in future
        HTTP_SERVER = 'http://%s:80' % args.server
    else:
        HTTP_SERVER = args.server
    if args.mode == 'pi':
        MODE = True
    else:
        MODE = False
    RATE = args.rate
    #main()


