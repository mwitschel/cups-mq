#!/usr/bin/python
########################################################
#
# _cupsbackend.py
#
#
# Copyright (C) 2011 Name
# Permission is hereby granted to use and distribute this code,
# with or without modifications, provided that this copyright
# notice is copied with it. Like anything else that's free,
# _cupsbackend.py is provided *as is* and comes with no
# warranty of any kind, either expressed or implied. In no
# event will the copyright holder be liable for any damamges
# resulting from the use of this software.
#
#
# Author:
# Email:
# Date: Mon Dec 19 14:29:12 CET 2011
#
# Repository Name: https://cups-mq.googlecode.com/svn/trunk/lib
# Revision: 10
#
# Description:
# cups backend lib
#
########################################################


### import modules
import sys
import os
import threading
import time
import string
import syslog
from subprocess import call
try:
    import cups
    pycups = True
except:
    pycups = False



### define constants


## cups backend returncodes
# according to cups backend manpage (http://www.cups.org/documentation.php/man-backend.html)

# The print file was successfully transmitted to the device or remote server:
CUPS_BACKEND_OK = 0

# The print file was not successfully transmitted to the device or remote server.
# The scheduler will respond to this by canceling the job, retrying the job,
# or stopping the queue depending on the state of the error-policy attribute:
CUPS_BACKEND_FAILED = 1

# The print file was not successfully transmitted because valid authentication information is required.
# The scheduler will respond to this by holding the job and adding the authentication-required job-reasons keyword
CUPS_BACKEND_AUTH_REQUIRED = 2

# The print file was not successfully transmitted because it cannot be printed at this time.
# The scheduler will respond to this by holding the job:
CUPS_BACKEND_HOLD = 3

# The print file was not successfully transmitted because it cannot be printed at this time.
# The scheduler will respond to this by stopping the queue
CUPS_BACKEND_STOP = 4

# The print file was not successfully transmitted because one or more attributes are not supported.
# The scheduler will respond to this by canceling the job:
CUPS_BACKEND_CANCEL = 5


## cups filter message prefixes
# more info: http://www.cups.org/documentation.php/api-filter.html#MESSAGES

# Sets the printer-state-message attribute and adds the specified message to the
# current error log file using the "alert" log level
ALERT = "ALERT:"

# Sets the named printer or job attribute(s). Typically this is used to set the
# marker-colors, marker-levels, marker-message, marker-names, marker-types,
# printer-alert, and printer-alert-description printer attributes.
# Standard marker-types values are listed in Table 1.
ATTR = "ATTR:"

# Sets the printer-state-message attribute and adds the specified message to the
# current error log file using the "critical" log level.
CRIT = "CRIT:"

# Sets the printer-state-message attribute and adds the specified message to the
# current error log file using the "debug" log level.
DEBUG = "DEBUG:"

# Sets the printer-state-message attribute and adds the specified message to the
# current error log file using the "debug2" log level.
DEBUG2 = "DEBUG2:"

# Sets the printer-state-message attribute and adds the specified message to the
# current error log file using the "emergency" log level.
EMERG = "EMERG:"

# Sets the printer-state-message attribute and adds the specified message to the
# current error log file using the "error" log level. Use "ERROR:" messages for non-
# persistent processing errors.
ERROR = "ERROR:"

# Sets the printer-state-message attribute. If the current log level is set to
# "debug2", also adds the specified message to the current error log file using the
# "info" log level.
INFO = "INFO:"

# Sets the printer-state-message attribute. If the current log level is set to
# "debug2", also adds the specified message to the current error log file using the
# "info" log level.
NOTICE = "NOTICE:"

# PAGE: is omitted here. For page logging use CUPSBackend.pagelog()

# PPD: is omitted here. Currently there is no use for PPD in message queueing

# Sets, adds, or removes printer-state-reason keywords to the current queue. Typically
# this is used to indicate persistent media, ink, toner, and configuration conditions
# or errors on a printer. Table 2 lists the standard state keywords - use vendor-
# prefixed ("com.acme.foo") keywords for custom states.
#
# Use of this for cupsmq is discussable. Lets see what we can get out of it.
STATE = "STATE:"



### define functions

# Parse URI and return dictinary with its parts
# this is only a stub and most likely obsolete.
# Should be removed soon.
def parseURI(URI):
    pass


### define classes

# Exception ShutDown
# Custom exception to signal shutdown
class ShutDown(Exception):
    """shut down everythin"""

# URIParser
# Parses a given URI upon instantiation, and thus takes a qualified URI
# as only argument.
#
# Attributes:
# URI           = the URI to parse
# proto         = protocoll part
# user          = user in URI
# passw         = password in URI
# host          = host in URI
# port          = the port in URI
# targetpath    = the path part in URI
class URIParser:

    def __init__(self, URI):
        self.URI = URI
        buff = self.URI.split("://")
        self.proto = buff[0]
        buff = buff[1]
        if buff.count("@") > 0:
            authbuff = buff.split("@")[0]
            self.user = authbuff.split(":")[0]
            try:
                self.passw = authbuff.split(":")[1]
            except:
                self.passw = ''
            buff = buff.split("@")[1]
        if buff.count(":") > 0:
            self.host = buff.split(":")[0]
            self.port = buff.split(":")[1].split("/")[0]
            buff = buff.split("/")[1:]
        else:
            self.host = buff.split("/")[0]
        self.targetpath = string.join(buff.split("/")[1:], '/')




# CUPSBackend
# Handles correct calling and output to cupsd if called without arguments
# Provides all information and data assotiated with a backend job.
#
# Attributes:
# user          user configured in CUPS URI
# passw         password configured in CUPS URI
# proto         protocol, aka backend name
# host          target host configured in URI
# port          port configured in URI
# __filename    filename of jobfile if provided in arguments, if not its an empty string
# title         cups jobtitle, this is usually the filename of the submitted file
# job           cups job number
# jobuser       user that submitted the job
# num_copies    number of copies
# jobdata       content of the jobfile itself
# targetpath    path specification after host in URI
#
# Methods:
# __init__      object constructor, sets all attributes

class CUPSBackend:

    # defaults for optional data
    user = ''
    passw = ''
    port = ''
    targetpath = ''
    __filename = ''

    def __init__(self,args=[],descr_str=""):

        # when called without arguments we give backend info.
        # This is also used when lpinfo -v is issued, where it should include "direct this_backend"
        if len(args) == 1:
            sys.stdout.write(descr_str % os.path.basename(args[0]))
            sys.stdout.flush()
            sys.exit(0)

        # backends take exactly 5 or 6 arguments. So if we get less tell the caller what we want
        if len(args) not in (6,7):
            sys.stdout.write("Usage: %s job-id user title copies options [file]\n" % os.path.basename(args[0]))
            sys.stdout.flush()
            sys.exit(1)
        else:
            # seems backend got called correctly let's get sesrious
            # reroute all output to stderr, so everything gets visible at least in cups
            # debug mode error_log
            sys.stdout = sys.stderr

            # copy parameters to object attribures
            self.job = args[1]
            self.jobuser = args[2]
            self.title = args[3]
            self.title = self.title.replace(' ','_')
            self.num_copies = args[4]
            self.joboptions = args[5]
            if len(args) == 7:
                self.__filename = args[6]

        # get DEVICE_URI from environment and determine protocol (aka backend name)
        self.URI = os.environ['DEVICE_URI']

        # parse URI and split it into its parts
        # this is for now redundant to URIParser object.
        # I need to clean this up when i have more time!!!
        buff = self.URI.split("://")
        self.proto = buff[0]
        buff = buff[1]
        if buff.count("@") > 0:
            authbuff = buff.split("@")[0]
            self.user = authbuff.split(":")[0]
            try:
                self.passw = authbuff.split(":")[1]
            except:
                self.passw = ''
            buff = buff.split("@")[1]
        if buff.count(":") > 0:
            self.host = buff.split(":")[0]
            self.port = buff.split(":")[1].split("/")[0]
            buff = buff.split("/")[1:]
        else:
            self.host = buff.split("/")[0]
        self.targetpath = string.join(buff.split("/")[1:], '/')


        # Provide jobdata in an object atribute.
        # when we got a filename, read jobdata from jobfile. otherwise read jobdata from stdin
        if self.__filename != '':
            infile = open(self.__filename)
            self.jobdata = infile.readlines()
            infile.close()
        else:
            self.jobdata = sys.stdin.readlines()


    def jobmsg(self, prefix=INFO, msg=""):
        sys.stderr.write("%s %s\n" % (prefix, msg))
        sys.stderr.flush()


    def pagelog(self, pagenum=1):
        sys.stderr.write("PAGE: total %s-pages\n" % pagenum)
        sys.stderr.flush()



# CUPS Frontend
# Create a connection to cupsd if pycups is available and handle submitting
# of jobs.
#
# Attributes
# con   = connection to local cups server
class CUPSFrontend:

    # cups host, this is somehow redundant now, because we only intend to
    # open connections to local spooler service
    cupshost = ''

    # path to lp, later to be configurable
    LP_BIN = "/usr/bin/lp"

    # Constructor. Tages cupshost as optinal parameter
    # cupshost ist howver currently not used.
    def __init__(self, cupshost='localhost'):
        self.__cupshost = cupshost

        if pycups:
            self.con = cups.Connection()

    # submitjob Method.
    # Submits a job to cups spooler.
    #
    # Arguments:
    # destq     = destination Queue
    # filename  = complete and absolute path to the file that is to be submitted
    # title     = Job title, if jobtitle is not set, the filename, e.g. the last part of
    #             the path in 'filename' will be used as job title
    # options   = The jobs options to be passed along the file, see pycups doc for details
    def submitjob(self, destq, filename, title='', options={}):
        if title == '':
            title = filename.split('/')[-1]

        # Check if native mode, i.a. pycups is available
        # if so, submit job via pycups interface
        if pycups:
            try:
                job = self.con.printFile(destq, filename, title, options)
                rc = 0
            except:
                # this sould be replaced by logging facility
                syslog.syslog(syslog.LOG_ERR, "can not submit " + title + " in native mode to " + destq)
                rc = 1

        # compatibility mode submission
        # if pycups is not available for any reason, subit job via lp command
        else:
            subproc_args = [LP_BIN, "-d" + destq, filename]
            rc = call(subproc_args)
            if rc != 0:
                # this should be replaced by logging facility
                syslog.syslog(syslog.LOG_ERR, "can not submit " + title + " in compat mode to " + destq)

        if rc == 0:
            # syslog submitted in native mode
            syslog.syslog("submitted " + filename + " to " + destq)

        # return rc for further error handling in frontend code
        return rc


# CUPSQueueFS
# regularly pulls a list of cups queues and creates / deletes directories
# in serverroot to create a representation of existing queues.
# Inherits threading.Thread and is therefor a thread object.
#
# Attributes:
# __cupscon     connection to cups server
# __serverroot  root path to queue directories
#
# Methods:
# __init__      object constructor
#
# Parameters to pass for init:
# serverroot    will be __serverroot, optional with default
# host          host to connect to (cups), optional with default

class CUPSQueueFS(threading.Thread):

    def __init__(self,serverroot='/var/spool/cupsmq/in/ftpd', host='localhost'):
        cups.setServer(host)
        self.__cupscon = cups.Connection()
        self.__serverroot = serverroot
        threading.Thread.__init__(self)

    def run(self):
        print "Starting Cups Queue FS Monitor"
        while True:
            try:
                printers = self.__cupscon.getPrinters()
                plist = set(printers.keys())
                dlist = set(os.listdir(self.__serverroot))
                for directory in plist.difference(dlist):
                    try:
                        os.makedirs(self.__serverroot + "/" + directory)
                    except:
                        print "could not create path", self.__serverroot + "/" + directory
                        raise cupsmq.ShutDown
                for directory in dlist.difference(plist):
                    try:
                        os.rmdir(self.__serverroot + "/" + directory)
                    except:
                        print "could not remove path", directory
                time.sleep(3)
            except cupsmq.ShutDown:
                break
        print "exiting queue monitor"


