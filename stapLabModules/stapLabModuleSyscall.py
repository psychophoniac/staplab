import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from threading import Thread
from queue import Queue
from time import sleep

#this is the base module for the stapLab Modules
class stapLabModuleSyscall():
	def __init__(self,name,queue,logStream=print):
		self.id			= id(self)
		self.log		= logStream
		self.name		= name
		self.queue		= queue
		self.stapRequirements	= {"syscall":[]}	# {stapModuleName:[Args]}
		self.refRequirements	= ['plt','pl']
		self.stats		= {}			# {syscall:count}
		self.thread		= Thread(target=self.run)
		self.thread.daemon	= True
		self.thread.running	= True
		self.thread.start()

	def __str__(self):
		return "<%s(id:%d), queue=%s,req= %s %s>" % (self.name,self.id,str(self.queue),str(self.stapRequirements),str(self.refRequirements))

	#def log(self,logStr):
		#print logStr
	#	self.logStream(logStr)
		
	def enqData(self,data):
		if self.queue is not None:
			self.queue.put(data)

	def setReferences(self,refDict):
		#TODO automatize this?
		self.plt	= refDict['plt']
		self.pl		= refDict['pl']

	def initGUI(self):
		self.fig 	= pl.figure()
		
		def onresize(event):
			width 		= event.width
			scale_factor 	= 100.0
			data_range 	= width/scale_factor
			start, end 	= self.plt.xlim()
			new_end 	= start+data_range
			self.plt.xlim((start, new_end))
		cid 		= self.fig.canvas.mpl_connect('resize_event', onresize)

		self.log("show graph Window")
		self.plt.ion()
		self.plt.show(block=False)
		self.log("grap worker initialized")		

	def drawGUI(self):
		if not self.guiInitialized and hasattr(self,'plt'):
			self.fig 	= pl.figure()
			def onresize(event):
				width 		= event.width
				scale_factor 	= 100.0
				data_range 	= width/scale_factor
				start, end 	= self.plt.xlim()
				new_end 	= start+data_range
				self.plt.xlim((start, new_end))
			cid 		= self.fig.canvas.mpl_connect('resize_event', onresize)

			self.log("show graph Window")
			self.plt.ion()
			self.plt.show(block=False)
			self.log("grap worker initialized")
			self.guiInitialized	= True
	
		try:
			if self.thread.running:
				self.fig.clf()
				a		= range(0,100)
				b		= random.sample(a,len(a))
				self.fig.canvas.stop_event_loop()
				# plot stuff
				self.plt.plot(a,b)
				self.fig.canvas.start_event_loop(timeout=1)
				self.plt.draw()
		except:
			self.log("drawGUI() error")
			if self.thread.running:
				self.stop()
				#raise

	def run(self):
		self.log("module %s entering mainLoop" % self)
		while self.thread.running:
			if self.queue is not None:
				while not self.queue.empty():
					data	= self.queue.get()
					print "%s|%s" % (self.name,data)
					self.drawGUI()
			sleep(0.1)
		self.log("module %s leaving mainLoop" % self)

	def stop(self):
		self.log("stopping %s" % self)
		self.log("syscall stats:\n%s" % str(self.stats))
		self.thread.running	= False
