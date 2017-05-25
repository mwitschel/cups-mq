#!/usr/bin/python
#################################################################
#
# directory.py - description
#
#
# Copyright (C) 2012
# Permission is hereby granted to use and distribute this code,
# with or without modifications, provided that this copyright
# notice is copied with it. Like anything else that's free,
# directory.py is provided *as is* and comes with no
# warranty of any kind, either expressed or implied. In no
# event will the copyright holder be liable for any damages
# resulting from the use of this software.
#
# Author: Matthias Witschel
# Email: mwitsch@gmail.com
# Date: Thu Jan  5 16:46:22 CET 2012
#
# Repository Name: https://cups-mq.googlecode.com/svn/trunk/backend
# Revision: 34
#
################################################################


### ATTENTION ###
# this backend needs to be run as root, to enable directory creation and
# changing of uid/gid of output files!
# to make cups run this backend as root, change permissions to 700 !

### import modules
import cupsmq
import sys
import os
import pwd


### define constants



### define classes

# short class description



### define functions

# main function
def main():
    # define descr_string. this will be printed when backend is called without any
    # parameters, which means it should give information about itself
    descr_str = "direct %s \"Unknown\" \"write files to directory\"\n"

    # instantiate backend object with given arguments and description string
    backend = cupsmq.CUPSBackend(sys.argv, descr_str)
    # create output path from backend targetpath and title
    outfilepath = "/" + backend.targetpath + "/" + backend.title

    try:
        userdat = pwd.getpwnam(backend.user)
    except:
        backend.jobmsg(cupsmq.DEBUG, "no file owner given, files will be created with cups standard user")

    # create target path if not exists
    if not os.path.exists(backend.targetpath):
        backend.jobmsg(cupsmq.DEBUG, "Creating targetpath /" + backend.targetpath)
        try:
            os.makedirs("/" + backend.targetpath)
        except:
            backend.jobmsg(cupsmq.ERROR, "can not create target path")
            sys.exit(cupsmq.CUPS_BACKEND_FAILED)

        # and change owner if defined
        if backend.user != '':
            backend.jobmsg(cupsmq.DEBUG, "Changing targetpath owner to " + userdat.pw_uid)
            try:
                os.chown(backend.targetpath, userdat.pw_uid, userdat.pw_gid)
            except:
                backend.jobmsg(cupsmq.ERROR, "can not change owner of /" + backend.targetpath + " to " + backend.user)
                sys.exit(cupsmq.CUPS_BACKEND_FAILED)

    # check if something already exists on that path and if so, exit with CUPS_BACKEND_HOLD
    # to hold this job and continue with the next in the queue
    if os.path.exists(outfilepath):
        backend.jobmsg(cupsmq.ERROR, "Output file already exists: " + outfilepath)
        sys.exit(cupsmq.CUPS_BACKEND_HOLD)

    else:
    # go on, write the output file to desired location
    # and if a user is given, chown written file to that userpython os.chown
        try:
            outfile = open(outfilepath, "w")
            outfile.writelines(backend.jobdata)
            outfile.close()
            backend.jobmsg(cupsmq.NOTICE, "file written successfully: " + outfilepath)
        except:
            backend.jobmsg(cupsmq.ERROR, "can not open for writing: " + outfilepath)
            sys.exit(cupsmq.CUPS_BACKEND_HOLD)

        if backend.user != '':
            try:
                os.chown(outfilepath, userdat.pw_uid, userdat.pw_gid)
                backend.jobmsg(cupsmq.INFO, "changed fileowner to: " + backend.user)
            except:
                backend.jobmsg(cupsmq.ERROR, "can not change fileowner to: " + backend.user)


    backend.pagelog()
    del backend
    sys.exit(cupsmq.CUPS_BACKEND_OK)

### main program

if __name__ == '__main__':
    main()

