import OutputModule as outmod
import StapModule as stapmod
from threading import Thread
from time import sleep
import networkx as nx
import matplotlib.pyplot as plt 
import matplotlib.colors as col
import matplotlib.animation as animation
import random as r
import math as m
import numpy as np
from random import random
import sys

import gtk
from numpy import arange, sin, pi
from matplotlib.figure import Figure
# uncomment to select /GTK/GTKAgg/GTKCairo
#from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
#from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvas

class GraphModule():
	def __init__(self,renderTarget=None,mID=-1,mName="GraphModule",dataStream=None,FPS=2,logStream=None,outStream=None,splitRegex=""):
		self.mid	= mID if mID >= 0 else id(self)	# module id
		self.mname	= mName				# module Name
		self.ls		= logStream			#
		self.os		= outStream			#
		self.ds		= dataStream			# datastream for incomming graph data
		if not isinstance(self.ds,outmod.GraphOutputModule):
			if self.ds is not None:
				if isinstance(self.ds, outmod.OutputSplitterModule):
					#TODO modul an bestehende koppeln
					pass
				else:
					#TODO splitter erzeugen, bestehendes modul in graphoutmod schreiben lassen
					pass
				
		self.fps	= FPS if FPS > 0 else 1		# render $FPS frames per second to target
		self.data	= {}				# datastorage for graph, dictionary
		self.sr		= splitRegex			# regex to split the raw data with into the actual data fields for the graph
		self.canvas	= None
		self.log("dataStream:" + str(self.ds))
		# default data layout:
		# [LOG/OUT][<timestamp>][<moduleName>|<moduleID>][<data>]
		#
		# so e.g. a graph would be time on x-axis and amount of syscalls on y-axis.
		# the regex would be "<-" and we would take the second part of the tuple and aggregate (count) over it.
		# the count would be the height on the y-axis
		# generally speaking we would have tuples (name,count) in the graph.
		self.rt		= renderTarget			# a target we will render to
		self.f 		= Figure(figsize=(5,4), dpi=100)		
		self.a 		= self.f.add_subplot(111)
		if self.rt is None:				# if we have no render target, create our own window
			self.win	= gtk.Window()
			#self.win.connect("destroy", lambda x: gtk.main_quit())
			self.win.connect("destroy", self.stop)
			self.win.set_default_size(400,300)	
			self.canvas	= FigureCanvas(self.f)  # a gtk.DrawingArea
			self.win.add(self.canvas)		
			self.win.show_all()
		else:
			#TODO:
			# fix warning caused by next line: 
			# process/GraphModule.py:63: GtkWarning: Attempting to add a widget with type GtkDrawingArea to a GtkWindow, but as a GtkBin subclass a GtkWindow can only contain one widget at a time; it already contains a widget of type GtkDrawingArea 
			self.rt.add(FigureCanvas(self.f))
		self.t		= Thread(target=self.run)
		self.t.daemon	= True
		self.running	= False
		#self.start()
	
	# this log function is used to get the data from the modules 
	# and is supposed to take care of handing it on to the presentating function, i.e. refreshData()
	def log(self,data):
		if self.ls is not None:
			outData = (outmod.timestamp(), self.mname, self.mid, data)
			self.ls.enqLog(outData)
		
	def out(self,data):
		if self.os is not None:
			outData = (outmod.timestamp(), self.mname, self.mid, data)
			self.os.enqLog(outData)

	# http://matplotlib.org/1.4.0/examples/user_interfaces/embedding_in_gtk.html
	def render(self):
		self.f.canvas.draw()
		if self.canvas is not None:
			#self.canvas.queue_draw()
			while gtk.events_pending():
				gtk.main_iteration()

	def generateRandomData(self):
		self.a.clear()
		r = 3+random() * 3.0
		self.data[0] = arange(0.0,r,0.1)
		self.data[1] = map((lambda e : e + random()), self.data[0])
		#print "data[0]:" , self.data[0]
		#print "data[1]:" , self.data[1]
		self.a.plot(
				self.data[0], 
				self.data[1],
				color='blue',
				linestyle='solid',
		#			dashed, solid, dotted, dash-dot
		#			marker='o',
					alpha=0.75,
		#			markersize=12,
					aa=True
				)
	
	def refreshData(self):
		if isinstance(self.ds, outmod.GraphOutputModule):
			d = self.ds.out()
			if d is not None:
				self.log("data:" + str(d))
				self.generateRandomData()
				return
				for elem in d:
					(timestamp, moduleName, moduleID, data) = elem
					dd = self.decode(data)
					self.data[dd] += 1
			else:
				self.generateRandomData()
		else:
			self.generateRandomData()
			
					
	def decode(self,data=None):
		if data is not None:
			s = data.split(self.sr)
			return s

	def run(self):
		while self.running:
			self.refreshData()
			self.render()
			sleep(1.0 / self.fps)
	
	def start(self):
		self.running = True
		#self.win.show_all()
		self.t.start()
	
	def stop(self,*args):
		self.running = False

if __name__ == "__main__":
	os	= outmod.StdoutOutputModule
	try:
		gm = GraphModule(renderTarget=None,mID=-1,mName="GraphModule",dataStream=None,FPS=1,logStream=os,outStream=os,splitRegex="")
		gm.start()
		while gm.running:
			sleep(1)
	except KeyboardInterrupt:
		gm.stop()



