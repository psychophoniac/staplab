import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from threading import Thread
from queue import Queue
from time import sleep
from stapLabModulePlot import stapLabModulePlot

#this is the base module for the stapLab Modules
class stapLabModuleSyscall(stapLabModulePlot):
	def __init__(self,name = None,queue = None,logStream=print):
		super(stapLabModuleSyscall,self).__init__(None,queue,logStream)
		self.id			= id(self)
		self.log		= logStream
		self.name		= name if name is not None else self.__class__.__name__
		self.queue		= queue
		self.stapRequirements	= {"syscall":[]}	# {stapModuleName:[Args]}
		self.refRequirements	= ['plt','pl']
		self.stats		= {}			# {syscall:count}
		
	def plot(self):
		self.log("plot syscall stuff")

	def processData(self,data):
		syscall		= data.split()[1]
		if syscall not in self.stats:
			self.stats[syscall]	= 1
		else:
			self.stats[syscall]	+= 1
	
	def onStop(self):
		self.log("stats:\n%s" % str(self.stats))
