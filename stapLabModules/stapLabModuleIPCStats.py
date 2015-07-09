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
	def __init__(self,name = None,queue = None,args = {},logStream=print):
		super(stapLabModuleIPCStats,self).__init__(None,queue,logStream)
		self.id				= id(self)
		self.log			= logStream
		self.name			= name if name is not None else self.__class__.__name__
		self.args			= args
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
		self.stats			= {}					# {ipPort:{Connections}}
		#self.scale			= 1000					# measure in bytes / scale
		self.subplot			= None
		#self.rects			= {'TCP':(None,None),'UDP':(None,None)}
		self.lock			= Lock()
		self.log(" %s init() done" % str(self))

	def plot(self,figure):
		self.lock.acquire()
		#self.log("plot()")
		if self.subplot is None:
			self.subplot	= figure.add_subplot(111, frame_on=True, title="", xlabel="port", ylabel="kilobytes")

		indices		= sorted(list(self.stats))
		if len(indices) > 0:
			self.subplot.clear()
			values			= [ self.stats[idx] for idx in indices ]	# bring values to order
			sumVal			= sum(values)					# sum of all elements
			values			= [ elem * 100 / sumVal for elem in values ]	# calculate percentage of pie for every element
			patches, texts, *rest 	= self.subplot.pie(
									values, 
									labels 		= indices, 
									colors		=('g', 'r', 'b', 'y', 'w'),
									pctdistance 	= 0.8,
									autopct		= (lambda pct: '{p:.2f}%  ({v:d})'.format(
																p=pct,	
																v=int(pct*sumVal/100.0)
																)
											)
								)
			#self.subplot.legend(patches, texts, loc="best")
			try:
				#self.subplot.axis('equal')
				figure.tight_layout()
				figure.canvas.draw()
				#figure.clf()
			except ValueError or AttributeError:
				pass
		else:
			self.subplot.text(0, 0, "no connection data", fontsize=12)
		self.lock.release()

	def processData(self,data):
		self.lock.acquire()
		self.stats	= {}	# clear stats
		#self.log("module %s received data: %s" % (str(self), data))
		dataIdxs	= data[0]
		for dataSet in data[1:]:	# first element contains the dataFields
			#for idx in dataIdxs:	# generic stuff can happen here...
			#	pass
			# we only care about the foreignAdress and Port.
			# keys:['proto', 'recvq', 'sendq', 'localAddress', 'foreignAddress', 'state', 'prog']
			if 'target-pid' in self.args:	# if he have a limitation on a target, honor it
				try:
					if 'prog' in dataSet:
						pid	= dataSet['prog'].split("/")[0]
						if pid != "-" and self.args != int(pid):
							continue
					else:	#TODO what do we do, if we don't know a pid?
						# -> most likely the connection does not matter, since it is likely we run under a different uid
						# and therefore have no insight on the processes' pid
						#print(dataSet)
						continue
				except KeyError:
					print(dataSet)
					raise
					#continue
			key	= dataSet['foreignAddress']
			if key not in self.stats:
				self.stats[key]	= 0
			self.stats[key]	+= 1
	
		#self.log("stats: %s" % self.stats)
			
		self.lock.release()
	
	def onStop(self):
		self.log("stats:\n%s" % str(self.stats))


