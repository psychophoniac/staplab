from threading import Thread
from time import sleep
from queue import Queue

# Wrapper class for generator Modules, like data Playback or net statistics
class dataGeneratorModule():
	def __init__(self,name,args=[],queue=None,logStream=print):	# TODO: follow children
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
		return "<%s(id:%d), queue=%s, args=%s>" % (self.name,self.id,str(self.queue), str(self.args))

	def run(self):
		while self.thread.running:
			#data	= subprocess.check_output(['netstat','-autn'],universal_newlines=True)
			#data	= data.split()
			if isinstance(self.queue,Queue):
				self.queue.put("testData")
			sleep(1)

	def stop(self):
		#self.log("stopping %s" % self)
		self.thread.running	= False
