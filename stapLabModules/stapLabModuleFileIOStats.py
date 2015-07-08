import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from stapLabModulePlot import stapLabModulePlot
from threading import Thread,Lock
from queue import Queue
from time import sleep
from datetime import datetime
import numpy as np

class stapLabModuleFileIOStats(stapLabModulePlot):
	def __init__(self,name = None,queue = None,logStream=print):
		super(stapLabModuleFileIOStats,self).__init__(None,queue,logStream)
		self.id				= id(self)
		self.log			= logStream
		self.name			= name if name is not None else self.__class__.__name__
		self.queue			= queue
		self.stapRequirements		= { 
							"fileio":[]
						}
		self.callbackRequirements	= [ (self.plot,500) ]				# [(callbackFunc, timer)]
		self.stats			= {}						# {file:{read:N,write:M}}
		self.scale			= 1000						# 
		self.subplot			= None
		self.rects			= (None,None)					# ([rectsRead],[rectsWrite])
		self.lock			= Lock()
		#self.plotUpd			= False

	def plot(self,figure):
		self.lock.acquire()
		if self.subplot is None:	# we reuse the subplot object for speed
			self.subplot	= figure.add_subplot(111, frame_on=True, title="File I/O Stats", xlabel="file", ylabel="kilobytes")
		if len(self.stats) > 0:
			try:
				#if self.plotUpd:	# if this is set, we had either a open/close or read/write operation
					#self.log(self.stats)
				indices		= sorted(list(self.stats))			# filenames, sorted
				valuesRead	= [ self.stats[idx]['read'] / self.scale for idx in indices ]	# bytes read / scale, sorted now
				valuesWrite	= [ self.stats[idx]['write'] / self.scale for idx in indices ]	# bytes written / scale, sorted now
				if self.rects[0] is None or len(self.rects) != len(self.stats) * 2:
					# we have new files, so more bars, so redraw them all
					ar		= np.arange(len(indices))
					width		= 0.5
					del self.rects
					self.rects	= (self.subplot.bar(ar, valuesRead, width, log = True, color='r') , 		# read-bars
								self.subplot.bar(ar + width, valuesWrite, width, log = True, color='g')	# write-bars
							)
					self.subplot.set_xticks(np.arange(len(indices)) + width)			# labels positions
					self.subplot.set_xticklabels(indices, rotation=90)				# label text and rotation
				else:
					# only same data values have changed, just fit the bars
					for rect, h in zip(self.rects[0], valuesRead):
						rect.set_height(h)
					for rect, h in zip(self.rects[1], valuesWrite):
						rect.set_height(h)
				self.subplot.legend((self.rects[0],self.rects[1]), ('read','write'))		# add legend
				# fit everything to window
				figure.tight_layout()
				figure.canvas.draw()
			except ValueError:	
				pass
			except AttributeError:
				pass
		else:
			self.subplot.text(0, 0, "no Data yet", fontsize=12)
		#self.plotUpd	= False
		self.lock.release()

	def processData(self,data):
		self.lock.acquire()
		# pattern:
		# action file:<name> [bytes:N|fd:N]?
		action, filename, *tail		= data.split()
		filename	= filename.split(":")[1]
		if action == 'close':
			if filename in self.stats:
				del self.stats[filename]
		elif action in ['read','write']:
			bytes	= int(tail[0].split(":")[1])
			if filename not in self.stats:					# TODO: this is redundancy at the moment
				self.stats[filename]	= {'read':0, 'write':0}		# there are some fopen calls fileio.stp does not catch a.t.m.
			self.stats[filename][action]	+= bytes
		elif action == 'open':
			if not filename in self.stats:
				self.stats[filename]	= {'read':0, 'write':0}
		else:
			self.log("unknown file operation %s on %s" % (action,filename))
			return
		#self.plotUpd	= True
		self.lock.release()
	
	def onStop(self):
		self.log("stats:\n%s" % str(self.stats))


