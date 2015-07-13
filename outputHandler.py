import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from stapLabModule import stapLabModule
from stream import Stream
from queue import Queue
from threading import Thread
from time import sleep

class outputHandler():

	def __init__(self,args):
		self.log		= print if 'logStream' not in args else args['logStream']
		self.streams		= {}	# {stapModule.id:<Stream>}
		self.args		= args

	# register a systemtap-skript for output
	# returns the Queue
	def registerStapModule(self,stapModuleInstance):
		self.log("registering %s" % stapModuleInstance.name)
		if not stapModuleInstance.id in self.streams:
			self.streams[stapModuleInstance.id]	= Stream(stapModuleInstance,args = self.args)
			return self.streams[stapModuleInstance.id]
		else:
			self.log("stream for %s with id %d already present!" % (stapModuleInstance.name, stapModuleInstance.id))
			return None

	def registerDataGenerator(self,dataGeneratorInstance):
		if not dataGeneratorInstance.id in self.streams:
			self.streams[dataGeneratorInstance.id]	= Stream(dataGeneratorInstance, args = self.args)
			return self.streams[dataGeneratorInstance.id]
		else:
			self.log("stream for %s with id %d already present!" % (dataGeneratorInstance.name, dataGeneratorInstance.id))
			return None

	# register a stapLab-module for receiving the output of a systemtap-script
	def registerStapLabModule(self,stapLabModule,stapModuleInstance):
		try:
			if stapModuleInstance is not None and stapModuleInstance.id in self.streams:
				self.log("registering stapLabModule %s to stapModule %s" % (stapLabModule,stapModuleInstance.name))
				self.streams[stapModuleInstance.id].register(stapLabModule)
			else:
				raise KeyError
		except KeyError:
			self.log("cannot register module %s to stream %s" %(stapModuleInstance,self.streams[stapModuleInstance.id]))
		



