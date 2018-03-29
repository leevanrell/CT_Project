#!/usr/bin/python
import threading 
import Queue 
import socket 
import json 
import os  
import sys 
import datetime 
import logging
from time import sleep 

class Logging_Thread(threading.Thread): 

    Queue q = Queue.Queue()
    
    def __init__(self, log, HTTP_SERVER):
        threading.Thread.__init__(self)
        self.running = True
        self.log = log;
        self.HTTP_SERVER = HTTP_SERVER
    
    def run(self):
        while self.running:
            self.send_Data()
            sleep(1)
        Data.join()
        sleep(.1)
        self.send_Data() # makes sure queue is empty before finishing
    
    def send_Data(self):
        while not q.empty(): # ensures there is a connection to internet/server
            if self.isConnected():
                document = q.get()
                r = requests.post(self.HTTP_SERVER, data=json.dumps(document), headers={'content-type': 'application/json'})
                #r = requests.post(HTTP_SERVER + '/data', data=json.dumps(document)) # converts to json and sends post request
                if r.status_code != 200:
                    q.add(document) # add back to queue if post fails
                    log.error('Logger] status code: %s' % r.status_code)
                else:
                    log.info('Logger] uploaded document')
            else:
               log.error('Logger] no internet connection')
               sleep(1)

    def isConnected(self): # checks to see if detector can connect to the http server
        try:
            socket.create_connection((HTTP_SERVER, 3000)) # connect to the host -- tells us if the host is actually reachable
            return True
        except OSError:
            pass
        return False