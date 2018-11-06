# SmogTok domoticz plugin
#
# Author: smogtok@gmail.com, 2018-11
#
#	Domoticz system python plugin for SmogTok application.
#
#   Gets current data from SmogTok page - for given probe or nearest from configuration.
#	Automatically creates domoticz devices (applicable to the choosen device) and collects data.
#   
#	Smogtok is air quality (including smog) monitoring system, that includes:
#		- multiple monitoring devices
#		- central data aggregation server
#		- application for presentation and analysis of the data
#
#   Please contact us if needed english (or other) version of the monitoring application.
#	https://smogtok.com   smogtok@gmail.com
#
#
"""
<plugin key="SmogTokPlug" name="SmogTok plugin" author="rafi" version="0.0.1" externallink="https://smogtok.com">
	<description>
		<h2>plugin SmogTok - monitorowanie jakości powietrza / air quality monitoring</h2><br/>
		<img width="64px" src="https://smogtok.com/favicon.ico" /><br/>
		Parametr "Identyfikator czujnika" jest opcjonalny. Jeśli nie zostanie ustawiony, 
		pobierane będą dane z nabliższego geograficznie, aktywnego czujnika zewnętrznego.
		<br/>
		Parameter "Identyfikator czujnika" is optional. If not set, 
		plugin will automatically get data from  the nearest (see global Domoticz localization settings) active probe.
		<br/>
		
	</description>
	<params>
		<param field="Mode1" label="Identyfikator czujnika" width="80px"></param>
	</params>
</plugin>
"""
import Domoticz
import json
import datetime

class BasePlugin:
	httpConn = None
	timeConnect = None
	Latitude = None
	Longitude = None
	
# CONSTANTS ---------------------------------
	sProtocol = "HTTPS"
	sPort = "443"
	sSmogTokHost = "smogtok.com"
	sCallForIdUrl = "/apprest/probedata/"
	sCallForGeoUrl = "/apprest/localdata/"
	sGetInterval=60
	
	def __init__(self):
		return

	def onStart(self):
		self.timeConnect = datetime.datetime.now()
		Domoticz.Debugging(2)
		DumpConfigToLog()

		ListLL = Settings["Location"].split(";", 1)
		self.Latitude = (ListLL[0])
		self.Longitude = (ListLL[1])

		# start from getting the data
		self.connectToSmogtok()
			
	def onStop(self):
		Domoticz.Log("onStop - Plugin is stopping.")

	def onConnect(self, Connection, Status, Description):
		if (Status == 0):
			Domoticz.Debug("Connected successfully.")
			self.sendRequest(Connection)
		else:
			Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Mode1"]+" with error: "+Description)

	def onMessage(self, Connection, Data):
		strData = Data["Data"].decode("utf-8", "ignore")
		Status = int(Data["Status"])

		if (Status == 200):
			Domoticz.Log("Good response received from server, Disconnecting.")
			LogMessage(strData)
			result=json.loads(strData)
			self.httpConn = None
			
			# NAME device
			if 'NAME' in result:
				d=getDeviceByName('Name')
				if (d.sValue != result['NAME']):
					d.Update(nValue=int(result['ID']), sValue=result['NAME'])

			# IJP device
			if ('IJP' in result) and ('DT' in result):
				d=getDeviceByName('IJP')
				setValueStr(d,int(result['IJP']))

			# REGS devices
			if 'REGS' in result:
				rs=result['REGS']
				for r in rs:
					#calculate code name of the register
					brn=r['REGNAME']
					brn=brn.replace(' ','')
					brn=brn.replace(',','')
					brn=brn[:4]
					if brn=='Wilg':
						brn='Humi'
					
					#get last update dt
					if 'DT' in r:
						vlu=r['DT']
					else:
						vlu=''
					
					#get value
					if 'VALUE' in r:
						v=r['VALUE']
					else:
						v=None
					
					#get device for value and set value
					d=getDeviceByName(brn)
					if brn!='Temp':
						setValueIfSDiff(d,v,vlu)
					else:
						setValueStr(d,v)
					
					#set value for % - if exists
					if 'PERCENT' in r:
						d=getDeviceByName(brn+"%")
						setValueStr(d,r['PERCENT'])

					
		elif (Status == 400):
			Domoticz.Error("Returned a Bad Request Error.")
		elif (Status == 500):
			Domoticz.Error("Returned a Server Error.")
		else:
			Domoticz.Error("Returned a status: "+str(Status))

	def onCommand(self, Unit, Command, Level, Hue):
		Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

	def onDisconnect(self, Connection):
		Domoticz.Log("onDisconnect called for connection to: "+Connection.Address+":"+Connection.Port)

	def onHeartbeat(self):
		if (self.httpConn != None and (self.httpConn.Connecting() or self.httpConn.Connected())):
			Domoticz.Debug("onHeartbeat called, Connection is alive.")
		else:
			elapsed_time = (datetime.datetime.now()-self.timeConnect).total_seconds()

			if(elapsed_time>self.sGetInterval):
				Domoticz.Debug("onHeartbeat called, run again")
#				self.timeConnect=datetime.datetime.now()
				self.connectToSmogtok()
			else:
				Domoticz.Debug("onHeartbeat called, wait for running again")

	def connectToSmogtok(self):
		self.timeConnect = datetime.datetime.now()
		self.httpConn = Domoticz.Connection(Name=self.sProtocol+" Test", Transport="TCP/IP", Protocol=self.sProtocol, Address=self.sSmogTokHost, Port=self.sPort)
		self.httpConn.Connect()		

	def sendRequest(self, Connection):
		url=""
		if(str(Parameters["Mode1"]).isdigit()):
			url=self.sCallForIdUrl+Parameters["Mode1"]
		else:
			url=self.sCallForGeoUrl+self.Latitude+","+self.Longitude

		sendData = { 'Verb' : 'GET',
					 'URL'  : url,
					 'Headers' : {
									'Connection': 'keep-alive', 
									'Host': self.sSmogTokHost, 
									'User-Agent':'Domoticz/1.0' 
								  }
				   }
		Connection.Send(sendData)

		
global _plugin
_plugin = BasePlugin()

def onStart():
	global _plugin
	_plugin.onStart()

def onStop():
	global _plugin
	_plugin.onStop()

def onConnect(Connection, Status, Description):
	global _plugin
	_plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
	global _plugin
	_plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
	global _plugin
	_plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
	global _plugin
	_plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
	global _plugin
	_plugin.onDisconnect(Connection)

def onHeartbeat():
	global _plugin
	_plugin.onHeartbeat()

# Generic helper functions
def LogMessage(Message):
	Domoticz.Log(Message)

	
def DumpConfigToLog():
	for x in Parameters:
		if Parameters[x] != "":
			Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
	Domoticz.Debug("Device count: " + str(len(Devices)))
	for x in Devices:
		Domoticz.Debug("Device:		   " + str(x) + " - " + str(Devices[x]))
		Domoticz.Debug("Device ID:	   '" + str(Devices[x].ID) + "'")
		Domoticz.Debug("Device Name:	 '" + Devices[x].Name + "'")
		Domoticz.Debug("Device nValue:	" + str(Devices[x].nValue))
		Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
		Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
	
	for x in Settings:
		Domoticz.Debug("Settings:		   " + str(x) + " - " + str(Settings[x]))

	return
				

####################################################################
#devices definitions

#			80 - temp
#			81 - wilgotnosc
#			243, 6 - procent
#			249, 1 - jakość powietrza
#			243, 19 - tekst


# Name, IJP, 
# PM xxx, PM xxx IJP, PM xxx %
# Temp
# Humi


CONST_DEVICES = {
	'Name': {
				'Unit': 1,
				'Name': 'Lokalizacja czujnika',
				'Type': 243,
				'Subtype': 19
			},
	'IJP':  {
				'Unit': 2,
				'Name': 'IJP',
				'Type': 243,
				'Subtype': 31
			},
	'Temp': {
				'Unit': 3,
				'Name': 'Temperatura',
				'Type': 80,
				'Subtype': None
			},
	'Humi': {
				'Unit': 4,
				'Name': 'Wilgotność',
				'Type': 81,
				'Subtype': None
			},
	'PM25': {
				'Unit': 5,
				'Name': 'PM 2,5',
				'Type': 249,
				'Subtype': 2
			},
	'PM10': {
				'Unit': 6,
				'Name': 'PM 10',
				'Type': 249,
				'Subtype': 2
			},
	'PM25%': {
				'Unit': 7,
				'Name': 'PM 2,5 - % normy',
				'Type': 243,
				'Subtype': 6
			},
	'PM10%': {
				'Unit': 8,
				'Name': 'PM 10 - % normy',
				'Type': 243,
				'Subtype': 6
			}
}

				
def getDeviceByName(dname):
	if not (dname in CONST_DEVICES):
		Domoticz.Error("Can't find configuration for device "+dname)
		return None
	d=CONST_DEVICES[dname]
	if d['Unit'] in Devices:
		return Devices[d['Unit']]
	Domoticz.Log("Create device "+dname)
		
	if d['Subtype']==None:
		Domoticz.Device(Name=d['Name'], Unit=d['Unit'], TypeName=dname, Type=d['Type']).Create()
	else:
		Domoticz.Device(Name=d['Name'], Unit=d['Unit'], TypeName=dname, Type=d['Type'], Subtype=d['Subtype']).Create()
	return Devices[d['Unit']]


def setValueIfSDiff(d,v,s):
	if (d.sValue != s):
		Domoticz.Log("Update device value:"+d.Name+":"+str(v))
		d.Update(nValue=int(v), sValue=s)
	else:
		Domoticz.Debug("Device value didn't change:"+d.Name)
		
def setValueStr(d,v):
	Domoticz.Log("Update device string value:"+d.Name+":"+str(v))
	d.Update(nValue=int(v), sValue=str(v))
