import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from stapLabModulePlot import stapLabModulePlot
from threading import Thread
from queue import Queue
from time import sleep
from datetime import datetime
import numpy as np

class stapLabModuleSyscall(stapLabModulePlot):
	def __init__(self,name = None,queue = None,logStream=print):
		super(stapLabModuleSyscall,self).__init__(None,queue,logStream)
		self.id				= id(self)
		self.log			= logStream
		self.name			= name if name is not None else self.__class__.__name__
		self.queue			= queue
		self.stapRequirements		= { "syscall" : [] }	# {stapModuleName:[Args]}
		#self.refRequirements		= [ 'plt', 'pl' ]
		self.callbackRequirements	= [ (self.plot,500) ]
		#self.refReqSet			= len(self.refRequirements) == 0
		self.stats			= {}			# {syscall:count}
		
	def plot(self,figure):
		self.log("module %s plot()" % str(self))
		if len(self.stats) > 0:
			figure.clf()
			#figure.canvas.stop_event_loop()
			indices = list(self.stats)
			values	= self.stats.values()
			width	= 0.8
			ax = figure.add_subplot(111)
			ax.bar(range(len(indices)), values, width, log=True)
			ax.set_xticks(np.arange(len(indices)) + width/2)
			ax.set_xticklabels(indices, rotation=90)
			ax.set_title("syscall overall call counter")
			ax.set_xlabel("syscall_name")
			ax.set_ylabel("count")
			figure.tight_layout()
		else:
			self.log("module %s waiting for data" % str(self))
			sleep(1)

	def processData(self,data):
		syscall		= data.split()[1]
		if syscall not in self.stats:
			self.stats[syscall]	= 1
		else:
			self.stats[syscall]	+= 1
	
	def onStop(self):
		self.log("stats:\n%s" % str(self.stats))


