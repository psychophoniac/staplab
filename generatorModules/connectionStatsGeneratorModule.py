from dataGeneratorModule import dataGeneratorModule
from threading import Thread
from time import sleep
from queue import Queue
import subprocess

# this module requires "ss" to be installed

class connectionStatsGeneratorModule(dataGeneratorModule):
	def __init__(self,name,queue=None,args={}):	# TODO: follow children
		self.args		= args
		self.log		= print if 'logStream' not in args else args['logStream']
		super(connectionStatsGeneratorModule,self).__init__(name,args)
		self.id			= id(self)
		self.name		= name if name is not None else self.__class__.__name__
		self.queue		= queue
		self.thread.start()

	def enqData(self,data):
		if isinstance(self.queue,Queue):
			self.queue.put(data)

	def run(self):
		self.log("module %s entering mainLoop" % str(self))
		while self.queue is None:
			sleep(0.1)
		while self.thread.running:
			dataLines	= subprocess.check_output(	['netstat','-autnp'],
									stderr	= subprocess.PIPE,
									universal_newlines=True
								).split("\n")[1:]
			#dataLines	= subprocess.check_output(
			#						['ss','-p', '--tcp', '--udp', '--numeric'],	# cmd
			#						shell=True,					# 
			#						universal_newlines=True				# 
			#					).split("\n")						# slice into lines
			dataSets	= list(map((lambda x: x.split()), dataLines[1:-1]))
			#dataIdxs	= data[0].split("\t")
			dataIdxs	= ['proto', 'recvq', 'sendq', 'localAddress', 'foreignAddress', 'state', 'prog']
			data		= [dataIdxs]
			for line in dataSets[1:]:
				dataSet		= line#.split()
				if dataSet[0] not in ['tcp','udp']:
					continue
				data	+= [dict(zip( dataIdxs, dataSet))]
			self.queue.put(data)
			sleep(0.5)

	def stop(self):
		self.log("stopping %s" % self)
		self.thread.running	= False
