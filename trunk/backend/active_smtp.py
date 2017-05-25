#!/usr/bin/python
#################################################################
#
# active_smtp_ssl.py - description
#
#
# Copyright (C) 2012
# Permission is hereby granted to use and distribute this code,
# with or without modifications, provided that this copyright
# notice is copied with it. Like anything else that's free,
# active_smtp_ssl.py is provided *as is* and comes with no
# warranty of any kind, either expressed or implied. In no
# event will the copyright holder be liable for any damages
# resulting from the use of this software.
#
# Author: Matthias Witschel
# Email: mwitsch@gmail.com
# Date: Sat Jan 28 00:09:05 CET 2012
#
# Repository Name: https://cups-mq.googlecode.com/svn/trunk/backend
# Revision: 92
#
# Description:
# Sends out the jobdata as mime encoded attachment in an email
# via ssl encrypted smtp to one or more recipients.
#
# URI format:
# smtp://<smtp_user>:<smtp_password>@<smtp_server>/<recipient_address>/<recipient_address>/...
#
# Attention! In smtp_user and smtp_password you need to replace '@' with '^'.
# The character will be interpreted internally as '@'. Otherwise the URI
# parser will fail to get things right.
#
################################################################


### import modules
import smtplib
import cupsmq
import sys
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders



### define constants



### define classes

# short class description



### define functions

# short function description
def main():
    # define descr_string. this will be printed when backend is called without any
    # parameters, which means it should give information about itself
    descr_str = "direct %s \"Unknown\" \"send files via smtp using ssl\"\n"

    # instantiate backend object with given arguments and description string
    backend = cupsmq.CUPSBackend(sys.argv, descr_str)

    # put jobdata in a string
    jobdata = ""
    for line in backend.jobdata:
        jobdata = jobdata + line

    # constructing 'from' address
    fromaddress = backend.user

    # creating the message
    msg = MIMEMultipart()
    msg['From'] = backend.jobuser
    msg['Date'] = formatdate(localtime = True)
    msg['Subject'] = backend.title
    msg.attach(MIMEText('This is an automated message, pls do not reply directly!'))

    # create attachment from jobdata
    part = MIMEBase('application','octet-stream')
    part.set_payload(jobdata)
    Encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="%s"' % backend.title)
    msg.attach(part)

    # create recipient address list from URI
    tolist = backend.targetpath.split("/")

    # lets open a ssl connection to SMTP server:
    backend.jobmsg(cupsmq.DEBUG, 'connecting to ' + backend.host)
    try:
        server = smtplib.SMTP(backend.host)
    except:
        backend.jobmsg(cupsmq.ERROR, "can not connect to " + backend.host)
        sys.exit(cupsmq.CUPS_BACKEND_STOP)

    # perform a login if username was given in URI
    if backend.user != '':
        backend.jobmsg(cupsmq.DEBUG, "authenticating...")
        try:
            server.login(backend.user.replace('^','@'), backend.passw.replace('^','@'))
        except:
            backend.jobmsg(cupsmq.ERROR, "login failed")
            sys.exit(cupsmq.CUPS_BACKEND_AUTH_REQUIRED)
    # send mail to every recipient:
    for recipient in tolist:
        backend.jobmsg(cupsmq.DEBUG,'sending to ' + recipient.replace('^', '@'))
        msg['To'] = recipient.replace('^','@')
        try:
            server.sendmail(fromaddress, recipient.replace('^','@'), msg.as_string())
        except:
            backend.jobmsg(cupsmq.ERROR, "send mail to " + recipient + " failed")
            sys.exit(cupsmq.CUPS_BACKEND_HOLD)


    backend.pagelog()

    del backend


### main program

# short description of program block

if __name__ == '__main__':
    main()

