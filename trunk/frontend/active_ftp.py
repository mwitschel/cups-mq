#!/usr/bin/python
########################################################
#
# active_ftp.py
#
#
# Copyright (C) 2012 Philipp Wiesner
# Permission is hereby granted to use and distribute this code,
# with or without modifications, provided that this copyright
# notice is copied with it. Like anything else that's free,
# active_ftp.py is provided *as is* and comes with no
# warranty of any kind, either expressed or implied. In no
# event will the copyright holder be liable for any damamges
# resulting from the use of this software.
#
#
# Author: Matthias witschel
# Email: mwitsch@gmail.com
# Date: Wed Jan  4 21:05:18 CET 2012
#
# Repository Name: https://cups-mq.googlecode.com/svn/trunk/frontend
# Revision: 30
#
# Description:
# Active FTP frontend for cups. Retrieves every found file on
# a ftp server path and submit it one by one to cups as one
# job each.
#
########################################################


### import modules
import os
import sys
from ftplib import FTP
import cupsmq
import syslog
import socket

### define constants
# for testing we always remove remote files, this will be another argument later
delremote = True

# real variables
filelist = []

# constants

### define classes

# short class description



### define functions
# add a filename to filelist, meant as callback function for FTP.retrlines
def file2list(filename):
    # add filename to list, when pattern matches
    # it would be nice to have this work with regexp
    # for now just add filename to list whatever...
    filelist.append(filename)

def main():
    # first, check if called correctly
    if len(sys.argv) != 3:
        print "usage: active_ftp.py URI targetqueue"
        sys.exit(1)

    uri = sys.argv[1]
    destq = sys.argv[2]


    # open syslog with appropriate information about process
    # and log starting information
    syslog.openlog(logoption=syslog.LOG_PID)
    syslog.syslog("cupsmq active ftp frontend started")

    spoolpath = "/var/spool/cupsmq/in/" + str(os.getpid())
    try:
        os.makedirs(spoolpath)
    except:
        syslog.syslog("could not create spoolpath " + spoolpath)
        sys.exit(4)

    # instantiate URIParser
    try:
        URI = cupsmq.URIParser(uri)
    except:
        syslog.syslog("could not parse URI " + uri)
        sys.exit(3)

    try:
        ftp = FTP(URI.host, URI.user, URI.passw)
    except:
        syslog.syslog("could not connect to " + URI.host)
        sys.exit(2)

    syslog.syslog("connected to " + URI.host)

    try:
        ftp.cwd(URI.targetpath)
    except:
        syslog.syslog("could not cwd to " + URI.targetpath)
        sys.exit(2)

    syslog.syslog("successfully CWD to " + URI.targetpath)

    try:
        logline = ftp.retrlines('NLST',file2list)
    except:
        syslog.syslog("could not get filelist")
        exit(2)
        
    # to avoid endless hanging frontend processes
    # set socket timeout to 30 seconds
    socket.setdefaulttimeout(30)

    syslog.syslog("got answer from " + URI.host + ": " + logline)
    syslog.syslog("recieved " + str(len(filelist)) + " filename(s)")

    # instantiate frontend
    frontend = cupsmq.CUPSFrontend()

    for filename in filelist:
        syslog.syslog("retrieving " + filename)
        lclfilename = spoolpath + '/' + filename
        cmdline = 'RETR ' + filename

        try:
            ftp.retrbinary(cmdline, open(lclfilename, 'wb').write)
        except:
            syslog.syslog("could not retrieve " + filename + " or write local file " + lclfilename)
            sys.exit(3)

        # submit file to cups via CUPSFrontend and recieve return code
        rc = frontend.submitjob(destq, lclfilename)

        # remove local spoolfile in any case
        syslog.syslog("removing local temp file " + lclfilename)
        os.remove(lclfilename)

        # remove remote file only if submitted successfully and permitted
        if rc == 0:
           if delremote:
                syslog.syslog("removing remote file " + filename)
                try:
                    ftp.delete(filename)
                except:
                    syslog.syslog("can not remove remote file " + filename)

    os.removedirs(spoolpath)

    ftp.quit()


### main program

if __name__ == '__main__':
    main()







