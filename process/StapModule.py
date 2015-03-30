from threading import Thread
from Queue import Queue, Empty
from time import sleep
import sys
import subprocess
import OutputModule as outmod
newlines = ['\n', '\r\n', '\r']

class StapModule():
	
	def __init__(self,stapFile,stapArgs,targetPID,mid=-1,mname="",logMessages=True,outStream=outmod.gos,logStream=outmod.gls):
		self.om = outStream
		self.lm = logStream
		self.mid	= mid if mid >= 0 else id(self)	# id for this module
		self.mname	= mname				# name for this module
		self.logmsg	= logMessages			# turn on log messages
		#self.log("init")
		self.t		= Thread(target=self.run)	# thread for reading Output
		self.t.daemon 	= True				# put to Background, die with parent 
		self.running 	= False				# start/stop indicator
		self.q 		= Queue()			# output Queue
		self.ph 	= -1 				# subprocess handle
		self.sfile	= stapFile			# stapFile (path)
		self.sargs	= stapArgs			# stapArgs (list)
		self.stpid	= targetPID			# stapScript target PID

	def enqueueOutput(self):
		while self.ph.poll() is not None:
			sleep(1)
		#self.log("enq")
		for line in iter(self.ph.stdout.readline, b''):
			self.out(line.rstrip())
		self.ph.stdout.close()
		#self.log("enq end")

	def dispatchSubprocess(self):
		cmd = [
			'stap', 				# stap bin
			'-s 16', 				# max kernel buffer for stap <-> user com
			'-DMAXSTRINGLEN=16384',			# max String length
			self.sfile				# stap script for module
		]
		cmd += self.sargs
		if self.stpid > 0:
			cmd += ['-x', str(self.stpid)]		# stap target PID
			self.log("dispatch command: %s" % cmd)
			self.ph = subprocess.Popen(
				cmd,
				stdout=subprocess.PIPE,
				stderr=subprocess.STDOUT,	# pipe errors to stdout
				universal_newlines=True
			)			
			return self.ph.pid			# return pid of subprocess
		else:
			return -1

	def log(self,message):
		if self.logmsg:
			outData = (outmod.timestamp(),self.mname,self.mid,message)
			if self.lm is not None:
				self.lm.enqLog(outData)
			else:
				#print("log:[%s][%s|%d]%s" % outData)
				print "logstream missing"
	
	def out(self,data):
		outData = (outmod.timestamp(), self.mname, self.mid, data)
		if self.om is not None:
			self.om.enq(outData)
		else:
			#print("[%s][%s|%s]%s" % outData)
			print "outstream missing"

	def start(self):
		pid = self.dispatchSubprocess()		# async from here on
		self.log("pid:%d" % pid)
		self.running = True
		self.t.start()				# implies run()
		self.log("start")

	def stop(self):
		self.log("stop queue thread")
		self.running = False
		self.log("stopping stap subprocess")
		self.ph.terminate()
		sleep(1)
		if self.ph.poll() is None:
			self.log("killing stap subprocess")
			self.ph.kill()

	def run(self):
		#self.log("run")
		tr = Thread(target=self.enqueueOutput)
		tr.daemon = True
		tr.start()
		while self.running:
			#self.log("running")
			sleep(1)


if __name__ == "__main__":
	om = outmod.StdoutOutputModule()
	s = StapModule("gather/udp.stp",[],sys.argv[1],1,"udp",logStream=om,outStream=om)
	s.start()
	while True:
		try:
			sleep(1)
		except KeyboardInterrupt:
			s.stop()
			sys.exit(0)


