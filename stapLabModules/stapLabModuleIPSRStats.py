import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from stapLabModulePlot import stapLabModulePlot
from threading import Thread,Lock
from queue import Queue
from time import sleep
from datetime import datetime
import numpy as np

class stapLabModuleIPSRStats(stapLabModulePlot):
	def __init__(self,name = None,queue = None,logStream=print):
		super(stapLabModuleIPSRStats,self).__init__(None,queue,logStream)
		self.id				= id(self)
		self.log			= logStream
		self.name			= name if name is not None else self.__class__.__name__
		self.queue			= queue
		self.stapRequirements		= { 
							"ip_sr_activity":[]
						}
		self.blackListIP		= {"source":["127.0.0.1"],"dest":["127.0.0.1"]}	# IP's to ignore {'in':["ip"],'out':["ip"]}
		#TODO: Port Filter?
		self.callbackRequirements	= [ (self.plot,500) ]				# [(callbackFunc, timer)]
		self.stats			= {'TCP':{},'UDP':{}}				# {tcp:{port:(send,recv)},udp:{port:(send,recv)}}
		self.scale			= 1000						# measure in bytes / scale
		self.subplot			= [None,None]
		self.rects			= {'TCP':(None,None),'UDP':(None,None)}
		self.lock			= Lock()

	def plotData(self,proto,subplot,figure):
		# TODO test if UDP is actually drawn correctly
		indices		= sorted(list(self.stats[proto]))
		data		= [ self.stats[proto][idx] for idx in indices ]
		upd		= False
		if len(indices) > 0:
			try:
				width		= 0.25
				valuesSent	= list(map((lambda x: x[0]) , data))
				valuesRecv	= list(map((lambda x: x[1]) , data))
				
				if self.rects[proto][0] is None or len(self.rects[proto][0]) < len(indices):
					ar			= np.arange(len(indices))
					self.rects[proto]	= (subplot.bar(ar, valuesSent, width, log = True, color='r') , 
									subplot.bar(ar + width, valuesRecv, width, log = True, color='g') )
				else:
					for rect, h in zip(self.rects[proto][0], valuesSent):
						rect.set_height(h)
					for rect, h in zip(self.rects[proto][1], valuesRecv):
						rect.set_height(h)
					subplot.set_xticks(np.arange(len(indices)) + width)
					subplot.set_xticklabels(indices, rotation=90)
					subplot.legend((self.rects[proto][0],self.rects[proto][1]), ('sent','recv'))
				figure.tight_layout()
				upd		= True
			# these are internal errors of matplotlib that happen on the beginning of data collection. silence them.
			# it is likely they happen since so much async stuff is going on here and that is not what matplotlib was built for
			except ValueError:	
				pass
			except AttributeError:
				pass
		else:
			idx = {'TCP':0,'UDP':1}[proto]
			self.subplot[idx].text(0, 0, "no Data yet", fontsize=12)
		return upd
		
	def plot(self,figure):
		self.lock.acquire()
		if self.subplot[0] is None:
			self.subplot[0]	= figure.add_subplot(211, frame_on=True, title="TCP S/R stats", xlabel="port", ylabel="kilobytes")
		if self.subplot[1] is None:
			self.subplot[1]	= figure.add_subplot(212, frame_on=True, title="UDP S/R stats", xlabel="port", ylabel="kilobytes")
		
		upd	= self.plotData('TCP',self.subplot[0],figure)
		upd	= self.plotData('UDP',self.subplot[1],figure) or upd
		if upd:
			#fig.tight_layout
			figure.canvas.draw()
		self.lock.release()

	def processData(self,data):
		self.lock.acquire()
		# pattern: [ TCP | UDP ]{1}.[ send | recv ]{1}[source:sIP:sPort dest:dIP,
		context, *var		= data.split()
		# match [ tcp | udp ]{1}.[ send | recv ]{1}
		proto,func		= context.split(".")
		# match [source... , dest..., size...]
		source, dest, size	= tuple(var)
		size			= size.split(":")[1]
		# match source:sourceIP:sourcePort
		sip, sport		= source.split(":")[1:]
		# match dest like above
		dip, dport		= dest.split(":")[1:]
		if sip not in self.blackListIP['source'] and dip not in self.blackListIP['dest']:
			port	= sport if func == 'send' else dport
			if port not in self.stats[proto]:
				self.stats[proto][port] 	= (0,0)

			self.stats[proto][port]	= {
							'send': (lambda x,z: (x[0]+z,x[1])),
							'recv': (lambda x,z: (x[0],x[1]+z))
						}[func](self.stats[proto][port],int(size))
		#self.stats['UDP']	= self.stats['TCP']	#TODO UDP testing. should work, though
		self.lock.release()
	
	def onStop(self):
		self.log("stats:\n%s" % str(self.stats))


