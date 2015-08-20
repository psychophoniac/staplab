import sys
for folder in ["gather", "stapLabModules","generatorModules"]:
	sys.path.append(folder)
import os
#import glob
from outputHandler import outputHandler
# TODO:
# make the generator Modules and the stapModules abstract enough,
# so that we can just load the classes, instantiate them and let them run
from stapModule import stapModule
from threading import Thread
from time import sleep

# TODO:
# make this document more readable

class Dispatcher():	
	def __init__(self,
				registerCallbackFunc,
				args			= {},
				stapLabModulesDir 	= "stapLabModules",
				stapModulesDir 		= "gather",
				generatorModulesDir 	= "generatorModules"
		):
		self.log			= print if 'logStream' not in args else args['logStream']
		self.registerCallback		= registerCallbackFunc
		self.stapLabModulesDir		= stapLabModulesDir
		self.stapModulesDir		= stapModulesDir
		self.generatorModulesDir	= generatorModulesDir
		self.stapLabModules		= {}			# {stapLabModule.id:stapLabModule}
		self.stapModules		= {}			# {stapModule.id:stapModule}
		self.generatorModules		= {}
		self.args			= args
		self.outputHandler		= outputHandler(args=self.args)
		self.thread			= Thread(target=self.run)
		self.thread.daemon		= True
		self.thread.running		= True
		self.thread.start()

	def dispatchStapLabModule(self,module,target):
		stapLabModuleInstance	= self.instanciateModule(
									moduleName	= module,
									modDir		= self.stapLabModulesDir,
									modArgs		= self.args
									#[module,[],None]
								)
		if stapLabModuleInstance is not None:
			self.log("instance of module %s(%s) created. Handle requirements." % (module,stapLabModuleInstance))

			requirements		= stapLabModuleInstance.stapRequirements	# load dict of stapModules we need to dispatch
			callbackRequirements	= stapLabModuleInstance.callbackRequirements
			generatorRequirements	= []
			if hasattr(stapLabModuleInstance,'generatorRequirements'):
				generatorRequirements	= stapLabModuleInstance.generatorRequirements

			self.log("module %s requirements: %s" % (module,requirements))
			for requirement in requirements:
				args		= requirements[requirement]
				stapModule	= self.dispatchStapModule(	
										name=requirement,
										args=args,
										target=target
									)
				self.outputHandler.registerStapLabModule(stapLabModuleInstance,stapModule)

			if len(callbackRequirements) > 0:
				for func, timer in callbackRequirements:
					self.registerCallback(func,timer)

			if len(generatorRequirements) > 0:
				for genReqMod in generatorRequirements:
					stream	= self.dispatchGeneratorModule(genReqMod)
					stream.register(stapLabModuleInstance)
			
			self.stapLabModules[stapLabModuleInstance.id]	= stapLabModuleInstance
			self.log("handling requirements for %s successfull!" % stapLabModuleInstance)
			return stapLabModuleInstance
		else:
			return None
			self.log("instanciating module %s failed!" % module)

	def dispatchStapModule(self,name,target,args=[]):
		self.log("dispatching stapModule %s" % name)	
		workdir		= os.path.dirname(os.path.realpath(__file__))
		filename	= (workdir + "/" + self.stapModulesDir + "/" + name + ".stp")
		
		if os.path.exists(filename):
			self.log("found: %s" % filename)
			pass
		else:
			self.log("not found: %s" % filename)
			return None

		stapModuleInstance	= stapModule(
							name,
							filename,
							target,
							args=args,
							queue=None,
							logStream = self.args['logStream']
					)
		if stapModuleInstance is not None:
			self.outputHandler.registerStapModule(stapModuleInstance)
			stapModuleInstance.run()

			self.stapModules[stapModuleInstance.id]	= stapModuleInstance
			self.log("dispatched stapModule %s with script %s" %(stapModuleInstance,filename))
			return stapModuleInstance
		else:
			self.log("could not dispatch stapModule %s with script %s" %(stapModuleInstance,filename))
			return None
		

	def dispatchStapLabModuleAll(self,modules,target):
		for module in modules:
			self.dispatchStapLabModule(module,target)

	def dispatchGeneratorModule(self,moduleName):
		generatorModuleInstance	= self.instanciateModule(
									moduleName,				# the generatorModule's classname
									self.generatorModulesDir,		# path to look in for the generator
									#modArgs = {'queue':None,'args':self.args}
									modArgs	= self.args
									#[moduleName,[],None])			# *ModuleArgs
								)
		stream		= None
		if generatorModuleInstance is not None:
			self.generatorModules[generatorModuleInstance.id]	= generatorModuleInstance
			stream		= self.outputHandler.registerDataGenerator(generatorModuleInstance)
		return stream

	def instanciateModule(self,moduleName,modDir,modArgs={}):
		self.log("dispatching module %s" % moduleName)	
		workdir		= os.path.dirname(os.path.realpath(__file__))
		filename	= (workdir + "/" + modDir + "/" + moduleName + ".py")
		try:		
			if os.path.exists(filename):
				self.log("found: %s" % filename)
			else:
				#self.log("not found: %s" % filename)
				raise IOError("File not found: %s" % filename)

			mod		= __import__(moduleName)
			instance	= getattr(mod,moduleName)(moduleName,args=modArgs)
			return instance
		except AttributeError or TypeError or IOError:
			self.log("module %s not found, no such module" % moduleName)
			if self.args['hardFail']:
				raise


	def run(self):
		# wait for at least one module to be running
		self.log("dispatcher waiting for waiting for at least one module to run")
		while len(self.stapLabModules) == 0:
			sleep(1)
		self.log("dispatcher entering mainLoop")
		# now run until we have no more open modules.
		while self.thread.running and len(self.stapLabModules) > 0:
			modulesRunning			= {}
			for stapLabModuleID in self.stapLabModules:
				stapLabModule		= self.stapLabModules[stapLabModuleID]
				if stapLabModule.thread.running:
					modulesRunning[stapLabModuleID]		= self.stapLabModules[stapLabModule.id]
			self.stapLabModules		= modulesRunning
			sleep(0.1)
		self.log("dispatcher has no open modules left, leaving mainLoop")
		self.stop()

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
		self.thread.running	= False	

if __name__ == "__main__":
	try:
		d = Dispatcher()
		#d.dispatchStapLabModule("stapLabModule")
		d.dispatchGeneratorModule("dataGeneratorModule")
		d.run()
	except KeyboardInterrupt:
		d.stop()

	sys.exit(0)
