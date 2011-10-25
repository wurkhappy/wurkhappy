# WurkHappy Email Notification Daemon
# Version 0.1
# 
# Written by Brendan Berg
# Copyright WurkHappy, 2011

from tools.email import Email
from tools.orm import Database, ORMJSONEncoder
from tools.beanstalk import Beanstalk
from daemons import notifications

import json
import logging
import sys
import traceback

# -------------------------------------------------------------------
# The daemon process himself
# -------------------------------------------------------------------

class MailController (object):
	_continue = True
	
	def __init__(self, config):
		self.config = config
		self.tubeName = config['notifications']['beanstalk_tube']
		Beanstalk.configure(config['beanstalk'])
		Database.configure(config['database'])
		Email.configure(config['smtp'])
		
		self.handlers = {
			'invite': notifications.InviteHandler,
			'agreementInvite': notifications.AgreementInviteHandler
		}
	
	def start(self):
		logging.info('{"message": "Starting up..."}')
		
		with Beanstalk() as bconn:
			bconn.watch(self.tubeName)
			
			while self._continue:
				msg = bconn.reserve(timeout=15)
				
				if msg:
					logDict = {
						"jobID": msg.jid,
						"body": msg.body
					}
					
					body = None
				
					try:
						body = json.loads(msg.body)
					except ValueError as e:
						logDict['error'] = "Message body was not well-formed JSON"
						logging.error(json.dumps(logDict))
						msg.delete()
						continue
					
					if body:
						handler = self.handlers[body['action']]()
						try:
							handler.receive(body)
							msg.delete()
						except BaseException as e:
							exc = traceback.format_exception(*sys.exc_info())
							logDict['exception'] = exc
							logging.error(json.dumps(logDict))
							msg.bury()
					else:
						logDict['error'] = "Message did not contain a body"
						logging.error(json.dumps(logDict))
						msg.delete()
		logging.info('{"message": "Successfully shut down."}')
	
	def stop(self, signum, frame):
		logging.info('{"message": "Received stop signal. Shutting down."}')
		self._continue = False



# -------------------------------------------------------------------
# PID file parser
# -------------------------------------------------------------------

class Parser (object):
	def __init__(self, filename):
		self.filename = filename

	def read(self):
		processID = None
		
		with open(self.filename, 'r+') as f:
			lines = ''.join([line for line in f])
			try:
				processID = int(lines.strip())
			except ValueError as e:
				return None
		
		return processID

	def write(self, d):
		with open(self.filename, 'w') as f:
			f.write(str(d) + "\n")
			f.flush()



# -------------------------------------------------------------------
# Command line startup
# -------------------------------------------------------------------

if __name__ == "__main__":
	from optparse import OptionParser
	import daemon
	import os, os.path
	import pwd
	import sys
	import yaml
	import signal
	import subprocess
	
	usage = 'usage: %s [-c config] [-p pidfile] [-f logfile] start|stop|refresh' % sys.argv[0]
	
	parser = OptionParser(usage)
	
	parser.add_option("-c", "--config", dest="config",
		help="specify a configuration file",
		metavar="CONF", default="config.yaml")
	parser.add_option("-u", "--user", dest="user",
		help="set the user for the child processes",
		metavar="USER", default=None)
	parser.add_option("-p", "--pidfile", dest="pidfile",
		help="specify a PID file", metavar="FILE",
		default="/var/spool/wh_notificationd.pid")
	parser.add_option("-f", "--logfile", dest="logfile",
		help="redirect STDOUT and STDERR to the specified file",
		metavar="FILE", default="/var/log/notification.log")

	(options, args) = parser.parse_args()
	
	if args[-1] not in ['start', 'stop', 'refresh']:
		parser.error('Final argument should be "start", "stop", or "refresh"')
	
	procParser = Parser(options.pidfile)
	procID = procParser.read()
	
	if args[-1] in ['stop', 'refresh']:
		if procID:
			cmd = ["kill", "-TERM", str(procID)]
			proc = subprocess.Popen(cmd, bufsize=0, executable=None)
		procParser.write('')
	
	if args[-1] == 'stop':
		sys.exit(0)
	elif args[-1] == 'start' and procID:
		parser.error('notificationd is already running')
		sys.exit(0)
	
	# workingDir = os.path.dirname(__file__)
	# if workingDir:
	# 	os.chdir(workingDir)
	
	logfile = open(options.logfile, 'a+')
	conf = yaml.load(open(options.config, 'r'))
	
	ctx = daemon.DaemonContext(stdout=logfile, stderr=logfile, working_directory='.')
	ctx.open()
	
	procID = procParser.write(os.getpid())
	
	# The log format is a JSON array containing the log level, the ISO 8601
	# date string, the process number, the filename and line number of the
	# log statement, and finally any message object that was logged:
	# ["INFO", "<ISO8601>", <PROC>, "<FILE:LINE>", {<MESSAGE>}]
	
	logformat = '["%(levelname)s", "%(asctime)s", %(process)d, "%(filename)s:%(lineno)d", %(msg)s]'
	logging.basicConfig(format=logformat, level=logging.INFO)
	
	proc = MailController(conf)
	signal.signal(signal.SIGTERM, proc.stop)
	proc.start()
	