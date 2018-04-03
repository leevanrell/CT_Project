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
    
    def __init__(self, log, q, HTTP_SERVER):
        threading.Thread.__init__(self)
        self.running = True
        self.log = log;
        self.q = q;
        self.HTTP_SERVER = HTTP_SERVER
    
    def run(self):
        while self.running:
            self.send_Data()
            sleep(1)
        sleep(1) #Sleep to wait for Data Thread to finish up (Data.join is buggy)
        self.send_Data() 
    
    def send_Data(self):
        while not q.empty():
            if self.isConnected():
                try:
                    document = q.get()
                    r = requests.post(self.HTTP_SERVER, data=json.dumps(document), headers={'content-type': 'application/json'})
                    #r = requests.post(HTTP_SERVER + '/data', data=json.dumps(document)) # converts to json and sends post request
                    if r.status_code != 200:
                        q.add(document)
                        log.error('Logger] status code: %s' % r.status_code)
                    else:
                        log.info('Logger] uploaded document')
                except OSError:
                    log.error('Logger] lost connection')
            else:
               log.error('Logger] no internet connection')
               sleep(1)

    def isConnected(self): 
        try:
            socket.create_connection((HTTP_SERVER, 3000)) 
            return True
        except OSError:
            pass
        return False