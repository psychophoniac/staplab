from threading import Thread
from time import sleep
from queue import Queue

# Wrapper class for generator Modules, like data Playback or net statistics
class dataGeneratorModule():
	def __init__(self,name,args={},queue=None):	# TODO: follow children
		self.id			= id(self)
		self.args		= args
		self.log		= print if 'logStream' not in args else args['logStream']
		self.name		= name if name is not None else self.__class__.__name__
		self.queue		= queue		
		self.thread		= Thread(target=self.run)
		self.thread.daemon	= True
		self.thread.running	= True
		#self.thread.start()

	def __str__(self):
		return "<%s(id:%d), queue=%s, args=%s>" % (self.name,self.id,str(self.queue), str(self.args))

	def run(self):
		while self.thread.running:
			if isinstance(self.queue,Queue):
				self.queue.put("testData")
			sleep(1)

	def stop(self):
		self.log("stopping module %s" % self)
		self.thread.running	= False
