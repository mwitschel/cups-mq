#!/usr/bin/python
#################################################################
#
# cupsmq-ftpd.py - description
#
#
# Copyright (C) 2011
# Permission is hereby granted to use and distribute this code,
# with or without modifications, provided that this copyright
# notice is copied with it. Like anything else that's free,
# cupsmq-ftpd.py is provided *as is* and comes with no
# warranty of any kind, either expressed or implied. In no
# event will the copyright holder be liable for any damages
# resulting from the use of this software.
#
# Author: Matthias Witschel
# Email: mwitsch@gmail.com
# Date: Tue Dec 20 22:39:59 CET 2011
#
# Repository Name: https://cups-mq.googlecode.com/svn/trunk/frontend
# Revision: 0
#
################################################################


### import modules
import cups
import time
import cupsmq
from pyftpdlib import ftpserver
import cups
import os
import ConfigParser
import sys

### define constants

### define classes

# rewrite FTPHandler class with custom on_file_recieved hook
class FTPHandlerCUPS(ftpserver.FTPHandler):

    # custom hook after file was recieved
    # send file to cups queue with the name of the directory
    def on_file_received(self, file):
        print "got file", file
        con = cups.Connection()
        queue = file.split("/")[-2]
        title = file.split("/")[-1]
        options = {}
        try:
            job = con.printFile(queue, file, title, options)
            print "submitted job", job
            os.remove(file)
        except:
            print "couldnt submit job"


### define functions
# short function description

### main program
# read configuration
if len(sys.argv) != 2:
    print sys.argv
    print "usage: cupsmq-ftpd.py <path to cupsmq config file>"
    exit(1)
else:
    config = ConfigParser.ConfigParser()
    try:
        config.read(sys.argv[1])
        # get config data from config object
        spooldir = config.get('cupsmq-ftpd', 'spooldir')
        if not os.path.exists(spooldir):
            try:
                os.makedirs(spooldir)
            except:
                print "can not create spool directory"
                sys.exit(2)
        listen = config.get('cupsmq-ftpd', 'listen')
        port = config.get('cupsmq-ftpd', 'port')
        address = (listen, port)
    except:
        print "can not read configuration file", sys.argv[1]
        exit(1)


# initialize and start queuefs monitor
monitor = cupsmq.CUPSQueueFS(serverroot=spooldir)
monitor.setDaemon(True)
monitor.start()
print "started"

## set up FTP server
# authorization
auth = ftpserver.DummyAuthorizer()
# for now accept a dummy user
auth.add_user("dummy", "gummy", spooldir, perm="elradwm")

handler = FTPHandlerCUPS
handler.authorizer = auth
handler.banner = "cups-mq queue ftpd ready"

ftpd = ftpserver.FTPServer(address, handler)
ftpd.serve_forever()
