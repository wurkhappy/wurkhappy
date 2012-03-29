
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
		with open(self.filename, 'w+') as f:
			f.write(str(d) + "\n")
			f.flush()



# -------------------------------------------------------------------
# Command line startup
# -------------------------------------------------------------------

def commandLineStartup(processClass):
	from optparse import OptionParser
	import daemon
	import os, os.path
	import pwd
	import sys
	import yaml
	import signal
	import subprocess
	
	usage = 'usage: %s [-c config] [-p pidfile] [-f logfile] [-d] start|stop|refresh' % sys.argv[0]
	
	parser = OptionParser(usage)
	
	parser.add_option("-c", "--config", dest="config",
		help="specify a configuration file",
		metavar="CONF", default="config.yaml")
	parser.add_option("-u", "--user", dest="user",
		help="set the user for the child processes",
		metavar="USER", default=None)
	parser.add_option("-p", "--pidfile", dest="pidfile",
		help="specify a PID file when using the --daemon flag", metavar="FILE",
		default="/var/spool/wh_notificationd.pid")
	parser.add_option("-f", "--logfile", dest="logfile",
		help="redirect STDOUT and STDERR to the specified file",
		metavar="FILE", default="/var/log/notification.log")
	parser.add_option("-d", "--daemon", dest="daemonize",
		help="detach from console and run as daemon",
		action="store_true")
	
	(options, args) = parser.parse_args()
	
	if options.daemonize:
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
	
	if options.daemonize:
		ctx = daemon.DaemonContext(stdout=logfile, stderr=logfile, working_directory='.')
		ctx.open()
		
		procID = procParser.write(os.getpid())
	
	# The log format is a JSON array containing the log level, the ISO 8601
	# date string, the process number, the filename and line number of the
	# log statement, and finally any message object that was logged:
	# ["INFO", "<ISO8601>", <PROC>, "<FILE:LINE>", {<MESSAGE>}]
	
	logformat = '["%(levelname)s", "%(asctime)s", %(process)d, "%(filename)s:%(lineno)d", %(msg)s]'
	
	if options.daemonize:
		logging.basicConfig(format=logformat, level=logging.INFO)
	else:
		logging.basicConfig(
			format=logformat, level=logging.INFO,
			filename=options.logfile, filemode='a+'
		)
	
	proc = processClass(conf)
	signal.signal(signal.SIGTERM, proc.stop)
	proc.start()
