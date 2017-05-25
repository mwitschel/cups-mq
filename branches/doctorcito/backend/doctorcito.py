#!/usr/bin/python
#################################################################
#
# doctorcito.py - description
#
#
# Copyright (C) 2012
# Permission is hereby granted to use and distribute this code,
# with or without modifications, provided that this copyright
# notice is copied with it. Like anything else that's free,
# doctorcito.py is provided *as is* and comes with no
# warranty of any kind, either expressed or implied. In no
# event will the copyright holder be liable for any damages
# resulting from the use of this software.
#
# Author: Matthias Witschel
# Email: mwitsch@gmail.com
# Date: Fr 20. Jan 21:39:46 CET 2012
#
# Repository Name: https://cups-mq.googlecode.com/svn/branches/doctorcito/backend
# Revision: 69
#
################################################################

#### documentation excerpt ####
# config file /etc/cupsmq/cupsmq.conf:
# [doctorcito]
# printer = <printer for hardcopies>
# filestore = <directory containing pdf files for webinterface>
# fileowner = <owner of the filestore and files in filestore>
#
# currently only one hardcopy printer is supported
# filestore directory will be created if not exists
# fileowner should be set to the user used to display the sheets, e.g. 'apache'
#  if you want to display the sheets via webinterface
#
# copy this backend to /usr/libexec/cups/backend/doctorcito and change
# permissions to 0700 (needs to run as root).
#
# copy lib/cupsmq.py and lib/indexer.py to /usr/lib64/python2.7/site-packages/
# maybe you need to change the path to match your current python version and architecture
#
# restart cups after the copying
#
# you should now see a new backend in cups available
#
# Printer URI to use doctorcito:
# doctorcito:///
#
# currently the URI does not contain any information for the backend so it jus specifies the
# backend to use.
#
# To test the backend, set device URI in environment and call the backend like cups would do.
# Do this as root!
#
# export DEVICE_URI="doctorcito:///"
#
# possibility 1:
# /usr/libexec/cups/backend/doctorcito 1 2 3 4 5 filename
#
# possibility 2:
# /usr/libexec/cups/backend/doctorcito 1 2 3 4 5 < filename


### import modules
import cupsmq
from indexer import Indexer
import sys
import os
import MySQLdb
import ConfigParser
import pwd


### define constants



### define classes

# short class description
class DbConnector:
    __host = "localhost"
    __instance = "doctorcito"
    __user = "doctorcito"
    __passw = "test"

    def __init__(self):
        # initialize database connection
        pass

    # add document to database
    def addDocument(self, results):
        pass

### define functions

# Main function
def main():
    strbuff = ""

    # define cups description string for backend identification
    descr_str = "direct %s \"Unknown\" \"write medical lab sheets to a filestore and add indexing data to a mysql database\"\n"

    # create a cups backend object instance
    backend = cupsmq.CUPSBackend(sys.argv, descr_str)

    # temp file path
    # to stay within cups specifications this needs to be moved to CUPS TMPDIR
    tmpfilename = "/tmp/docotorcito-" + backend.job

    # instantiate Indexer object
    indexer = Indexer()

    # instantiate database connector
    dbcon = DbConnector()

    # instantiate config parser
    # and read doctorcito config, exit on error
    config = ConfigParser.ConfigParser()
    try:
        config.read('/etc/cupsmq/cupsmq.conf')
        destprinter = config.get('doctorcito', 'printer')
        filestore = config.get('doctorcito', 'filestore')
        fileowner = config.get('doctorcito', 'fileowner')
    except:
        backend.jobmsg(cupsmq.ERROR, "can not read /etc/cupsmq/cupsmq.conf")
        sys.exit(cupsmq.CUPS_BACKEND_FAILED)

    # get userinfo of fileowner from OS
    # exit with CUPS_BACKEND_FAILED to hold queue if this can not be done
    try:
        userdat = pwd.getpwnam(fileowner)
    except:
        backend.jobmsg(cupsmq.ERROR, "Can not determine file owner, check your config!")
        sys.exit(cupsmq.CUPS_BACKEND_FAILED)


    # write job document to temp file.
    tmpfile = open(tmpfilename ,"w")
    tmpfile.writelines(backend.jobdata)
    tmpfile.close()

    # run pdftotext to get text content from pdf file
    #
    p = os.popen("/usr/bin/pdftotext -raw " + tmpfilename + " -")
    linebuff = p.readlines()
    p.close()

    # adding the indexing patterns to indexer instance
    # this should be configurable via config file, but currently i cant think of a way,
    # have to review config parser documentation on tuples in config file
    indexer.addPattern("Patient", mode=indexer.LINES, count=2)
    indexer.addPattern("Druckdatum:", mode=indexer.WORDS, count=2)
    indexer.addPattern("Entnahmedatum:", mode=indexer.WORDS, count=2)
    indexer.addPattern("Station")
    indexer.addPattern("folgt")

    # run indexer on linebuffer
    results = indexer.run(linebuff)

    # check if pattern 'folgt' returned any occurences
    # if not, submit to destinatione queue
    if len(results['folgt']) == 0:

        # instantiate frontend object
        frontend = cupsmq.CUPSFrontend()
        # submit tempfile via frontend object
        frontend.submitjob(destprinter, tmpfilename)

        # give cups a notice, that we printed the sheet
        backend.jobmsg(cupsmq.NOTICE, "submitted sheet to " + destprinter)

        # delete frontend, we dont need it any more
        del frontend

    # remove 'folgt' from indexer results in any case
    # we dont want it in the database
    results.pop('folgt')

# todo:
# - write index data to database

    # construct output file name
    patnumber = results['Patient'][0]
    printdate = results['Druckdatum:'][0].replace('.','-').replace(' ','_').replace(':','-')
    filename = filestore + '/' 'labor_' + patnumber + "_" + printdate + '.pdf'

    # if filestore path does not exist, create it
    if not os.path.exists(filestore):
        backend.jobmsg(cupsmq.DEBUG, 'Creating filestore path ' + filestore)
        os.makedirs(filestore)
        os.chown(filestore, userdat.pw_uid, userdat.pw_gid)

    # backends are not allowed to overwrite existing data, so exit with error, when file exists
    # and hold this job
    if os.path.exists(filename):
        backend.jobmsg(cupsmq.ERROR, "Output file already exists: " + filename)
        sys.exit(cupsmq.CUPS_BACKEND_HOLD)

    # write file to filestore
    try:
        outfile = open(filename, "w")
        outfile.writelines(backend.jobdata)
        outfile.close()
        backend.jobmsg(cupsmq.NOTICE, "file written successfully: " + filename)
    except:
        backend.jobmsg(cupsmq.ERROR, "can not open for writing: " + filename)
        sys.exit(cupsmq.CUPS_BACKEND_HOLD)

    # change owner of the file to fileowner set in config
    try:
        os.chown(filename, userdat.pw_uid, userdat.pw_gid)
        backend.jobmsg(cupsmq.INFO, "changed fileowner to: " + backend.user)
    except:
        backend.jobmsg(cupsmq.ERROR, "can not change fileowner to: " + backend.user)


    # send debug msg to cups containing indexing data
    backend.jobmsg(cupsmq.DEBUG, 'indexing data: ' + str(results))

    # add document to database
    dbcon.addDocument(results)

    # remove temporary file
    os.remove(tmpfilename)

    # cleanup, just to be sure
    del backend
    del dbcon
    del config

### main program
if __name__ == "__main__":
    main()

