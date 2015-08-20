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
		self.stats			= {}	# {ip:{port:(send,recv)}}
		self.statNodes			= {}	# {node:(send,recv)}
		self.graph 			= nx.Graph()
		self.graph.add_node("127.0.0.1")
		self.thread			= Thread(target=self.run)
		self.thread.daemon		= True
		self.thread.running		= True
		self.lock			= Lock()
		self.thread.start()
		
	def plot(self,figure):		
		changed	= False
		for ip in self.stats:
			if ip is not "127.0.0.1" and not self.graph.has_node(ip):
				self.graph.add_node(ip,node_size=4000,node_shape="s")
				self.graph.add_edge(ip,"127.0.0.1",attr_dict={"label":"N/A"})
				changed = True
			for port in self.stats[ip]:
				#pnode = ip + ":" + port
				pnode = port
				if not self.graph.has_node(pnode):
					statName = ip + ":" + port
					self.graph.add_node(pnode,attr_dict={"node_size":700,"node_shape":"o","font_size":8})
					self.graph.add_edge(pnode ,ip, attr_dict={"label":"N/A"})
					changed = True
		if changed:
			figure.clf()
			pos = nx.spring_layout(self.graph, weight=None, iterations=100, scale = 2)
			#draw ip nodes
			ipNodeList = list(self.stats)
			#print(ipNodeList)
			try:
				nx.draw_networkx(self.graph, 
							nodelist = ipNodeList, 
							pos = pos, 
							with_labels = True,
							node_size = 4000 , 
							node_shape = "p", 
							font_size = 8
						)
			except nx.exception.NetworkXError:	# catch some error about a node not having a position yet (we just re-render, that does it)
				pass
			#draw port nodes
			portList = list(self.stats.values())
			portNodesList = [ item for sublist in (list(e) for e in portList) for item in sublist ]
			try:
				nx.draw_networkx_nodes(self.graph, 
							nodelist = portNodesList, 
							pos = pos ,
							with_labels = True,
							node_size = 700 , 
							node_shape = "o", 
							font_size=8
						)
				edges = self.graph.edges(data=True)
				labels = {}
				for (a, b, *c) in edges:
					stats = "N/A"
					if a in self.stats:
						if b in self.stats[a]:
							labels[a,b] = self.stats[a][b]
					else:
						if a in self.stats[b]:
							labels[b,a] = self.stats[b][a]
				nx.draw_networkx_edge_labels(self.graph, pos = pos, edge_labels=labels,ax=None)
			except nx.exception.NetworkXError:	# catch some error about a node not having a position yet (we just re-render, that does it)
				pass
			# draw connStats
			statNodesList = list(self.statNodes)
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
		self.log("source= %s, dest= %s" %(sip+":"+sport, dip+":"+dport))
		if sip not in self.blackListIP['source'] and dip not in self.blackListIP['dest']:
			port	= sport if func == 'send' else dport
			IP	= dip	if func == 'send' else sip
			if IP not in self.stats:
				self.stats[IP] 	= {}
			if port not in self.stats[IP]:
				self.stats[IP][port]	= (0,0)

			self.stats[IP][port]	= {
							'send': (lambda x,z: (x[0]+z,x[1])),
							'recv': (lambda x,z: (x[0],x[1]+z))
						}[func](self.stats[IP][port],int(size))
		self.lock.release()
		

