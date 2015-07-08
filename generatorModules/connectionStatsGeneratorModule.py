from dataGeneratorModule import dataGeneratorModule
from threading import Thread
from time import sleep
import subprocess

class connectionStatsGeneratorModule(dataGeneratorModule):
	def __init__(self,name,args=[],queue=None,logStream=print):	# TODO: follow children
		super(connectionStatsGeneratorModule,self).__init__(name)
		self.id			= id(self)
		self.log		= logStream
		self.name		= name if name is not None else self.__class__.__name__
		self.queue		= queue
		self.args		= args
		self.thread		= Thread(target=self.run)
		self.thread.daemon	= True
		self.thread.running	= True
		self.thread.start()

	def __str__(self):
		return "<%s(id:%d), queue=%s>" % (self.name,self.id,str(self.queue))

	def enqData(self,data):
		if self.queue is not None:
			self.queue.put(data)

	def run(self):
		while self.queue is None:
			sleep(0.1)
		while self.thread.running:
			data	= subprocess.check_output(['netstat','-autn'],universal_newlines=True)
			data	= data.split()
			self.queue.put(str(data))
			sleep(1)

	def stop(self):
		#self.log("stopping %s" % self)
		self.thread.running	= False
