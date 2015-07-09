import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from threading import Thread
from queue import Queue
from time import sleep
from datetime import datetime

# this is the base module for the stapLab Modules that plot stuff. (i.e. all at the moment)
# all one needs to do is override the functions like 
# plot(), processData(), initGUI() and, if necessary, 
# stop() or __init__() (don't forget to call self.__super__(className,self)(...)!)
class stapLabModulePlot(object):
	def __init__(self,name = None,queue = None, args = {}, logStream=print,guiRefreshTime=0.5):
		self.id				= id(self)
		self.log			= logStream
		self.name			= "stapLabModulePlot" if name is not None else self.__class__.__name__
		self.queue			= queue
		self.args			= args
		self.stapRequirements		= {	# "stapModuleName":["Args"] 	<-- stapModules to start and connect with this stapLabModule
						}
		self.callbackRequirements	= [ (self.plot,500) ]	# callbacks to be called by a timer run in the main thread
		self.guiRefreshTime		= guiRefreshTime
		self.thread			= Thread(target=self.run)
		self.thread.daemon		= True
		self.thread.running		= True
		self.thread.start()


	def __str__(self):
		return "<%s(id:%d), args=%s, queue=%s,req= %s>" % ( 		self.name,
										self.id,
										str(self.args),
										str(self.queue),
										str(self.stapRequirements)
									)
		
	def enqData(self,data):
		if isinstance(self.queue,Queue):
			self.queue.put(data)		# this call is blocking. This is intentional, so we are thread-safe (on the cost of speed).

	# this function is to be overridden by derived classes that plot stuff. The drawing logic is to be inserted here.
	def plot(self,figure = None):
		self.log("module %s plot()" % str(self))

	# this function is to be overridden by derived classes and is set to contain the data handling logic.
	def processData(self,data):
		self.log("processData")

	def run(self):
		self.log("module %s entering mainLoop" % self)
		while self.thread.running:
			if isinstance(self.queue,Queue):
				while not self.queue.empty():
					data	= self.queue.get()
					self.processData(data)
			sleep(0.1)
		self.log("module %s leaving mainLoop" % self)

	# this function is to be overridden by deriving classes and is called once the mainloop stopped.
	def onStop(self):
		pass

	def stop(self):
		self.log("stopping %s" % self)
		if hasattr(self,"onStop"):
			self.onStop()
		self.thread.running		= False


