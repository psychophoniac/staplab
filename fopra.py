import sys
import os.path
for folder in ["gather", "process", "view"]:
	sys.path.append(folder)
import argparse
from time import sleep
import signal
import subprocess
from Queue import Queue, Empty
from threading import Thread

class stapLab():

	def __init__(self):
		self.running	= True
		self.module	= None
		self.tid	= -1
		self.moduleArgs = []
		self.gui	= False
		self.handle	= None
		self.q		= Queue()
		self.stapModules = {
					'dummy':['gather/dummy.stp'],
					'udp':['gather/udp.stp'],
					'tcp':['gather/tcp.stp'],
					# the socket module is broken since the last kernel update, i don't know why yet
					'socket':['gather/socket.stp','-g','-GprintRawData=0','-GprintSendRecv=1','-GprintOpenClose=1'],
					'syscall':['gather/syscall.stp','-Gprint_time_spent=1','-GprintData=1']
				}

		self.parseArgs()

		# catch Interrupt-Signal
		signal.signal(signal.SIGINT, lambda x,y: self.stop())
		# catch terminate-Signal
		signal.signal(signal.SIGTERM, lambda x,y: self.stop())

	def log(self,data):
		print data

	def parseArgs(self):
		parser = argparse.ArgumentParser(description='staplab - systemtap module dispatcher and data visualizer')
		parser.add_argument('module', type=str, nargs="?", metavar="module",default=None, 
					help='module to be dispatched, see -i without argument for a list')
		parser.add_argument('targetPid', type=int, nargs="?", metavar="tid",default=-1, 
					help='target Pid, must be in between 0 and the MAX_PID limit (usually residing in /proc/sys/kernel/pid_max)')
		parser.add_argument('-i','--info', type=str, metavar="moduleInfo",
					help="list information about additional arguments for the specified stapModule")
		parser.add_argument('-l','--list-available-modules', action="store_true", help="list available modules")
		parser.add_argument('-a', type=str, metavar="argument", nargs="+", default=[],
					help="additional arguments for the module. For a listing use the -i flag and specify the module name as argument")
		parser.add_argument('-n','--no-gui', action="store_true", help="if set, disable GUI and write module output to stdout")
		args = vars(parser.parse_args())
		self.log(args)

		if(args["list_available_modules"]):
			# list available modules
			self.showAvailableModules()
			self.stop()

		if(args["info"] is not None):
			# list module information
			self.showModuleInfo(args["i"])
			self.stop()

		if(args["no_gui"]):
			self.log("disabling GUI")
			self.gui=False
		else:
			self.gui=True

		if(args["module"] is not None):
			self.module=args["module"]
	
		maxPid = int(open("/proc/sys/kernel/pid_max").read().replace('\n',''))
		if(args["targetPid"] > 0 and args["targetPid"] < maxPid):
			self.tid = args["targetPid"]
		else:
			self.log("invalid pid provided: %d" % args["targetPid"])
	

		if( len(args["a"]) > 0):
			self.moduleArgs=args["a"]

	def showAvailableModules(self):
		for m in self.stapModules:
			# there is some switches the user is not ought to use, filter them out
			# we know them by the "=" character in the stapModules variable
			userArgs=filter(lambda x: "=" in x, self.stapModules[m][1:])
			self.log("%s, args: %s" % (m, userArgs))

	def showModuleInfo(self,module="test"):
		self.log("moduleInfo " + module)

	def dispatchStapModule(self):
		if self.module is not None and self.module in self.stapModules:
			self.log("dispatching Module %s on target Pid %d" %(self.module, self.tid))
			cmd 	= [
					'stap', 				# stap bin
					'-s 16', 				# max kernel buffer for stap <-> user com
					'-DMAXSTRINGLEN=16384',			# max String length
					self.stapModules[self.module][0]	# stap script for module
				]
			cmd 	+= self.moduleArgs
			cmd 	+= ['-x', str(self.tid)]				# stap target PID
			self.log("dispatch command: %s" % cmd)
			self.handle = subprocess.Popen(
							cmd,
							stdout=subprocess.PIPE,
							stderr=subprocess.STDOUT,	# pipe errors to stdout
							universal_newlines=True
						)
			self.log("subprocess running, pid %i" % self.handle.pid)
			self.t 		= Thread(target=self.outputWorkerMain)
			self.t.running	= False
			self.t.daemon 	= True
		else:
			self.log("invalid module provided: " + str(self.module))
			sys.exit(-1)
	
	def outputWorkerMain(self):
		self.enqOutput()
	
	def enqOutput(self):
		#self.log("enq start")
		while self.handle.poll() is not None:
			sleep(0.1)
		for line in iter(self.handle.stdout.readline, b''):
			self.updateData(line.rstrip())
		self.handle.stdout.close()
		#self.log("enq end")

	def updateData(self,data=[]):
		self.log("data: %s" % data)
	
	def drawGUI(self):
		#TODO
		sleep(1)

	def run(self):
		self.dispatchStapModule()
		self.log("starting output worker thread")
		self.t.running	= True
		self.t.start()
		self.log("entering mainLoop")
		while self.running:
			#self.log("mainLoop")
			self.drawGUI()
	
	def processRunning(self,pid):
		return os.path.exists("/proc/%d" % pid)

	def stop(self):
		self.log("stop")
		self.running 	= False
		self.t.running	= False
		self.handle.terminate()
		if(self.processRunning(self.handle.pid)):
			self.log("stap subprocess is still running, wait one second and check back")
			c = 0
			while(self.processRunning(self.handle.pid) and c < 10):
				sleep(0.1)
				c += 1
			self.log("stap subprocess is still running, sending kill signal")
			self.handle.kill()
			if not self.processRunning(self.handle.pid):
				self.log("could not kill process, pid: %d" % self.handle.pid)
			else:
				self.log("process killed")
		else:
			self.log("stap subprocess stopped")

		sys.exit(0)

if __name__ == "__main__":
	stapLab().run()

	sys.exit(0)
