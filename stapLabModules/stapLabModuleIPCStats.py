import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from stapLabModulePlot import stapLabModulePlot
from threading import Thread,Lock
from queue import Queue
from time import sleep
from datetime import datetime
import numpy as np

class stapLabModuleIPCStats(stapLabModulePlot):
	def __init__(self,name = None,queue = None,logStream=print):
		super(stapLabModuleIPCStats,self).__init__(None,queue,logStream)
		self.id				= id(self)
		self.log			= logStream
		self.name			= name if name is not None else self.__class__.__name__
		self.queue			= queue
		self.stapRequirements		= { 
							#[]
						}
		self.generatorRequirements	= { 
							"connectionStatsGeneratorModule":[]
						}
		self.blackListIP		= {"source":["127.0.0.1"],"dest":["127.0.0.1"]}	# IP's to ignore {'in':["ip"],'out':["ip"]}
		#TODO Port Filter?
		self.callbackRequirements	= [ (self.plot,500) ]			# [(callbackFunc, timer)]
		#self.stats			= {}					# {ipPort:{Connections}}
		#self.scale			= 1000					# measure in bytes / scale
		#self.subplot			= [None,None]
		#self.rects			= {'TCP':(None,None),'UDP':(None,None)}
		self.lock			= Lock()

	def plot(self,figure):
		self.lock.acquire()
		self.log("plot()")
		self.lock.release()

	def processData(self,data):
		self.lock.acquire()
		self.log("module %s received data: %s" % (str(self), data))
		self.lock.release()
	
	def onStop(self):
		self.log("stats:\n%s" % str(self.stats))


