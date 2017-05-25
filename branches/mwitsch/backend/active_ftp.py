#!/usr/bin/python
########################################################
#
# active_ftp.py
#
#
# Copyright (C) 2011 Philipp Wiesner
# Permission is hereby granted to use and distribute this code,
# with or without modifications, provided that this copyright
# notice is copied with it. Like anything else that's free,
# active_ftp.py is provided *as is* and comes with no
# warranty of any kind, either expressed or implied. In no
# event will the copyright holder be liable for any damamges
# resulting from the use of this software.
#
#
# Author: Philipp Wiesner
# Email: philipwiesner@gmail.com
# Date: Mon Dec 19 16:23:05 CET 2011
#
# Repository Name: https://cups-mq.googlecode.com/svn/trunk/backend
# Revision: 10
#
# Description:
# Automatically transmit print file to given ftp server by DEVICE URI
#
########################################################


### import modules
from ftplib import FTP
import os
import sys
import cupsmq as cupsbackend


### define variables
filelist = []

### define constants


### define functions

def file2list(filename):
    # add filename to list, when pattern matches
    # it would be nice to have this work with regexp
    # for now just add filename to list whatever...
    filelist.append(filename)


# main function
def main():
    # define descr_string. this will be printed when backend is called without any
    # parameters, which means it should give information about itself
    descr_str = "direct %s \"Unknown\" \"upload files via FTP to given Server by DEVICE URI\"\n"

    # instantiate backend object with given arguments and description string
    backend = cupsbackend.CUPSBackend(sys.argv, descr_str)

    # set spoolpath to ftp-<> in cupsMQ output spool
    spoolpath = "/var/spool/cupsmq/out/ftp-" + str(backend.host)

    # if our spool directory does not already exist, we need to create it
    # if it can not be created, exit with CUPS_BACKEND_FAILED
    if not os.path.isdir(spoolpath):
        try:
            os.makedirs(spoolpath)
        except:
            backend.jobmsg(cupsbackend.ERROR, "Can not create spool path: " + spoolpath)
            sys.exit(cupsbackend.CUPS_BACKEND_FAILED)

    # copy jobdata to file in spool directory
    try:
        spoolfile = open(spoolpath + "/" + backend.title, "w")
        spoolfile.writelines(backend.jobdata)
        spoolfile.close()
    except:
        backend.jobmsg(cupsbackend.ERROR, "can not write local spoolfile")
        sys.exit(cupsbackend.CUPS_BACKEND_STOP)

    # connect to ftp server
    try:
        ftp = FTP(backend.host, backend.user, backend.passw)
        backend.jobmsg(cupsbackend.INFO, "connected to remote host: " + backend.host)
    except:
        backend.jobmsg(cupsbackend.ERROR, "can not connect to remote host " + backend.host)
        sys.exit(cupsbackend.CUPS_BACKEND_STOP)


    # change remote work dir if required
    spoolfile = open(spoolpath + "/" + backend.title, "r")
    if backend.targetpath != '':
        try:
            ftp.cwd(backend.targetpath)
            backend.jobmsg(cupsbackend.INFO, "changed cwd to " + backend.targetpath)
        except:
            backend.jobmsg(cupsbackend.ERROR, "can not change cwd to " + backend.targetpath)
            sys.exit(cupsbackend.CUPS_BACKEND_FAILED)


    # check for existing files
    logline = ftp.retrlines('NLST',file2list)
    if backend.title in filelist:
        backend.jobmsg(cupsbackend.ERROR, "can not subit " + backend.title + ", seems to exist on remote path")
        sys.exit(cupsbackend.CUPS_BACKEND_HOLD)

    # upload spoolfile
    try:
        ftp.storbinary("STOR " + backend.title, spoolfile)
        backend.jobmsg(cupsbackend.INFO, "submitted file successfully: " + backend.title)
    except:
        backend.jobmsg(cupsbackend.ERROR, "could not submit jobfile " + backend.title)
        sys.exit(cupsbackend.CUPS_BACKEND_FAILED)

    spoolfile.close()

    # close all open connections
    spoolfile.close()
    os.remove(spoolpath + "/" + backend.title)
    ftp.quit()
    backend.pagelog()
    del backend

    # exit gracefully telling cupsd all is perfect
    sys.exit(cupsbackend.CUPS_BACKEND_OK)


### main program
if __name__ == '__main__':
    main()









