import sys
for folder in ["gather", "stapLabModules"]:
	sys.path.append(folder)
from threading import Thread, Lock
from time import sleep
from stapLabModulePlot import stapLabModulePlot
import networkx as nx
import random as rand

class stapLabModuleIPconnGraph(stapLabModulePlot):
	def __init__(self,name,queue=None,args = {}):
		super(stapLabModuleIPconnGraph,self).__init__(None,queue,args=args)
		self.id				= id(self)
		self.log			= print if 'logStream' not in args else args['logStream']
		self.name			= name
		self.queue			= queue
		self.stapRequirements		= {"ip_sr_activity":[]}	# {stapModuleName:[Args]}
		self.callbackRequirements	= [ (self.plot,1000) ]
		self.refRequirements		= []
		self.blackListIP		= {"source":[],"dest":[]}	# IP's to ignore {'in':["ip"],'out':["ip"]}
		self.stats			= {}	# ip:port
		self.graph 			= nx.MultiDiGraph()
		self.graph.add_node("127.0.0.1")
		self.thread			= Thread(target=self.run)
		self.thread.daemon		= True
		self.thread.running		= True
		self.lock			= Lock()
		self.thread.start()
		
	def plot(self,figure):
		figure.clf()
		for ip in self.stats:
			if ip is not "127.0.0.1" and not self.graph.has_node(ip):
				self.graph.add_node(ip)
				self.graph.add_edge(ip,"127.0.0.1")
			for port in self.stats[ip]:
				pnode = ip + ":" + port
				if not self.graph.has_node(pnode):
					self.graph.add_node(pnode)
					self.graph.add_edge(pnode ,ip)
		pos = nx.spring_layout(self.graph,weight=None)
		nx.draw(self.graph, with_labels = True)
		#nx.draw_networkx_labels(self.stats.values(), pos, self.stats)
		figure.canvas.draw()

	def processData(self,data):
		self.lock.acquire()
		# pattern: [ TCP | UDP ]{1}.[ send | recv ]{1}[source:sIP:sPort dest:dIP,
		context, *var		= data.split()
		# match [ tcp | udp ]{1}.[ send | recv ]{1}
		proto,func		= context.split(".")
		# match [source... , dest..., size...]
		source, dest, size	= tuple(var)
		size			= size.split(":")[1]
		# match source:sourceIP:sourcePort
		sip, sport		= source.split(":")[1:]
		# match dest like above
		dip, dport		= dest.split(":")[1:]
		if sip not in self.blackListIP['source'] and dip not in self.blackListIP['dest']:
			port	= sport if func == 'send' else dport
			IP	= sip	if func == 'send' else dip
			if IP not in self.stats:
				self.stats[IP] 	= {}
			if port not in self.stats[IP]:
				self.stats[IP][port]	= (0,0)

			self.stats[IP][port]	= {
							'send': (lambda x,z: (x[0]+z,x[1])),
							'recv': (lambda x,z: (x[0],x[1]+z))
						}[func](self.stats[IP][port],int(size))
		self.lock.release()
		

