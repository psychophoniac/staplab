import StapModule as stpmod
import OutputModule as outmod
import sys
import os
from time import sleep

stapModules = {
			'dummy':['gather/dummy.stp'],
			'udp':['gather/udp.stp'],
			'tcp':['gather/tcp.stp'],
			'socket':['gather/socket.stp','-g','-GprintRawData=0','-GprintSendRecv=1','-GprintOpenClose=1'],
			'syscall':['gather/syscall.stp','-Gprint_time_spent=1','-GprintData=1']
		}

class StapModuleHandler:
	def __init__(self,outputStream=outmod.gos,logStream=outmod.gls,enableLogging=True):
		self.dm 	= {}					# dispatched modules
		self.idc	= 0
		self.om = outputStream
		self.lm = logStream
		self.mid	= id(self)
		self.logging	= enableLogging
		self.log("StapModuleHandler initialized")

	def checkTargetPID(self,tid=-1):
		if isinstance(tid,str):
			tid=int(tid)
		self.max_pid_file = "/proc/sys/kernel/pid_max"
		self.maxPID = int(open(self.max_pid_file).read().replace('\n',''))
		result = tid in range(1,self.maxPID)
		try:
			os.kill(tid, 0)
			result &= True
		except OSError:
			result &= False
		return result

	def getModuleID(self):
		self.idc += 1
		return self.idc	

	def log(self,message):
		if self.logging:
			if self.lm is not None:
				#self.lm.outLog(outmod.makeOutstreamTuple(self,message))
				self.lm.enqLog(outmod.makeOutstreamTuple(self,message))
			else:
				print outmod.makeLogStr(outmod.makeOutstreamTuple(self,message))

	# moduleName, Arguments[], targetPID, outStream, LogStream
	def startModule(self, module="invalid", args=[], target=-1, outStream=None, logStream=None):
		if outStream is None:
			outStream = self.om
		if logStream is None:
			logStream = self.lm
		if module in stapModules and self.checkTargetPID(target):
			#moduleID = self.getModuleID()
			moduleID = -1	# is set directly in the module via the python-built-in id() function now
			aargs = stapModules[module][1:] + args
			sm = stpmod.StapModule(	stapModules[module][0],	# file with the stapscript
						aargs,				# stapscript and additional stap args 
						target,				# targetPID
						moduleID,			# the moduleID
						module,				# the moduleName
						outStream=outStream,		# set outputStream
						logStream=logStream
					)
			sm.start()
			self.log("started Module %s and ID:%d" % (module,sm.mid))
			self.dm[sm.mid] = sm
			return sm.mid if sm is not None else -1
		else:
			self.log("failed starting Module %s" % module)
			return -1
	
	def stopModule(self,moduleID):
		if moduleID in self.dm:
			self.dm[moduleID].stop()
			self.log("stopped Module with ID:%d name:%s" % (moduleID,self.dm[moduleID].mname))
			del self.dm[moduleID]
			return True
		else:
			self.log("failed stopping Module with ID:%d name:%s" % (moduleID,self.dm[moduleID]))
			return False

	def stopAllModules(self):
		succ = True
		for mid in self.dm.items():
			succ = succ and self.stopModule(mid[0])
		return succ
	
	def getModuleList(self):
		return self.dm.items()

	def getModuleDict(self):
		return self.dm

	def closeAllStreams(self):
		if self.om is not None:
			self.om.close()
		if self.lm is not None:
			self.lm.close()

	def close(self):
		self.log("closing all modules")
		self.stopAllModules()
		self.log("closing all streams")
		self.closeAllStreams()

if __name__ == "__main__":
	ls = outmod.gls
	#os = outmod.DatabaseOutputModule("testdb")
	#os = outmod.gos
	outstream = outmod.StdoutOutputModule()
	smh = StapModuleHandler(outputStream=outstream,logStream=ls)

	try:

		mID = smh.startModule("udp",[],sys.argv[1])
		sleep(5)
		smh.stopModule(mID)
		sleep(1)

		mID = smh.startModule("syscall",[],sys.argv[1])
		sleep(5)
		smh.stopModule(mID)
		sleep(1)
		
		mID = smh.startModule("syscall",[],sys.argv[1])
		mID2 = smh.startModule("udp",[],sys.argv[1])

		sleep(5)
		smh.stopModule(mID)
		smh.stopModule(mID2)
		sleep(1)

		mID = smh.startModule("socket",[],sys.argv[1])

		sleep(5)
		
		smh.close()

		#raise SystemExit

	except KeyboardInterrupt, SystemExit:
		sys.exit(-1)
	sys.exit(0)

