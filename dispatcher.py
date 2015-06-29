import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
import os
import glob
from outputHandler import outputHandler
import subprocess
from threading import Thread
from time import sleep

class Dispatcher():

	class stapModule():
		def __init__(self,name,script,target,args,queue):	# TODO: follow children
			self.id			= id(self)
			self.name		= name
			self.queue		= queue
			self.handle		= None
			self.script		= script
			self.target		= target
			self.args		= args
			self.thread		= Thread(target=self.outputWorkerMain)
			self.thread.daemon	= True
			self.thread.running	= True
			self.thread.start()
	
		def log(self,logStr):
			print logStr

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
			cmd 	= [
					'stap', 				# stap bin
					'-s 16', 				# max kernel buffer for stap <-> user com
					'-DMAXSTRINGLEN=16384',			# max String length
					self.script					# stap script for module
				]
			cmd 	+= self.args
			cmd 	+= ['-x', str(self.target)]				# stap target PID
			#self.log("dispatch command: %s" % cmd)
			self.handle		 = subprocess.Popen(
							cmd,
							stdout=subprocess.PIPE,
							stderr=subprocess.STDOUT,	# pipe errors to stdout
							universal_newlines=True
						)
			#self.log("handle: %s" % str(self.handle))

		def stop(self):
			#self.log("stopping %s" % self)
			self.handle.terminate()	#TODO check if really terminated
			self.thread.running	= False
	
	def __init__(self,stapLabModulesDir="stapLabModules",stapModulesDir="gather"):
		self.stapLabModulesDir	= stapLabModulesDir
		self.stapModulesDir	= stapModulesDir
		self.stapLabModules	= {}	# {stapLabModule.id:stapLabModule}
		self.stapModules	= {}	# {stapModule.id:stapModule}
		self.outputHandler	= outputHandler()
	
	def log(self,logStr):
		print logStr

	def dispatchStapLabModule(self,module,target=-1):
		self.log("dispatching module %s" % module)
		workdir		= os.path.dirname(os.path.realpath(__file__))
		filename	= (workdir + "/" + self.stapLabModulesDir + "/" + module + ".py")

		if os.path.exists(filename):
			pass
			#self.log("found: %s" % filename)
		else:
			self.log("not found: %s" % filename)
			return None
		
		# create instance of the module by importing the class and creating an instance
		pymod			= __import__(module)
		stapLabModuleInstance	= getattr(pymod, module)(name=module,queue=None)
		if stapLabModuleInstance is not None:
			#self.log("instance of module %s(%s) created. Handle requirements." % (module,stapLabModuleInstance))
			requirements	= stapLabModuleInstance.getRequirements()		# load lists of stapModules we need to dispatch
			#self.log("module %s requirements: %s" % (module,requirements))
			for requirement in requirements:
				args		= requirements[requirement]
				stapModule	= self.dispatchStapModule(name=requirement,args=args,target=target)
				self.outputHandler.registerStapLabModule(stapLabModuleInstance,stapModule)
			self.stapLabModules[stapLabModuleInstance.id]	= stapLabModuleInstance
			#self.log("handling requirements for %s successfull!" % stapLabModuleInstance)
		else:
			self.log("instanciating module %s failed!" % module)

	def dispatchStapModule(self,name,args=[],target=-1):
		self.log("dispatching stapModule %s" % name)	
		workdir		= os.path.dirname(os.path.realpath(__file__))
		filename	= (workdir + "/" + self.stapModulesDir + "/" + name + ".stp")
		
		if os.path.exists(filename):
			pass
			#self.log("found: %s" % filename)
		else:
			self.log("not found: %s" % filename)
			return None

		#self.log("dispatching stapScript %s with script %s" %(name,filename))

		stapModuleInstance	= self.stapModule(name,filename,target,args=args,queue=None)	# name, script, target, args, queue
		if stapModuleInstance is not None:
			self.outputHandler.registerStapModule(stapModuleInstance)
			stapModuleInstance.run()
			self.stapModules[stapModuleInstance.id]	= stapModuleInstance
			#self.log("dispatched stapModule %s with script %s" %(stapModuleInstance,filename))
			return stapModuleInstance
		else:
			self.log("could not dispatch stapModule %s with script %s" %(stapModuleInstance,filename))
			return None
		

	def dispatchStapLabModuleAll(self,modules):
		for module in modules:
			self.dispatchStapLabModule(module)

	def run(self):
		while True:
			sleep(1)

	def stop(self):
		for slm in self.stapLabModules:
			try:
				self.stapLabModules[slm].stop()
			except OSError:
				pass
		for sm in self.stapModules:
			try:
				self.stapModules[sm].stop()
			except OSError:
				pass

if __name__ == "__main__":
	try:
		d = Dispatcher()
		d.dispatchStapLabModule("stapLabModule")
		d.run()
	except KeyboardInterrupt:
		d.stop()

	sys.exit(0)