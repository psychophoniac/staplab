import sys
for folder in ["gather", "process", "view"]:
	sys.path.append(folder)
import OutputModule as outmod
import StapModuleHandler as stmodh
from GraphModule import GraphModule
from time import sleep
#from gi.repository import Gtk
import gtk
from threading import Thread


class fopraMain():
	def __init__(self, logMod = None, outMod = None):
		self.mid = -1
		self.lm = outmod.StdoutOutputModule()
		self.tid = -1
		try:
			self.tid = int(sys.argv[1])
		except IndexError, ValueError:
			self.tid = -1
		print "tid: %d" % self.tid
			
		# gui
		self.initGTK()
		
		# log
		self.lm = outmod.OutputSplitterModule(outstreams=[
									outmod.GtkListStoreOutputModule(self.builder.get_object("liststore5")),
									outmod.StdoutOutputModule()
									])
		self.om = outmod.GtkListStoreOutputModule(self.builder.get_object("liststore1"))
		self.smh = stmodh.StapModuleHandler(outputStream=self.om,logStream=self.lm)

		#self.gtkt = Thread(target=Gtk.main)
		#self.gtkt = Thread(target=gtk.main)
		self.gtkt = Thread(target=self.run)
		self.gtkt.daemon = True

	def initGTK(self):
		self.gladefile = "view/stapLabGUI.glade"
		#self.builder = Gtk.Builder()
		self.builder = gtk.Builder()
		self.builder.add_from_file(self.gladefile)

		self.tidSelWin = self.builder.get_object("selectTidDialog")

		self.mainWin = self.builder.get_object("mainWindow")
		self.logWin = self.builder.get_object("logOutputWindow")

		self.tidErrWin = self.builder.get_object("tidErrorWindow")
		self.tidErrWin.hide()	

		# wire events
		self.tidErrWin.connect("delete-event", self.tidErrWinHide)
		self.tidSelWin.connect("delete-event", self.stop)
		self.mainWin.connect("delete-event", self.stop)
		self.logWin.connect("delete-event", lambda w, e: w.hide() or True)
		self.builder.get_object("showGraphWindow").connect("delete-event", self.showGraph,"close")
		
		# button wiring is done here rather than in the glade-file		
		self.builder.get_object("button1").connect("clicked", self.showGraph)
		self.builder.get_object("button2").connect("clicked", self.showFileChooserDialog)
		self.builder.get_object("button3").connect("clicked", self.showRemoveModuleDialog)
		self.builder.get_object("button4").connect("clicked", self.showAddModuleDialog)
		self.builder.get_object("button5").connect("clicked", self.initGtkMainWindow)
		self.builder.get_object("button6").connect("clicked", self.tidErrWinHide)
		self.builder.get_object("button7").connect("clicked", self.dataExport)
		self.builder.get_object("button8").connect("clicked", self.hideFileChooserDialog)
		self.builder.get_object("button9").connect("clicked", self.hideAddModuleDialog,"dispatch")
		self.builder.get_object("button10").connect("clicked", self.hideAddModuleDialog)
		self.builder.get_object("button11").connect("clicked", self.hideRemoveModuleDialog,"delete")
		self.builder.get_object("button12").connect("clicked", self.hideRemoveModuleDialog)
		self.builder.get_object("button13").connect("clicked", self.showLogOutputWindow)
	
		# add autoscroll to all scrolledWindows
		# TODO: to disable autoscroll, call these with "disconnect" instead of "connect"
		self.builder.get_object("treeview1").connect("size-allocate", self.autoscroll, "treeview1")
		self.builder.get_object("treeview2").connect("size-allocate", self.autoscroll, "treeview2")
		self.builder.get_object("treeview3").connect("size-allocate", self.autoscroll, "treeview3")
		self.builder.get_object("treeview4").connect("size-allocate", self.autoscroll, "treeview4")
		self.builder.get_object("treeview5").connect("size-allocate", self.autoscroll, "treeview4")
		
		#toggle quiet state in module list
		self.builder.get_object("cellrenderertoggle1").connect("toggled", self.toggleModuleQuietState)
		
		if self.tid > 0:
			self.initGtkMainWindow()
		else:
			self.tidSelWin.show()
			self.mainWin.hide()

	def tidErrWinHide(self, *args):
		self.tidErrWin.hide()

	def initGtkMainWindow(self, *args):
		self.max_pid_file = "/proc/sys/kernel/pid_max"
		self.mainWin.connect("delete-event", self.stop)
		try:
			self.maxPID = int(open(self.max_pid_file).read().replace('\n',''))
		except IOError as e:
			print e
		while True:	# there is no do-while in python, so we use a while True and a return statement further down
			if self.tid > 0 and self.tid <= self.maxPID:
				self.builder.get_object("entry1").set_text(str(self.tid))
				self.mainWin.show_all()
				self.tidSelWin.hide()
				return self.tid
			else:
				self.builder.get_object("entry2").set_text(str(self.tid))
				self.tidSelWin.show()
				try:					
					self.tid = int(self.builder.get_object("entry2").get_text())
				except ValueError:
					self.tid = -1
					self.tidErrWin.show()
	
	def toggleModuleQuietState(self, widget,path,*args):
		if path is not None:
			model 	= self.builder.get_object("treeview2").get_model()
			row 	= model[path]
			name 	= row[0]
			show 	= row[1]
			mid 	= int(row[2])
			dm 	= self.smh.getModuleDict()
			module	= dm[mid]
			module.toggleQuiet()
			row[1] = not row[1]

	def showGraph(self,sm=None, *args):
		if "close" in args:
			self.gm.stop()
		else:
			sm = self.getSelectedRowFromTreeView(treeView=self.builder.get_object("treeview2"))
			self.lm.outLog(outmod.makeOutstreamTuple(self,"log module:" + str(sm)))
			mlist = self.smh.getModuleList()
			print "mdict: " + str(mlist)
			for (i,m) in mlist:
				if m.mname == sm:
					sm = m
					break
			print "selected: " + str(sm)
			
			rt = self.builder.get_object("showGraphWindow")
			self.gm = GraphModule(renderTarget=rt,
						mID=-1,
						mName="GraphModule",
						dataStream=sm,
						FPS=2,
						logStream=self.lm,
						outStream=self.lm
						)
			self.gm.start()
			self.builder.get_object("showGraphWindow").show_all()
	
	def showLogOutputWindow(self,*args):
		self.builder.get_object("logOutputWindow").show()
	
	def showFileChooserDialog(self,*args):
		self.builder.get_object("fileChooserDialog").show()
	
	def hideFileChooserDialog(self,*args):
		self.builder.get_object("fileChooserDialog").hide()

	def showRemoveModuleDialog(self,*args):
		self.builder.get_object("removeModuleDialog").show()
		#TODO
		# set text accordingly to the selected module in the main window
		pass

	def hideRemoveModuleDialog(self,*args):
		#TODO
		self.builder.get_object("removeModuleDialog").hide()
		if "remove" in args:
			pass
		self.updateSpinner()

	def showAddModuleDialog(self,*args):
		modules = []
		for module in stmodh.stapModules.items():
			modules += [module[0]]

		self.updateListStore(ls=self.builder.get_object("liststore3"),values=modules)

		self.addModWin = self.builder.get_object("addModuleDialog")
		self.builder.get_object("treeview3").set_cursor(0)
		self.addModWin.show()

	def hideAddModuleDialog(self,*args):
		self.builder.get_object("addModuleDialog").hide()
		
		if "dispatch" in args:
			selectedModule = self.getSelectedRowFromTreeView(self.builder.get_object("treeview3"))
			additionalArgs = self.builder.get_object("entry3").get_text()
			self.log("dispatch: %s additional values:%s" % (selectedModule,additionalArgs))
			additionalArgs = additionalArgs.split(",")
			self.smh.startModule(module=selectedModule, args=additionalArgs, target=self.tid, outStream=self.om, logStream=self.lm)
			#TODO recover old "show in output" state
			ml = self.smh.getModuleList()
			#print "ml: ", ml
			vals = map((lambda m : [m[1].mname]+[True]+[m[1].mid]),ml)
			#vals = ['udp',True]
			#vals = [["abc", True]]
			#print "vals: ", vals
			self.updateListStore(ls=self.builder.get_object("liststore2"),values=vals)
		self.updateSpinner()

	def updateListStore(self,ls=None,values=[],clear=True,*args):
		if ls is not None:
			if clear:
				ls.clear()
			#print "update, values: ", values
			for val in values:
				try:
					#ls.append([val])
					#it = ls.append(row=[val])
					#print "append:" , val	
					if isinstance(val,list):
					#if ls is self.builder.get_object("liststore2"):
					#	print "tv2"
						it = ls.append(row=val)
						#for e in [0,1]:
						#	ls.set_value(it,e,val[e])
					else:
						it = ls.append(row=[val])
					#ls.append(
				except ValueError as e:
					print "Exception:",e
					self.stop()

	def updateSpinner(self):
		moduleCount = len(self.smh.getModuleList())
		self.spinner = self.builder.get_object("spinner1")
		if moduleCount > 0:
			self.spinner.start()
		else:
			self.spinner.stop()

	def autoscroll(self,sw=None,*args):
		if sw is not None:
			for elem in args:
				if isinstance(elem,str) and elem.startswith("treeview"):	
					tv = self.builder.get_object(elem)
					adj = tv.get_vadjustment()
   					adj.set_value( adj.get_upper() - adj.get_page_size() )
					self.builder.get_object(elem).queue_draw()
					return
	
	def getSelectedRowFromTreeView(self,treeView=None,*args):
		if treeView is not None:
			treeSelection = treeView.get_selection()
			result = ""
			(model, pathlist) = treeSelection.get_selected_rows()
			for path in pathlist :
				tree_iter = model.get_iter(path)
				value = model.get_value(tree_iter,0)
				result += value
			return result
		else:
			return str(None)
	
	
	def dataExport(self,*args):
		# stapmodule = currently selected item in module list
		# target = result of filechooserdialog, file/ db ...
		sm = self.getSelectedRowFromTreeView(treeView=self.builder.get_object("treeview2"))
		targetType = self.getSelectedRowFromTreeView(treeView=self.builder.get_object("treeview5"))
		targetFile = self.builder.get_object("fileChooserDialog").get_filename()
		print "Data export, module:", sm, " targetFile:", targetFile, " targetType:", targetType
		self.builder.get_object("fileChooserDialog").hide()
		pass
	
	def mainloop(self,*args):
		#self.log("mainLoop Heartbeat %d" % self.c)
		#print "hb",self.c
		#gtk.main_iteration_do(blocking=False)
		#self.c += 1
		while gtk.events_pending():
			gtk.main_iteration()
		sleep(0.1)
		return self.running	

	def log(self,data):
		#self.lm.outLog((outmod.timestamp(),"fopraMain","-1",data))
		self.lm.enqLog((outmod.timestamp(),"fopraMain","-1",data))

	def run(self):
		try:
			self.log("running()")
			self.running = True
			#self.gtkt.start()
			self.c = 0
			while self.mainloop():
				pass
		except KeyboardInterrupt:
			self.stop()

	def stop(self,*args):
		self.lm = outmod.StdoutOutputModule()
		self.om = self.lm
		self.log("stop()")
		if self.running:
			self.running = False
			self.smh.close()
			self.mainWin.destroy()
			#gtk.main_quit()
			

if __name__ == "__main__":
	fm = fopraMain(logMod="stdout")
	try:
		fm.run()
	except Exception as e:
		print e
	fm.stop()
	sys.exit(0)


