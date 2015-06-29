import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from threading import Thread
from Queue import Queue
from time import sleep

#this is the base module for the stapLab Modules
class stapLabModuleSyscall():
	def __init__(self,name,queue):
		self.id			= id(self)
		self.name		= name
		self.queue		= queue
		self.requirements	= {"syscall":[]}	# {stapModuleName:[Args]}
		self.stats		= {}			# {syscall:count}
		self.thread		= Thread(target=self.run)
		self.thread.daemon	= True
		self.thread.running	= True
		self.thread.start()

	def __str__(self):
		return "<%s(id:%d), queue=%s,req=%s>" % (self.name,self.id,str(self.queue),str(self.requirements))

	def log(self,logStr):
		print logStr
		
	def enqData(self,data):
		if self.queue is not None:
			self.queue.put(data)

	def getRequirements(self):
		return self.requirements

	def run(self):
		self.log("module %s entering mainLoop" % self)
		while self.thread.running:
			if self.queue is not None:
				while not self.queue.empty():
					data	= self.queue.get()
					func	= data.split()[1]
					if not self.stats.has_key(func):
						self.stats[func]	= 0
					self.stats[func]	+=1
					#print "%s|%s" %(self.name,data)
			sleep(0.1)
			#self.log("syscall stats:\n%s" % str(self.stats))
		self.log("module %s leaving mainLoop" % self)

	def stop(self):
		self.log("stopping %s" % self)
		self.log("syscall stats:\n%s" % str(self.stats))
		self.thread.running	= False
