#! /usr/bin/python3
#from __future__ import print_function
import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from threading import Thread
from dispatcher import Dispatcher
import argparse
from time import sleep
#import matplotlib.pyplot as plt
import pylab as pl

class stapLab():
	def __init__(self,
				logStream	= (lambda _: None)
		):
		self.log		= logStream
		self.options		= self.parseargs()
		if self.options['verbose']:
			self.log	= print
		self.dispatcher		= Dispatcher(	registerCallbackFunc	= self.registerGUIcallback,
							args			= {
											'target-pid' 	: self.options['target-pid'],	
											'logStream'	: self.log,
											'hardFail'	: True
										}
						)
		self.timers		= []
		self.start()

	def parseargs(self):
		# parse args
		#TODO:
		# subargument structure so we can set individual options to each module, e.g.:
		# stapLab tid moduleA optionA1 optionB1 moduleB optionA2 optionB2
		# stapLab [-f] tid [module [option]]
		# -> Theoretically this could also be done by just simply copying an existing module and quickly modifiying the sourcecode
		# the advantage of this would be that we keep program complexity lower and it is more powerful to do it in code, 
		# compared to using switches and the cli parameters.
		parser = argparse.ArgumentParser(description='staplab - systemtap module dispatcher and data visualizer')
		parser.add_argument('target-pid', type=int, metavar="target_pid",
					help='target process ID. Must be greater than zero.')
		parser.add_argument('modules', type=str, nargs="+", metavar="module",default=['dummy'], 
					help='module to be dispatched')
		parser.add_argument('-f','--follow-children', action='store_true',
					help='if a process forks, include children to the tapset')
		parser.add_argument('-d','--hardFail', action='store_true',
					help='fail hard if Module cannot be loaded, i.e. quit and don\'t continue loading other modules')
		parser.add_argument('-v','--verbose', action='store_true',
					help='be verbose about what is going on internally')

		args = vars(parser.parse_args())
		self.log(args)
		return args

	def registerGUIcallback(self,func,timerInterval=20):
		fig	= pl.figure()
		self.log("set timer for %s" % str(func))
		def guiCallBack(func,figure):
			try:
				func(figure)
				#manager = pl.get_current_fig_manager()
				#manager.canvas.draw()
			except KeyboardInterrupt:
				self.stop()
		timer	= fig.canvas.new_timer(interval = timerInterval)
		timer.add_callback(guiCallBack,func,fig)
		timer.start()
		self.timers	+= [timer]

	def start(self):
		self.dispatcher.dispatchStapLabModuleAll(modules=self.options['modules'], target=self.options['target-pid'])
		self.log("entering stapLab mainLoop")
		
		# wait for dispatcher to launch at least one module
		while self.dispatcher.stapLabModules == 0:
			sleep(1)
		
		# now run until we have no modules left to process
		while len(self.dispatcher.stapLabModules) > 0:
			try:
				# we do this so we can catch KeyboardInterrupts better
				pl.show()
				sleep(0.1)
			except KeyboardInterrupt:
				self.stop()
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
	sys.exit(0)


