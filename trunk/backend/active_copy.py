#!/usr/bin/python
#################################################################
#
# active_copy.py - description
#
#
# Copyright (C) 2012
# Permission is hereby granted to use and distribute this code,
# with or without modifications, provided that this copyright
# notice is copied with it. Like anything else that's free,
# active_copy.py is provided *as is* and comes with no
# warranty of any kind, either expressed or implied. In no
# event will the copyright holder be liable for any damages
# resulting from the use of this software.
#
# Author: Matthias Witschel
# Email: mwitsch@gmail.com
# Date: Sat Jan  7 13:49:12 CET 2012
#
# Repository Name: https://cups-mq.googlecode.com/svn/trunk/backend
# Revision: 46
#
################################################################


### import modules
import cupsmq
import string
import sys
import syslog

### define constants



### define classes

# short class description



### define functions

# main function
def main():
    # define description string to be put out by backend if called without params
    descr_str = "direct %s \"Unknown\" \"copy files to various other queues\"\n"

    # instantiate backend object
    backend = cupsmq.CUPSBackend(sys.argv, descr_str)

    # instantiate frontend object
    frontend = cupsmq.CUPSFrontend()

    # get targetqueues from device URI
    targetqs = backend.targetpath.split("/")

    # write temp file
    # todo

    # submit temp files to every given queue
    for q in targetqs:
        try:
            frontend.submitjob(q, tempfile, backend.title)
            backend.jobmsg(cupsmq.DEBUG, "submitted " + backend.title + " to " + q)
        except:
            backend.jobmsg(cupsmq.ERROR, "can not submit " + backend.title + " to " + q)

    backend.pagelog()
    del backend
    del frontend

### main program

if __name__ == '__main__':
    main()







