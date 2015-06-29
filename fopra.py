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
from datetime import datetime

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
		self.dt		= None
		self.stapModules = {
					# moduleName: [stapFile path, grapType, additionalArgs...]
					# grapType can be bar, line, cake
					'dummy':['gather/dummy.stp'],			# dummy skript that just prints the unixtime every sec
					'udp':['gather/udp.stp'],
					'tcp_sr_stats':['gather/tcp_sr_stats.stp'],	# tcp send /receive stats
					'tcp_c_tats':['gather/tcp.stp'],		# tcp connection stats
					# the socket module is broken since the last kernel update, i don't know why yet
					#'socket_verbose':['gather/socket_verbose.stp','-g','-GprintRawData=0','-GprintSendRecv=1','-GprintOpenClose=1'],
					'socket':['gather/socket.stp','-GexcludeList="sshd avahi-daemon"'],
					'syscall':['gather/syscall.stp','-Gprint_time_spent=1','-GprintData=1']
				}		
		
		def dummyUpd(data):
			if data is not None:
				self.data[data.split(" ")[1].split(":")[1]] = 1
			else:
				self.log("empty data")

		def syscallUpd(data):
			if data is not None:
				s = data.split()[1]
				if self.data.has_key(s):
					self.data[s] += 1
				else:
					self.data[s] = 1
			else:
				self.log("empty data")

		scale	= 1000

		def tcpUpd(data):
			if data is not None:
				parts	= data.split()
				action	= {}
				# update recv data
				def updRecv(count=-1):
					if count >= 0:
						#self.log("updR:%d" % count)
						self.data[1] += int( count / scale)
					
				# update recv data
				def updSend(count=-1):
					if count >= 0:
						#self.log("updS:%d" % count)
						self.data[0] += int( count / scale)

				# number of bytes received / sent
				if self.module == 'tcp_sr_stats':
					action	= {
						'tcp.recvmsg':(lambda d: None),
						'tcp.recvmsg.return':(lambda d: updRecv(int(d[2][5:])) ),
						'tcp.sendmsg':(lambda d: None),
						'tcp.sendmsg.return':(lambda d: updSend(int(d[0][11:])) ),
						'tcp.disconnect':(lambda d: None),
						'tcp.disconnect.return':(lambda d: None)
					}
				# who did we talk to from where
				elif self.module == 'tcp_c_stats':
					action	= {
						'tcp.recvmsg':(lambda d: None),
						'tcp.recvmsg.return':(lambda d: None),
						'tcp.sendmsg':(lambda d: None),
						'tcp.sendmsg.return':(lambda d: None),
						'tcp.disconnect':(lambda d: None),
						'tcp.disconnect.return':(lambda d: None)
					}
				else:
					self.log("tcp parse error, no module parser found for: %s" % self.module)
					self.stop()

				# trigger action according to values we just set
				#print parts[1:]
				action[parts[0]](parts[1:])
			else:	
				self.log("empty data")
			
		self.smDataExtr	= {
					'syscall':syscallUpd,
					'tcp_sr_stats':tcpUpd,
					'udp':None,
					'dummy':dummyUpd
				}

		# create a watchdog-Thread, that stops stapLab if the target pid terminates
		self.wd		= Thread(target=self.watchdogWorkerMain)
		self.wd.daemon	= True
		self.wd.running	= True
		
		# graph data
		self.data	= None
		self.dataHist	= None
		self.dhPointer	= -1
		self.timer	= None
		self.lastUpd	= -1

		# draw gui every x seconds
		self.guiDrawInterval	= 0.1
	
		self.parseArgs()

		# what graph to draw for every model
		# possible values could be line,bar,graph,cake...?
		self.smGraphType	= {
					'dummy':'line',	
					'udp':'?',
					'tcp_sr_stats':'line',
					'tcp_c_tats':'bar',
					#'socket_verbose':'?',
					'socket':'?',
					'syscall':'bar'
				}[self.module]
		
		# set correct dataType for self.data
		self.data	= {
					'dummy':[],	
					'udp':None,		#TODO, should be the same one as tcp
					'tcp_sr_stats':[0,0],	# data[0] = send , data[1] = recieve,
					'tcp_c_tats':None,	#TODO
					#'socket_verbose':'?',
					'socket':None,		#TODO
					'syscall':{}
				}[self.module]
	
		self.dataHist	= {
					'dummy':None,	
					'udp':None,			#TODO, should be the same one as tcp
					'tcp_sr_stats':[[0,0]]*60, 	# we will keep track of the last 60 values
					'tcp_c_tats':None,#TODO
					#'socket_verbose':'?',
					'socket':None,			#TODO
					'syscall':{}
				}[self.module]
	
		# set timer if we need one. Update Interval for self.dataHist in seconds.
		self.timer	= {
					'dummy':None,	
					'udp':None,#TODO
					'tcp_sr_stats':1,
					'tcp_c_tats':None,		#TODO, should be the saaction[parts[0]](parts[1:])me one as tcp_sr_tats
					#'socket_verbose':'?',
					'socket':None,			#TODO
					'syscall':None
				}[self.module]

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
		self.log("watchdog started")dp':None,

		while self.running and self.processRunning(self.tid):
			sleep(0.1)

		self.log("watchdog indicates that target pid (%d) has terminated" % self.tid)
		if self.running:
			self.stop()
		self.log("watchdog terminated")
	
	def enqOutput(self):
		while self.handle.poll() is not None:
			sleep(0.01)
		for line in iter(self.handle.stdout.readline, b''):
			self.q.put(line.rstrip())
		self.handle.stdout.close()
		
	def updateDataHistory(self):
		delta = (datetime.now() - self.lastUpd)
		if delta.total_seconds() > self.timer:
			self.dataHist	= self.dataHist[1:] + [self.data]
			self.data	= [0,0]
			self.lastUpd	= datetime.now()

	def updateData(self):
		self.log("update data")
		while self.dt.running:
			while not self.q.empty():
				data = self.q.get()
				self.smDataExtr[self.module](data)
			sleep(0.1)
			if self.timer is not None:
				self.updateDataHistory()
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
			scale_factor = 100.0
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
		if self.gui:
			try:
				plt.clf()
				self.fig.canvas.stop_event_loop()
				if self.data is not None and len(self.data) > 0:
					#self.log("plotting: %s" % str(self.data))
					if self.smGraphType is 'line':
						histLen	= len(self.dataHist)
						if self.module == 'tcp_sr_stats':
							indices	= ['send','received']
							values	= [map(lambda x:x[0], self.dataHist), map(lambda x: x[1], self.dataHist)]
						timeRange	= range(0,histLen)
						plt.plot(timeRange,values[0])
						plt.plot(timeRange,values[1])
						plt.title("sent / received tcp traffic")
						plt.grid(True)
						plt.xlabel("time")
						plt.ylabel("traffic in kilobytes")
						plt.legend(indices, loc='upper left')
					elif self.smGraphType is 'bar':
						# convert data to indices and values:
						if self.module == 'syscall':
							indices = list(self.data)
							values	= self.data.values()
						width	= 0.8
						ax = pl.subplot(111)
						ax.bar(range(len(indices)), values, width, log=True)
						ax.set_xticks(np.arange(len(indices)) + width/2)
						ax.set_xticklabels(indices, rotation=90)
						self.fig.tight_layout()
					elif self.smGraphType is 'graph':
						pass
					elif self.smGraphType is 'cake':
						pass
				else:
					self.log("self.data is None, nothing to draw!")
					#for i in range(1000):
					#	y = np.random.random()
					#	plt.scatter(i, y)
				self.fig.canvas.start_event_loop(timeout=1)
				plt.draw()
			except:
				self.log("error in draw function")
				self.log("data: %s" % str(self.data))
				raise
		else:
			self.log("data: %s" % str(self.data))

	def run(self):
		self.dispatchStapModule()
		self.t.running		= True
		self.dt.running		= True
		if self.timer is not None:
			self.lastUpd	= datetime.now()
			self.dhPointer	= 0
		# start async threads
		self.t.start()
		self.wd.start()
		self.dt.start()
		if self.gui:
			self.initGraphModule()
		self.log("entering mainLoop")
		while self.running:			
			self.drawGUI()
			sleep(self.guiDrawInterval)
	
	def processRunning(self,pid):
		# check if process is alive by sending signal 0
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
