import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from threading import Thread
from queue import Queue
from time import sleep
from stapLabModulePlot import stapLabModulePlot

#this is the base module for the stapLab Modules
class stapLabModuleSyscall(stapLabModulePlot):
	def __init__(self,name,queue,logStream=print):
		self.id			= id(self)
		self.log		= logStream
		self.name		= name
		self.queue		= queue
		super(stapLabModuleSyscall,self).__init__("stapLabModulePlot",queue,logStream)
		self.stapRequirements	= {"syscall":[]}	# {stapModuleName:[Args]}
		self.refRequirements	= ['plt','pl']
		self.stats		= {}			# {syscall:count}
		#self.thread		= Thread(target=self.run)
		#self.thread.daemon	= True
		#self.thread.running	= True
		#self.thread.start()

	def __str__(self):
		return "<%s(id:%d), queue=%s,req= %s %s>" % (self.name,self.id,str(self.queue),str(self.stapRequirements),str(self.refRequirements))

	def setReferences(self,refDict):
		#TODO automatize this?
		self.plt	= refDict['plt']
		self.pl		= refDict['pl']
		
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
