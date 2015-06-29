import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from stapLabModule import stapLabModule
from Queue import Queue
from threading import Thread
from time import sleep

class outputHandler():
	
	class Stream():
		# TODO use Threads for output distribution
		def __init__(self,stapModuleInstance,interval=0.1,withdraw=False):
			self.id				= id(self)
			self.name			= stapModuleInstance.name
			self.queue			= Queue()
			self.receivers			= []
			self.interval			= interval	# check every x seconds for output in queue. 0 means go as fast as possible (causes high CPU load)
			self.withdraw			= withdraw	# if True, drop incomming input if we have no listeners
			self.thread			= Thread(target=self.run)
			self.thread.daemon		= True
			self.thread.running		= True
			self.thread.start()
			stapModuleInstance.queue	= self.queue

		def log(self,logStr):
			print logStr
		
		def __str__(self):
			return "<Stream,name=%s,queue=%s,receivers=%s>" % (self.name, self.queue, self.receivers)
		
		def register(self,stapLabModuleInstance):
			if stapLabModuleInstance is not None:
				if stapLabModuleInstance not in self.receivers:
					self.receivers	+= [stapLabModuleInstance]
					stapLabModuleInstance.queue	= self.queue
					#self.log("registered %s to %s" % (str(stapLabModuleInstance), self.name))
				else:
					self.log("%s already in receivers of Stream %s" % (stapModuleInstance.name, self))

		def unregister(self,stapModuleInstance):
			if stapModuleInstance is not None:
				try:
					receivers.remove(stapModuleInstance)
				except ValueError:
					self.log("cannot unregister module %s to stream %s" %(stapModuleInstance,self))

		def emtpyQueue(self):
			with self.queue.mutex:
				self.queue.clear()

		def run(self):
			#self.log("%s entering mainLoop" % self)
			while self.thread.running:
				if not self.queue.empty():
					if len(self.receivers) > 0:
						data	= self.queue.get()
						for receiver in self.receivers:
							if receiver is not None:
								receiver.enqData(data)
					else:
						if self.withdraw:
							self.emptyQueue()
				sleep(self.interval)
			#self.log("%s leaving mainLoop" % self)

		def stop(self):
			self.thread.running	= False

	def __init__(self):
		self.streams		= {}	# {stapModule.id:<Stream>}

	def log(self,logStr):
		print logStr

	# register a systemtap-skript for output
	# returns the Queue
	def registerStapModule(self,stapModuleInstance):
		#self.log("registering %s" % stapModuleInstance.name)
		if not self.streams.has_key(stapModuleInstance.id):
			self.streams[stapModuleInstance.id]	= self.Stream(stapModuleInstance)
			#stapModuleInstance.queue		= self.streams[stapModuleInstance.id].queue
			return self.streams[stapModuleInstance.id]
		else:
			self.log("stream for %s with id %d already present!" % (stapModuleInstance.name, stapModuleInstance.id))
			return None

	# register a stapLab-module for receiving the output of a systemtap-script
	def registerStapLabModule(self,stapLabModule,stapModuleInstance):
		try:
			if stapModuleInstance is not None and self.streams.has_key(stapModuleInstance.id):
				#self.log("registering stapLabModule %s to stapModule %s" % (stapLabModule,stapModuleInstance.name))
				self.streams[stapModuleInstance.id].register(stapLabModule)
			else:
				raise KeyError
		except KeyError:
			self.log("cannot register module %s to stream %s" %(stapModuleInstance,self.streams[stapModuleInstance.id]))
		



