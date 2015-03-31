import threading as thr
from Queue import Queue, Empty
from time import sleep
import datetime as dt
import sys
import sqlite3
import os.path
#from gi.repository import Gtk
import gtk

# global functions
def timestamp():
	return dt.datetime.now()

def makeOutstreamTuple(module,data):
	return (timestamp(),module.__class__.__name__, module.mid, data)

def makeLogStr((timestamp, moduleName, moduleID, data)):
	return "[LOG][%s][%s|%s][%s]" % (timestamp, moduleName, moduleID, data)

def makeOutStr((timestamp, moduleName, moduleID, data)):
	return "[OUT][%s][%s|%s][%s]" % (timestamp, moduleName, moduleID, data)

Streams = { 'out':0, 'log':1 }

# base class for all output streams
# uses threads to asynchronously read the output-queues of all incomming streams
# queues in python are threadsafe, see https://docs.python.org/2/library/queue.html
class OutputModule():
	def __init__(self,mID=-1):
		self.mid	= mID if mID >= 0 else id(self)
		self.qn		= Queue()			# normal out queue
		self.ql		= Queue()			# log out queue
		self.t 		= thr.Thread(target=self.run)	# 
		self.t.daemon 	= True				#
		self.running 	= True				#
		self.t.start()					#
		
	
	def enq(self,(timestamp,moduleName, moduleID, data)):
		self.qn.put((timestamp,moduleName,moduleID,data))

	def enqLog(self,(timestamp,moduleName, moduleID, data)):
		self.ql.put((timestamp,moduleName,moduleID,data))

	def deq(self):
		try:
			line = self.qn.get_nowait()
		except Empty:
			return None
		return line

	def deqLog(self):
		try:
			line = self.ql.get_nowait()
		except Empty:
			return None
		return line	
	
	def out(self,(timestamp, moduleName, moduleID, data)=(timestamp(),"test",123,"data")):
		#print "[%s][%s|%s][%s]" % (timestamp(),moduleName,moduleID,data)
		print "data angekommen"

	def outLog(self,(timestamp, moduleName, moduleID, data)=(timestamp(),"test",123,"data")):
		print "logData angekommen"

	def run(self):
		while self.running:
			l = self.deq()
			while l is not None:
				self.out(l)
				l = self.deq()
			l = self.deqLog()
			while l is not None:
				self.outLog(l)
				l = self.deqLog()
			sleep(0.1)

	def close(self):
		pass

class DummyOutputModule(OutputModule):
	def __init(self,mID=-1):
		OutputModule.__init__(self,mID)

	def out(self,(timestamp, moduleName, moduleID, data)):
		pass

	def outLog(self,(timestamp, moduleName, moduleID, data)):
		pass

class StdoutOutputModule(OutputModule):
	def __init(self,mID=-1):
		OutputModule.__init__(self,mID)
		print makeLogStr(makeOutstreamTuple(self,data))

	def out(self,(timestamp, moduleName, moduleID, data)):
		print makeOutStr((timestamp, moduleName, moduleID, data))

	def outLog(self,(timestamp, moduleName, moduleID, data)):
		print makeLogStr((timestamp, moduleName, moduleID, data))

class StreamOutputModule(OutputModule):
	def __init(self,mID=-1):
		OutputModule.__init__(self,mID)
		#print makeLogStr(makeOutstreamTuple(self,data))

	def out(self):
		res = []
		while True:
			cur = self.deq()
			if cur is not None:
				res += cur
			else:
				return None
		return res

	def outLog(self):
		res = []
		while True:
			cur = self.deq()
			if cur is not None:
				res += cur
			else:
				break
		return res

	def run(self):
		while self.running:
			sleep(1)

# generate a global instance of stdout on import that anyone can grab.
#gls = StdoutOutputModule()
#gos = StdoutOutputModule()
gls = DummyOutputModule()
gos = DummyOutputModule()

#global log Function
def glog(module,data):
	if gls is not None:
		name = "None"
		mid = -1
		if module is not None:
			name 	= module.__class__.__name__
			mid	= module.mid
		gls.outLog((timestamp(),name,mid,data))

def gout(module,data):
	if gos is not None:
		name = "None"
		mid = -1
		if module is not None:
			name 	= module.__class__.__name__
			mid	= module.mid
		gos.outLog((timestamp(),name,mid,data))


class FileOutputModule(OutputModule):
	def __init__(self,outFileName,mID=-1):
		OutputModule.__init__(self,mID)
		self.fn 	= outFileName
		self.open()

	def out(self,(timestamp, moduleName, moduleID, data)):
		self.fh.write(makeOutStr(timestamp, moduleName, moduleID, data) + "\n")

	def outLog(self,(timestamp, moduleName, moduleID, data)):
		self.fh.write(makeLogStr(timestamp, moduleName, moduleID, data) + "\n")

	def open(self):
		self.fh = open(self.fn,"w")		# This opens the file and truncates it, if existent

	def close(self):
		self.fh.close()

	def flush(self):
		self.close()
		self.open()

# a thread with a reference to its' parent
class prThread(thr.Thread):
	def __init__(self,*args,**kwargs):
		self.parent = None
		thr.Thread.__init__(self,*args,**kwargs)

class DatabaseOutputModule(OutputModule):
	# DB Scheme:
	# id
	# stream Integer, 0 = outstream 1 = logstream, see "Streams" dict
	# timestamp as text in YYYY-MM-DD hh:mm:ss:uuuuuu
	# modulename 
	# moduleid
	# data raw data as text
	
	# autoFlush: creates Thread, that commits all data to file every <timeperiod>
	def __init__(self, dbName,mID=-1,commitTimePeriod=5,minElementsFlush=10):
		OutputModule.__init__(self,mID)
		self.dbname 		= dbName
		self.dbfn 		= self.dbname + ".sql"
		self.con 		= None
		self.ctp 		= commitTimePeriod	
		self.ft 		= prThread(target=self.tFlush)
		self.ft.parent 		= self
		self.ft.daemon 		= True
		self.lastFlush 		= dt.datetime.now()
		self.minElemFlush 	= minElementsFlush	# write db to disk only after at 
							# least this many elements are ready to be written
		self.elemToFlush = 0			# how many elements are wating for a flush
		self.init()
	
	def init(self):
		if self.connect() == 0 :
			self.createTable()
		
		if self.con is not None:
			glog(self,"opened db on %s.sql" % self.dbname)
			if self.ctp > 0:
				self.ft.start()
				self.lastFlush = dt.datetime.now()
				glog(self,"threaded flushing started")
			else:
				glog(self,"using instant flushing")
		else:
			glog(self,"failed to open db on %s.sql" % self.dbname)
		

	def close(self):
		if self.con is not None:
			self.flush(force=True)
			self.con.close()
			self.con = None
			glog(self,"shutdown db on %s.sql" % self.dbname)
			

	def connect(self):
		if self.dbname is not None:
			rval = 0
			if os.path.isfile(self.dbfn):
				glog(self,"DatabaseOutputModule fileName Exists: %s" % self.dbfn)
				rval = 1
			# check_same_thread=False -> allow commit triggered by other threads, too 
			self.con = sqlite3.connect(self.dbfn,check_same_thread=False)
			return rval
		else:
			glog(self,"DatabaseOutputModule needs valid db-name, None provided.")
			return -1

	def createTable(self):
		if self.con is not None:
			self.con.execute("""
					CREATE TABLE %s (
						id INTEGER PRIMARY KEY AUTOINCREMENT,
						stream INTEGER,
						timestamp TEXT,
						moduleName TEXT,
						moduleID TEXT,
						data TEXT
					)		
				""" % (self.dbname))

	def insert(self,(timestamp, moduleName, moduleID, data),stream=Streams['out']):
		if self.con is not None:
			insStr = "INSERT INTO %s (stream,timestamp,moduleName,moduleID,data) VALUES ( \'%s\',\'%s\',\'%s\',\'%s\',\'%s\')"
			self.con.execute(insStr % (self.dbname,stream,timestamp, moduleName, moduleID, data))
			#glog(self, "insert")
			if self.ctp <= 0:
				self.flush()
			

	def tFlush(self):
		while True:
			now = dt.datetime.now()
			delta = (now - self.lastFlush).total_seconds()
			if delta > self.ctp:
				self.flush()
				self.lastFlush = now
			else:
				sleep(delta)

	def flush(self,force=False):
		if self.elemToFlush > self.minElemFlush or force:		
			self.con.commit()
			self.elemToFlush = 0
			glog(self,"commit")
		else:
			self.elemToFlush += 1
	#	if self.con is not None:
		
		

	def outLog(self,(timestamp, moduleName, moduleID, data)):
		self.insert((timestamp, moduleName, moduleID, data),stream=Streams['log'])

	def out(self,(timestamp, moduleName, moduleID, data)):
		self.insert((timestamp, moduleName, moduleID, data),stream=Streams['out'])

#TODO:
# set a maximum number of lines to display in the target listStore
# autoscroll to bottom of the corresponding treeview
class GtkListStoreOutputModule(OutputModule):
	def __init__(self,gtkListStore,mID=-1):
		OutputModule.__init__(self,mID)
		self.qn		= Queue()			# normal out queue
		self.ql		= Queue()			# log out queue
		self.t 		= thr.Thread(target=self.run)	# 
		self.t.daemon 	= True				#
		self.running 	= True				#
		self.ls		= gtkListStore
		self.t.start()					#
		self.mid	= id(self) if mID is -1 else mID
	
	def enq(self,(timestamp,moduleName, moduleID, data)):
		self.qn.put((timestamp,moduleName,moduleID,data))

	def enqLog(self,(timestamp,moduleName, moduleID, data)):
		self.ql.put((timestamp,moduleName,moduleID,data))

	def deq(self):
		try:
			line = self.qn.get_nowait()
		except Empty:
			return None
		return line

	def deqLog(self):
		try:
			line = self.ql.get_nowait()
		except Empty:
			return None
		return line	
	
	def out(self,(timestamp, moduleName, moduleID, data)=(timestamp(),"test",123,"data")):
		data = makeOutStr((timestamp, moduleName, moduleID, data))
		self.ls.append([data])

	def outLog(self,(timestamp, moduleName, moduleID, data)=(timestamp(),"test",123,"data")):
		data = makeLogStr((timestamp, moduleName, moduleID, data))
		self.ls.append([data])

#	def run(self):
#		while self.running:
#			l = self.deq()
#			if l is not None:
#				self.out(l)
#			l = self.deqLog()
#			if l is not None:
#				self.outLog(l)

	def close(self):
		pass

class OutputSplitterModule:
	pass
	

if __name__ == "__main__":
	#om = StdoutOutputModule()
	#om = OutputModule()
	#om = FileOutputModule("om.txt")
	#om.enq("testmodule",1337,str(datetime.datetime.now()))
	om = DatabaseOutputModule('test')
	glog(om,"init done")
	while True:
		try:
			sleep(1)
			#om.enq((timestamp(),"testmodule",1337,str(datetime.datetime.now())))
			om.out((timestamp(),"ftest",1337,"so much fake data"))
			#sleepraise SystemExit
			
		except KeyboardInterrupt:
			if isinstance(om,FileOutputModule):
				om.close()
				om.running = False
			if isinstance(om,DatabaseOutputModule):
				om.close()
			sys.exit(0)

