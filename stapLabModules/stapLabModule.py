import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from threading import Thread
from queue import Queue
from time import sleep

#this is the base module for the stapLab Modules
class stapLabModule():
	def __init__(self,name,queue,args={}):
		self.id			= id(self)
		self.log		= print if 'logStream' not in args else args['logStream']
		self.name		= name
		self.queue		= queue
		self.stapRequirements	= {}	# {stapModuleName:[Args]}
		self.refRequirements	= []
		self.thread		= Thread(target=self.run)
		self.thread.daemon	= True
		self.thread.running	= True
		self.thread.start()

	def __str__(self):
		return "<%s(id:%d), queue=%s,req= %s %s>" % (self.name,self.id,str(self.queue),str(self.stapRequirements),str(self.refRequirements))
		
	def enqData(self,data):
		if self.queue is not None:
			self.queue.put(data)

	def run(self):
		self.log("module %s entering mainLoop" % self)
		while self.thread.running:
			print("stapLabModule running")
			sleep(1)
		self.log("module %s leaving mainLoop" % self)

	def stop(self):
		#self.log("stopping %s" % self)
		self.thread.running	= False
