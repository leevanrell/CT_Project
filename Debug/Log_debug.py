DB_URL = 'mongodb://localhost:27017/'

import threading
import serial
import pymongo
import os
import socket
import Queue
from pymongo import MongoClient
from time import sleep

class Logging_Thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.client = MongoClient(DB_URL)
        self.db = self.client['Test_DB'] 
        self.collection = self.db['Test_Collection']
        self.running = True
    
    def run(self):
        global q
        while self.running:
            while not q.empty():
                if self.isConnected():
                    self.collection.insert_one(q.get())
                else:
                    sleep(.5)
            sleep(.5)
        while not q.empty():
            if self.isConnected():
                collection.insert_one(q.get())
            else:
                sleep(.5)
    
    def isConnected(self):
        try:
            socket.create_connection(("www.google.com", 80)) # connect to the host -- tells us if the host is actuallyreachable
            return True
        except OSError:
            pass
        return False

def main():
    #setupGPS()
    global q
    q = Queue.Queue()
    print 'shit'
    for i in range(1, 1000):
        entry = {'int': i}
        q.put(entry)
    print 'tst'
    Logger = Logging_Thread()
    try:
        Logger.start()
        while True:
            pass
    except (KeyboardInterrupt, SystemExit): # when you press ctrl+c
        print '\nKilling Thread...'
        GPS.running = False
        GPS.join()

    print 'Done'

if __name__ == "__main__":
    main()
