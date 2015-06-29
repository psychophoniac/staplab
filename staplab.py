import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from threading import Thread
from Dispatcher import Dispatcher

class staplab():
	def __init__(self):
		self.t		= Thread(target=self.run)
		self.t.daemon	= True
		self.t.running	= True
		self.running	= True
		
		self.dispatcher	= Dispatcher()
		self.options	= self.parseargs()
		self.dispatcher.dispatchAll(self.options['modules'])
		
		self.t.run()
		
	def log(self,logStr):
		print logStr

	def parseargs(self):
		options		= {}
		# parse args

		# parse Modules to be dispatched
		options['modules']	= []	# modules to be dispatched
		pass

	def run(self):
		self.log("entering stapLab mainLoop")
		while self.running:
			pass
		self.log("entering stapLab mainLoop")

	def stop(self):
		self.log("stapLab.stop()")
		self.running	= False
		self.t.running	= False
		


if __name__ == "__main__":
	stapLab().run()

	sys.exit(0)
