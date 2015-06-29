import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from threading import Thread
from dispatcher import Dispatcher
import argparse
from time import sleep

class stapLab():
	def __init__(self):
		self.dispatcher		= Dispatcher()
		self.options		= self.parseargs()
		self.run()
		
	def log(self,logStr):
		print logStr

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
		print args
		return args

	def run(self):
		self.dispatcher.dispatchStapLabModuleAll(modules=self.options['modules'], target=self.options['target-pid'])		
		self.log("entering stapLab mainLoop")
		while True:
			try:
				# we do this so we can catch KeyboardInterrupts better
				for c in range(0,100):
					sleep(0.01)
			except KeyboardInterrupt:
				self.stop()
		self.log("leaving stapLab mainLoop")

	def stop(self):
		self.log("stapLab.stop()")
		self.dispatcher.stop()
		sys.exit(0)

if __name__ == "__main__":
	stapLab()
