#!/usr/bin/python
import threading
import Queue
import socket
import json
import os 
import sys
import datetime
import logging
import urllib2
import requests
from time import sleep


class Logging_Thread(threading.Thread): 

    def __init__(self, log, q, HTTP_SERVER):
        threading.Thread.__init__(self)
        self.running = True
        self.log = log
        self.q = q
        self.HTTP_SERVER = HTTP_SERVER

    def run(self):
        while self.running:
            self.send_Data()
            sleep(1)
        sleep(1) #Sleep to wait for Data Thread to finish up (Data.join is buggy)
        self.send_Data() 

    def send_Data(self):
        while not self.q.empty():
            if self.isConnected(self.HTTP_SERVER):
                try:
                    document = self.q.get()
                    #r = requests.post(self.HTTP_SERVER, data=json.dumps(document), headers={'content-type': 'application/json'})
                    r = requests.post(self.HTTP_SERVER + '/data', data=json.dumps(document), headers={'content-type': 'application/json'}) # converts to json and sends post request
                    if r.status_code != 200:
                        self.q.put(document)
                        self.log.error('Logger] status code: %s' % r.status_code)
                    else:
                        self.log.info('Logger] uploaded document')
                except OSError:
                    self.log.error('Logger] lost connection')
            else:
               self.log.error('Logger] no internet connection')
               sleep(.5)

    def isConnected(self, HTTP_SERVER): 
        try:
            if url.lower().startswith('http'):
                urllib2.urlopen(HTTP_SERVER, timeout=1)
            else:
                raise ValueError from None
            return True
        except urllib2.URLError as err:
            return False