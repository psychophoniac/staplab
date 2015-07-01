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
						'plt'		# plt is the plot instance that we get our figure Object from
					]
		self.thread		= Thread(target=self.run)
		self.thread.daemon	= True
		self.thread.running	= True
		self.guiInitialized	= False
		self.thread.start()

	def __str__(self):
		return "<%s(id:%d), queue=%s,req= %s %s>" % (self.name,self.id,str(self.queue),str(self.stapRequirements),str(self.refRequirements))

	#def log(self,logStr):
	#	print logStr

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
		self.fig 	= pl.figure()
		def onresize(event):
			self.log("onResize")
			width 		= event.width
			scale_factor 	= 100.0
			data_range 	= width/scale_factor
			start, end 	= self.plt.xlim()
			new_end 	= start+data_range
			self.plt.xlim((start, new_end))

		def onClose(event):
			self.log("onClose")
			self.stop()

		cid 		= self.fig.canvas.mpl_connect('resize_event', onresize)
		#TODO connect closing event to self.stop()
		cid2		= self.fig.canvas.mpl_connect('close_event', onClose)

		self.log("show graph Window")
		#self.plt.ion()
		self.plt.show(block=False)
		self.log("grap worker initialized")
		self.guiInitialized	= True

	def drawGUI(self):
		if not self.guiInitialized and hasattr(self,'plt'):
			self.initGUI()
	
		try:
			while self.windowThread.running:
				self.fig.clf()
				a		= range(0,100)
				b		= random.sample(a,len(a))
				self.fig.canvas.stop_event_loop()
				# plot stuff
				self.plt.plot(a,b)
				self.fig.canvas.start_event_loop(timeout=1)
				self.plt.draw()
				sleep(1)
		except:
			self.log("drawGUI() error")
			if self.thread.running:
				self.stop()
				#raise

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
					self.log("%s|%s" % (self.name,data))
					#self.drawGUI()
			sleep(0.1)
		self.log("module %s leaving mainLoop" % self)

	def stop(self):
		self.log("stopping %s" % self)
		self.windowThread.running	= False
		self.thread.running		= False


