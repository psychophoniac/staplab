import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from stapLabModule import stapLabModule
from queue import Queue
from threading import Thread
from time import sleep

class outputHandler():
	
	class Stream():
		# TODO use Threads for output distribution
		def __init__(self,stapModuleInstance,interval=0.1,withdraw=False,logStream=print):
			self.id				= id(self)
			self.log			= logStream
			self.name			= stapModuleInstance.name
			self.queue			= Queue()	# the input queue
			self.receivers			= []
			self.interval			= interval	# check every x seconds for output in queue. 0 means go as fast as possible (causes high CPU load)
			self.withdraw			= withdraw	# if True, drop incomming input if we have no listeners
			self.thread			= Thread(target=self.run)
			self.thread.daemon		= True
			self.thread.running		= True
			self.thread.start()
			stapModuleInstance.queue	= self.queue

		#def log(self,logStr):
		#	print logStr
		
		def __str__(self):
			return "<Stream,name=%s,queue=%s,receivers=%s>" % (self.name, self.queue, self.receivers)
		
		def register(self,stapLabModuleInstance):
			if stapLabModuleInstance is not None:
				if stapLabModuleInstance not in self.receivers:
					self.receivers	+= [stapLabModuleInstance]
					stapLabModuleInstance.queue	= self.queue
					self.log("registered %s to %s" % (str(stapLabModuleInstance), self.name))
				else:
					self.log("%s already in receivers of Stream %s" % (stapModuleInstance.name, self))

		def unregister(self,stapLabModuleInstance):
			if stapLabModuleInstance is not None:
				try:
					self.receivers.remove(stapLabModuleInstance)
					self.log("unregistered %s from %s" % (str(stapLabModuleInstance), self.name))
				except ValueError:
					self.log("cannot unregister module %s to stream %s" %(stapLabModuleInstance,self))

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

				for receiver in self.receivers:
					if not receiver.thread.running:
						self.unregister(receiver)

				sleep(self.interval)
			#self.log("%s leaving mainLoop" % self)

		def stop(self):
			self.thread.running	= False

	def __init__(self,logStream=print):
		self.log		= logStream
		self.streams		= {}	# {stapModule.id:<Stream>}

	# register a systemtap-skript for output
	# returns the Queue
	def registerStapModule(self,stapModuleInstance):
		#self.log("registering %s" % stapModuleInstance.name)
		if not stapModuleInstance.id in self.streams:
			self.streams[stapModuleInstance.id]	= self.Stream(stapModuleInstance)
			return self.streams[stapModuleInstance.id]
		else:
			self.log("stream for %s with id %d already present!" % (stapModuleInstance.name, stapModuleInstance.id))
			return None

	# register a stapLab-module for receiving the output of a systemtap-script
	def registerStapLabModule(self,stapLabModule,stapModuleInstance):
		try:
			if stapModuleInstance is not None and stapModuleInstance.id in self.streams:
				#self.log("registering stapLabModule %s to stapModule %s" % (stapLabModule,stapModuleInstance.name))
				self.streams[stapModuleInstance.id].register(stapLabModule)
			else:
				raise KeyError
		except KeyError:
			self.log("cannot register module %s to stream %s" %(stapModuleInstance,self.streams[stapModuleInstance.id]))
		



