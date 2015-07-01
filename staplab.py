#from __future__ import print_function
import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from threading import Thread
from dispatcher import Dispatcher
import argparse
from time import sleep
import matplotlib.pyplot as plt
import pylab as pl

class stapLab():
	def __init__(self,logStream=print):
		self.log		= logStream
		self.dispatcher		= Dispatcher(references={'plt':plt,'pl':pl},logStream=logStream)
		self.options		= self.parseargs()
		#print(self.log)
		self.start()
		
	#def log(self,logStr):
		#print logStr
	#	self.logStream(logStr)

	def parseargs(self):
		# parse args
		#TODO:
		# subargument structure so we can set individual options to each module, e.g.:
		# stapLab tid moduleA optionA1 optionB1 moduleB optionA2 optionB2
		# stapLab [-f] tid [module [option]]
		parser = argparse.ArgumentParser(description='staplab - systemtap module dispatcher and data visualizer')
		parser.add_argument('target-pid', type=int, metavar="target_pid",
					help='target process ID. Must be greater than zero.')
		parser.add_argument('modules', type=str, nargs="+", metavar="module",default=['dummy'], 
					help='module to be dispatched')
		parser.add_argument('-f','--follow-children', action='store_true',
					help='if a process forks, include children to the tapset')

		args = vars(parser.parse_args())
		self.log(args)
		return args

	def start(self):
		self.dispatcher.dispatchStapLabModuleAll(modules=self.options['modules'], target=self.options['target-pid'])
		#plt.show(block=False)
		self.log("entering stapLab mainLoop")
		
		# wait for dispatcher to launch at least one module
		while self.dispatcher.stapLabModules == 0:
			sleep(1)
		# now run until we have no modules left to process
		while len(self.dispatcher.stapLabModules) > 0:
			try:
				# we do this so we can catch KeyboardInterrupts better
				#plt.draw()
				sleep(1.0)
			except KeyboardInterrupt:
				self.stop()
				return
			except:
				self.log("error in stapLab mainLoop")
				raise
		self.log("leaving stapLab mainLoop")

	def stop(self):
		self.log("stapLab.stop()")
		self.dispatcher.stop()
		sys.exit(0)

if __name__ == "__main__":
	stapLab()
