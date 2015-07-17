import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from stapLabModulePlot import stapLabModulePlot
from threading import Lock
import numpy as np

class stapLabModuleSyscall(stapLabModulePlot):
	def __init__(self,name = None,queue = None,args = {}):
		super(stapLabModuleSyscall,self).__init__(None,queue,args=args)
		self.id				= id(self)
		self.log			= print if 'logStream' not in args else args['logStream']
		self.name			= name if name is not None else self.__class__.__name__
		self.queue			= queue
		self.stapRequirements		= { "syscall" : [] }	# {stapModuleName:[Args]}
		self.callbackRequirements	= [ (self.plot,500) ]
		self.stats			= {}			# {syscall:count}
		self.rects			= None
		self.subplot 			= None
		self.lock			= Lock()
		
	def plot(self,figure):
		#self.log("module %s plot()" % str(self))
		#TODO fix artefacts in bars. (eventually double-drawn bars?)
		if self.subplot is not None:
			self.lock.acquire()
			if len(self.stats) > 0:			
				#figure.clf()
				indices = list(self.stats)
				values	= self.stats.values()
				width	= 0.8
				if self.rects is None or len(self.rects) < len(values):
					self.rects	= self.subplot.bar(range(len(indices)), values, width, log=True)
				else:
					for rect, h in zip(self.rects, values):
						rect.set_height(h)
				self.subplot.set_xticks(np.arange(len(indices)) + width/2)
				self.subplot.set_xticklabels(indices, rotation=90)
			else:
				self.subplot.text(0, 0, "no Data yet", fontsize=12)
				#sleep(1)
			self.lock.release()
			figure.tight_layout()			
			figure.canvas.draw()
		else:
			self.subplot = figure.add_subplot(111)
			self.subplot.set_title("syscall overall call counter")
			self.subplot.set_xlabel("syscall_name")
			self.subplot.set_ylabel("count")

	def processData(self,data):
		self.lock.acquire()
		syscall		= data.split()[1]
		if syscall not in self.stats:
			self.stats[syscall]	= 1
		else:
			self.stats[syscall]	+= 1
		self.lock.release()
	
	def onStop(self):
		self.log("stats:\n%s" % str(self.stats))


