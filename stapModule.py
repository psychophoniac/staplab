import subprocess
from threading import Thread
from time import sleep

class stapModule():
		def __init__(self,name,script,target,args,queue,followChildren = True,logStream=print):
			self.id			= id(self)
			self.log		= logStream
			self.name		= name
			self.queue		= queue
			self.handle		= None
			self.script		= script
			self.target		= target
			self.args		= args
			self.followChildren	= followChildren
			self.thread		= Thread(target=self.outputWorkerMain)
			self.thread.daemon	= True
			self.thread.running	= True
			self.thread.start()

		def __str__(self):
			return "<stapModule %s(id:%d), queue=%s, handle=%s>" % (self.name,self.id,str(self.queue),str(self.handle))

		def outputWorkerMain(self):
			#self.log("outputWorker for stapModule %s started" % self.name)
			while self.thread.running:
				if self.handle is not None:
					while self.handle.poll() is not None:
						sleep(0.01)
					for line in iter(self.handle.stdout.readline, b''):
						if self.queue is not None:	# we can have a stapModule without an currently valid queue
							self.queue.put(line.rstrip())
					self.handle.stdout.close()
			#self.log("outputWorker for stapModule %s stopped" % self.name)

		def run(self):
			cmd 			= [
							'stap', 				# stap bin
							'-s 16', 				# max kernel buffer for stap <-> user com
							'-DMAXSTRINGLEN=16384',			# max String length
							self.script					# stap script for module
						]
			if self.followChildren:
				cmd		+= '-DtrackChildren=1'
			else:
				cmd		+= '-DtrackChildren=0'
			cmd 			+= self.args
			cmd 			+= ['-x', str(self.target)]				# stap target PID
			self.log("dispatch command: %s" % cmd)
			self.handle		 = subprocess.Popen(
							cmd,
							stdout=subprocess.PIPE,
							stderr=subprocess.STDOUT,	# pipe errors to stdout
							universal_newlines=True
						)
			self.log("handle: %s" % str(self.handle))

		def stop(self):
			self.log("stopping %s" % self)
			self.handle.terminate()	#TODO check if really terminated
			self.thread.running	= False
