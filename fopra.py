import sys
#import os.path
import os
import errno
for folder in ["gather", "process", "view"]:
	sys.path.append(folder)
import argparse
from time import sleep
import signal
import subprocess
from Queue import Queue, Empty
from threading import Thread
import numpy as np
import matplotlib.pyplot as plt
import pylab as pl

class stapLab():

	def __init__(self):
		self.running	= True	#
		self.module	= None	# stapModule to run, defined in self.stapModules
		self.tid	= -1	# target process ID
		self.moduleArgs = []	# additional arguments for the stapModule
		self.gui	= True	# enable or disable gui
		self.handle	= None	# the process handle for the stapModule
		self.q		= None	# queue for the output of the stapModule
		self.t		= None	# Thread to enqueue the output from the stapModule
		self.stapModules = {
					# moduleName: [stapFile path, grapType, additionalArgs...]
					# grapType can be bar, line, cake
					'dummy':['gather/dummy.stp'],
					'udp':['gather/udp.stp'],
					'tcp':['gather/tcp.stp'],
					# the socket module is broken since the last kernel update, i don't know why yet
					#'socket':['gather/socket.stp','-g','-GprintRawData=0','-GprintSendRecv=1','-GprintOpenClose=1'],
					'syscall':['gather/syscall.stp','-Gprint_time_spent=1','-GprintData=1']
				}
		
		def dummyUpd(data):
			if data is not None:
				self.data[data.split(" ")[1].split(":")[1]] = 1
				#self.data.append(int(data.split(" ")[1].split(":")[1]))
				#self.data2.append(
			else:
				self.log("empty data")

		def syscallUpd(data):
			if data is not None:
				s = data.split()[1]
				if self.data.has_key(s):
					self.data[s] += 1
				else:
					self.data[s] = 1
			
		self.smDataExtr	= {
					#'syscall':self.updateSyscallData,
					'syscall':syscallUpd,
					'tcp':self.updateTcpData,
					'udp':self.updateUdpData,
					#'socket':self.updateSocketData,
					'dummy':dummyUpd
				}

		# create a watchdog-Thread, that stops stapLab if the target pid terminates
		self.wd		= Thread(target=self.watchdogWorkerMain)
		self.wd.daemon	= True
		self.wd.running	= True
		
		# graph data
		self.data	= None
		self.data2	= None

		# draw gui every x seconds
		self.guiDrawInterval	= 0.1
	
		self.parseArgs()

		# catch interrupt-Signal
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
		parser.add_argument('-g', '--gui-update-interval', type=float, nargs="?", metavar="gint",default=0.1, 
					help='gui update interval in seconds. Takes a float, e.g. 0.1 (default). 0 means update as fast as possible.')
		parser.add_argument('-i','--info', type=str, metavar="moduleInfo",
					help="list information about additional arguments for the specified stapModule")
		parser.add_argument('-l','--list-available-modules', action="store_true", help="list available modules")
		parser.add_argument('-a', type=str, metavar="argument", nargs="+", default=[],
					help="additional arguments for the module. For a listing use the -i flag and specify the module name as argument")
		parser.add_argument('-n','--no-gui', action="store_true", help="if set, disable GUI and write module output to stdout")
		args = vars(parser.parse_args())
		#self.log(args)

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
	
		if(args["gui_update_interval"] is not None):
			if(args["gui_update_interval"] >= 0):
				self.guiDrawInterval = args["gui_update_interval"]
			else:
				self.log("invalid gui update value:%d" % args["gui_update_interval"])
				self.stop()

		if(args["module"] is not None):
			self.module=args["module"]
	
		maxPid = int(open("/proc/sys/kernel/pid_max").read().replace('\n',''))
		if(args["targetPid"] > 0 and args["targetPid"] < maxPid):
			self.tid = args["targetPid"]
		else:
			self.log("invalid pid provided: %d" % args["targetPid"])
			self.stop()
	

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
			self.q		= Queue()
			self.t 		= Thread(target=self.outputWorkerMain)
			self.t.running	= False
			self.t.daemon 	= True
			# data update Thread
			self.dt		= Thread(target=self.updateData)
			self.dt.daemon	= True
			self.dt.running	= False
		else:
			self.log("invalid module provided: " + str(self.module))
			sys.exit(-1)
	
	def outputWorkerMain(self):
		self.log("outputWorker started")
		self.enqOutput()
		self.log("outputWorker terminated")

	def watchdogWorkerMain(self):
		self.log("watchdog started")

		while self.running and self.processRunning(self.tid):
			sleep(0.1)

		self.log("watchdog indicates that target pid (%d) has terminated" % self.tid)
		if self.running:
			self.stop()
		self.log("watchdog terminated")
	
	def enqOutput(self):
		#self.log("enq start")
		while self.handle.poll() is not None:
			sleep(0.01)
		for line in iter(self.handle.stdout.readline, b''):
			#self.updateData(line.rstrip())	
			self.q.put(line.rstrip())
		self.handle.stdout.close()
		#self.log("enq end")	

	def updateSyscallData(self,data=""):
		pass
		
	#self.updateDummyData(self,data=""):
	#	pass	

	def updateTcpData(self,data=""):
		pass	

	def updateUdpData(self,data=""):
		pass	

	def updateData(self):
		self.log("update data")
		while self.dt.running:
			while not self.q.empty():
				#self.log("updateData(), q=%s" % str(self.q))
				data = self.q.get()
				if not self.gui:
					self.log("data: %s" % data)
				else:
					self.smDataExtr[self.module](data)
					#self.log("updated data")
			sleep(0.1)
		self.log("update data ende")
			
	
	def initGraphModule(self):
		self.log("initializing Graph worker")
		self.fig = pl.figure()
		#plt.draw()
		# TODO:
		# close this programm when graph window is closed,
		# aka connect closing-event from gui to self.close
		#plt.gcf().canvas.mpl_connect('delete-event',self.stop)
		
		def onresize(event):
			width = event.width
			scale_factor = 100.
			data_range = width/scale_factor
			start, end = plt.xlim()
			new_end = start+data_range
			plt.xlim((start, new_end))		
		cid = self.fig.canvas.mpl_connect('resize_event', onresize)

		self.log("show graph Window")
		plt.ion()
		plt.show(block=False)
		self.log("grap worker initialized")		
	
	def drawGUI(self):
		#self.log("drawGUI()")
		if self.gui:
			try:
				plt.clf()
				self.fig.canvas.stop_event_loop()
				if self.data is not None and len(self.data) > 0:
					#self.log("plotting: %s" % str(self.data))
					# line graph:
					#plt.plot(self.data)
					# bar graph:
					indices = list(self.data)
					values	= self.data.values()
					width	= 0.8
					ax = pl.subplot(111)
					#ax.bar(range(len(indices)), map((lambda x: int(x)), indices), width)
					ax.bar(range(len(indices)), values, width, log=True)
					ax.set_xticks(np.arange(len(indices)) + width/2)
					ax.set_xticklabels(indices, rotation=90)
					self.fig.tight_layout()
					#print(self.data)
					#self.fig.show()
				else:
					self.log("self.data is None, nothing to draw!")
					for i in range(1000):
						y = np.random.random()
						plt.scatter(i, y)
				self.fig.canvas.start_event_loop(timeout=1)
				plt.draw()
			except:
				self.log("error in draw function")
				self.log("data: %s" % str(self.data))
				raise
		else:
			return

	def run(self):
		self.dispatchStapModule()
		self.t.running		= True
		self.dt.running		= True
		if self.data is None:
			#self.data	= []
			self.data	= {}
		if self.data2 is None:
			self.data2	= []
		# start async threads
		self.t.start()
		self.wd.start()
		self.dt.start()
		if self.gui:
			self.initGraphModule()
		self.log("entering mainLoop")
		while self.running:
			#self.updateData()			
			self.drawGUI()
			sleep(self.guiDrawInterval)
	
	def processRunning(self,pid):
		#return os.path.exists("/proc/%d" % pid)
		# see http://stackoverflow.com/questions/568271
		try:
		        os.kill(pid, 0)
		except OSError as err:
	     		if err.errno == errno.ESRCH:
        		# ESRCH == No such process
				return False
			elif err.errno == errno.EPERM:
			# EPERM clearly means there's a process to deny access to
				return True
		        else:
				# According to "man 2 kill" possible error values are
				# (EINVAL, EPERM, ESRCH)
				raise
		else:
			# process is existent
			return True

	def stop(self):
		self.log("stop")
		self.running 	= False
		# close figure window
		plt.close()
		# stop watchdog
		if self.wd is not None: 
			self.wd.running	= False
		# stop output worker
		if self.t is not None:
			self.t.running	= False
		# stop data update Thread
		if self.dt is not None:
			self.dt.running = False
		# stop stapModule
		if self.handle is not None:
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
