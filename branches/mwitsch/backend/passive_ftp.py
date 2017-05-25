#!/usr/bin/python
########################################################
#
# _ftpd.py
#
#
# Copyright (C) 2011 Name
# Permission is hereby granted to use and distribute this code,
# with or without modifications, provided that this copyright
# notice is copied with it. Like anything else that's free,
# _ftpd.py is provided *as is* and comes with no
# warranty of any kind, either expressed or implied. In no
# event will the copyright holder be liable for any damamges
# resulting from the use of this software.
#
#
# Author: Matthias Witschel
# Email: mwitsch@gmail.com
# Date: Mon Dec 19 13:47:17 CET 2011
#
# Repository Name: https://cups-mq.googlecode.com/svn/trunk/backend
# Revision: 10
#
# CupsMQ FTPD backend
# FTPD functionality implemented via pyftpdlib.
#
# URI format:
# ftpd://<user>:<pw>@<listen>:<portnumber>
#
# user = username to authenticate client
# pw = password for cleint authentication
# listen = IP address to listen on
# portnumber = portnumber to listen on
#
# Server will start and listen on port specified in URI.
# Server will provide access to one file only (the actual jobfile).
# Connection will be authenticated by user and pw specified in URI.
# Backend will automatically close all connections and terminate after file has been sent.
#
#######################################################


### import modules
from pyftpdlib import ftpserver
import asyncore
import sys
import os
import cupsmq as cupsbackend
import shutil



### define constants



### define classes

# Rewrite FTPHandler class with custom on_file_sent hook
class FTPHandlerOnce(ftpserver.FTPHandler):

	# custom hook after file is sent
	# shut down server process
	def on_file_sent(self, file):
		raise asyncore.ExitNow


### define functions

# main funtion
def main():
	# define descr_string. this will be printed when backend is called without any
	# parameters, which means it should give information about itself
	descr_str = "direct %s \"Unknown\" \"passively provide files via FTPD\"\n"

	# instantiate backend object with given arguments and description string
	backend = cupsbackend.CUPSBackend(sys.argv, descr_str)

	# set spoolpath to ftpd-<portnumber> in cupsMQ output spool
	spoolpath = "/var/spool/cupsmq/out/ftpd-" + str(backend.port)

	# if our spool directory does not already exist, we need to create it
	# if it can not be created, exit with CUPS_BACKEND_FAILED
	if not os.path.isdir(spoolpath):
		try:
			os.makedirs(spoolpath)
            backend.jobmsg(cupsmq.INFO, "created local spoolpath: " + spoolpath)
		except:
            backend.jobmsg(cupsmq.ERROR, "can not create local spoolpath: " + spoolpath)
			sys.exit(cupsbackend.CUPS_BACKEND_FAILED)

	# create address tuple for pyftpdlib FTPServer object
	address = (backend.host, int(backend.port))

	# copy jobdata to file in spool directory
    try:
        spoolfile = open(spoolpath + "/" + backend.title, "w")
        spoolfile.writelines(backend.jobdata)
        spoolfile.close()
        backend.jobmsg(cupsmq.INFO, "wrote jobdata to local spoolfile")
    except:
        backend.jobmsg(cupsmq.ERROR, "can not write jobdata to local spoolfile: " + spoolpath + "/" + backend.title)
        sys.exit(cupsmq.CUPS_BACKEND_FAILED)

	# set authorization to user and password configured in cups queue
	# permission string is always "lr" - user can only list and recieve files
	auth = ftpserver.DummyAuthorizer()
	auth.add_user(backend.user, backend.passw, spoolpath, perm = "lr")

	# instantiate FTPHandler object with overwritten on_file_sent method
	# give authorizer to handler
	# and set ftp server banner
	handler = FTPHandlerOnce
	handler.authorizer = auth
	handler.banner = "cupsMQ ftpd backend ready"

	# instantiate ftp server object
	# and start server loop
    try:
        ftpd = ftpserver.FTPServer(address, handler)
    except:
        backend.jobmsg(cupsmq.ERROR, "can not start ftp server: " + str(address))
        sys.exit(cupsmq.CUPS_BACKEND_FAILED)

    ftpd.serve_forever()

	# after transfer has occured FTPHandlerOnce shuts down the
	# asyncore loop. So we now delete the temporary file.
	os.remove(spoolpath + "/" + backend.title)
    backend.pagelog()

	# destroy the backend object, just to be shure ;)
	del backend

	# exit gracefully telling cupsd all is perfect
	sys.exit(cupsbackend.CUPS_BACKEND_OK)



### main program
if __name__ == '__main__':
	main()







