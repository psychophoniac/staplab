import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from stapLabModule import stapLabModule
from queue import Queue
from threading import Thread
from time import sleep

class Stream():
		# TODO use Threads for output distribution
		def __init__(self,stapModuleInstance, args = {}, interval = 0.1, withdraw=False):
			self.id				= id(self)
			self.args			= args
			self.log			= print if 'logStream' not in args else args['logStream']
			self.name			= stapModuleInstance.name
			self.queue			= Queue()			# the input queue
			self.receivers			= []
			self.interval			= interval			# check every x seconds for output in queue.
			self.withdraw			= withdraw			# if True, drop incomming input if we have no listeners
			self.thread			= Thread(target=self.run)
			self.thread.daemon		= True
			self.thread.running		= True
			self.thread.start()
			stapModuleInstance.queue	= self.queue

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

		def unregister(self,module):
			if module is not None:
				try:
					self.receivers.remove(module)
					self.log("unregistered %s from %s" % (str(module), self.name))
				except ValueError:
					self.log("cannot unregister module %s to stream %s" %(module,self))

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

