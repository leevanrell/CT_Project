#!/usr/bin/python
import threading
import json
import requests
from time import sleep

import lib.Helper as Helper


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
            if Helper.isConnected(self.HTTP_SERVER):
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