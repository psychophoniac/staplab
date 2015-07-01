import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from threading import Thread
from queue import Queue
from time import sleep
import numpy as np
#import matplotlib.pyplot as plt
import pylab as pl
import random

#this is the base module for the stapLab Modules
class stapLabModulePlot():
	def __init__(self,name,queue,logStream=print):
		self.id			= id(self)
		self.log		= logStream
		self.name		= name
		self.queue		= queue
		self.stapRequirements	= {	# {
						#	"stapModuleName":["Args"] 	<-- stapModules to start and connect with this stapLabModule
						# }
						"dummy":[]	# for testing
					}
		self.refRequirements	= [	# [
						# 	"reference"			<-- internal Objects that need to be handed to this Module
						# ]
				#		'plt'		# plt is the plot instance that we get our figure Object from
					]
		self.thread		= Thread(target=self.run)
		self.thread.daemon	= True
		self.thread.running	= True
#		self.guiInitialized	= False
		self.thread.start()

	def __str__(self):
		return "<%s(id:%d), queue=%s,req= %s %s>" % (self.name,self.id,str(self.queue),str(self.stapRequirements),str(self.refRequirements))

	def setReferences(self,refDict):
		self.plt	= refDict['plt']
		
	def enqData(self,data):
		if self.queue is not None:
			self.queue.put(data)

	def getStapRequirements(self):
		return self.stapRequirements
	
	def getRefRequirements(self):
		return self.refRequirements

	def initGUI(self):
		self.log("initGUI()")

	# this function is to be overridden by derived classes that plot stuff. The drawing logic is to be inserted here.
	def plot(self):
		self.log("plot")

	# this function is to be overridden by derived classes and is set to contain the data handling logic.
	def processData(self,data):
		self.log("processData")

	def drawGUI(self):
		# wait until all refRequirements are passed to this module
		while False in list(map((lambda x: hasattr(self,x)), self.refRequirements)):
			sleep(0.1)
		self.initGUI()
		while self.windowThread.running:
			self.plot()
			sleep(1)

	def run(self):
		self.log("module %s entering mainLoop" % self)
		self.windowThread		= Thread(target=self.drawGUI)
		self.windowThread.daemon	= True
		self.windowThread.running	= True
		self.windowThread.start()
		while self.thread.running:
			if self.queue is not None:
				while not self.queue.empty():
					data	= self.queue.get()
					self.processData(data)
					#self.drawGUI()
			sleep(0.1)
		self.log("module %s leaving mainLoop" % self)

	# this function is to be overridden by deriving classes and is called once the mainloop stopped.
	def onStop(self):
		pass

	def stop(self):
		self.log("stopping %s" % self)
		if hasattr(self,"onStop"):
			self.onStop()
		self.windowThread.running	= False
		self.thread.running		= False


