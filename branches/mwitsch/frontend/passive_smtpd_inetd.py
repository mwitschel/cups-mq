#!/usr/bin/python
#################################################################
#
# active_smtpd_inetd.py - description
#
#
# Copyright (C) 2012
# Permission is hereby granted to use and distribute this code,
# with or without modifications, provided that this copyright
# notice is copied with it. Like anything else that's free,
# active_smtpd_inetd.py is provided *as is* and comes with no
# warranty of any kind, either expressed or implied. In no
# event will the copyright holder be liable for any damages
# resulting from the use of this software.
#
# Author: Matthias Witschel
# Email: mwitsch@gmail.com
# Date: So 29. Jan 13:02:33 CET 2012
#
# Repository Name: https://cups-mq.googlecode.com/svn/branches/mwitsch/frontend
# Revision: 99
#
################################################################


### import modules
import smtpd
import sys
import syslog


### define constants



### define classes

# custmized smtpd server class
class CupsmqSMTPServer(smtpd.SMTPServer):

    # custumized message handler
    def process_message(self, peer, mailfrom, rcpttos, data):
        print 'mail from', mailfrom



### define functions

# the main function
def main():

    line = sys.stdin.readline()
    syslog.syslog(line)
    sys.exit(99)
    server = CupsmqSMTPServer(('127.0.0.1', 1025), None)



### main program

if __name__ == '__main__':
    main()







