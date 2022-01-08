# imports
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
import platform
import os
import sys
import zmq
import platform
import subprocess
import json
from qt_modules import *

def conditionalShow(wind):
	if "aarch64" in platform.platform():
		wind.showFullScreen()
	else:
		wind.show()

class TextEntryWindow(QWidget):
	
	def centerWindow(self):
		qtRectangle = self.frameGeometry()
		centerPoint = QDesktopWidget().availableGeometry().center()
		y = centerPoint.y()
		print("y:" + str(y))
		y /= 2
		centerPoint.setY(int(y))
		qtRectangle.moveCenter(centerPoint)
		self.move(qtRectangle.topLeft())

	def returnText(self):
		self.callback(self.passwordEdit.text())
		#os.system("killall onboard")
		conditionalShow(self.parent)
		self.hide()
		
	def btnstate(self,b):
		if b.isChecked():
			self.passwordEdit.setEchoMode(QLineEdit.Normal)
		else:
			self.passwordEdit.setEchoMode(QLineEdit.Password)
			
	def __init__(self, essid = "wifi", parent = None, callback = None):
		print("Creating TEW")
		super().__init__(parent)
		self.parent = parent
		self.callback = callback
		self.passwordEdit = QLineEdit(self)
		self.passwordEdit.returnPressed.connect(self.returnText)
		#self.bottomHalf = QFrame(self)
		self.layout   = QVBoxLayout()
		self.label    = QLabel(self)
		self.label.setText("Enter Password for " + essid)
		
		self.showPassword = QCheckBox("Show Password")
		self.showPassword.stateChanged.connect(lambda:self.btnstate(self.showPassword))
		self.showPassword.setChecked(False)
		self.btnstate(self.showPassword)
		
		self.label       .setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		self.passwordEdit.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		self.showPassword.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		
		self.layout.addWidget(self.label       )
		self.layout.addWidget(self.passwordEdit)
		self.layout.addWidget(self.showPassword)
		#self.layout.addWidget(self.bottomHalf)
	
	
		self.setLayout(self.layout)
		os.system("onboard -s 480x160 -x 0 -y 160 &")
		#os.system("xdotool search \"onboard\" windowactivate --sync &")
		
		self.setFixedWidth(480)
		self.setFixedHeight(150)
				
		self.centerWindow()
		
		self.setWindowFlag(Qt.FramelessWindowHint)
		print("Done Creating TEW")
		return None
	
class SSIDWindow(QWidget):
	def connect(self, passwd):
		ESSID = self.hostDict["ESSID"]
		print("connecting to " + ESSID)
		command = "sudo nmcli dev wifi connect " + ESSID + " password \"" + passwd + "\""
		print(command)
		os.system(command)
		self.close()
	
	def connectToHost(self, hostDict):
		self.hostDict = hostDict
		print(json.dumps(hostDict, indent = 4))
		if hostDict.get("Authentication Suites (1)") == "PSK":
			self.tew = TextEntryWindow(parent = None, callback = self.connect, essid = hostDict.get("ESSID")) # a window cannot have another window as parent. this kills it
			conditionalShow(self.tew )
		else:
			command = "sudo nmcli dev wifi connect " + ESSID
			print(command)
			os.system(command)
		self.close()
			
	
	def anyButtonPressed(self, instance):
		print(instance.text())
		ssid, freq, address = instance.text().split("✵")
		for host in self.layout.slice.hosts:
			if address == host.get("ADDRESS"):
				self.connectToHost(host)
				break
		#if instance == self.folderSlice:
		#	self.fileSlice.setItemsFromDirectory(os.path.join(self.folderSlice.basePath, self.folderSlice.selectedText))
		#elif instance == self.fileSlice:
		#	sendpath = os.path.join(instance.basePath, instance.selectedText) + ".json"
		#	self.socket.send_string(sendpath)
			
	def scanSSIDs(self):
		#SSIDs = subprocess.check_output(["sudo iw dev wlan0 scan | grep 'SSID:'"], shell=True).decode(encoding='UTF-8')
		#SSIDs = SSIDs.split('\n')
		#SSIDs = [str(s.replace('\tSSID: ', '')) for s in SSIDs]
		#SSIDs = [s for s in SSIDs if s != '']
		SSID_txt = runCommand("sudo iwlist wlan0 scan")
		print(SSID_txt)
		HOSTS = []
		ssidDict = None
		ssidLines = SSID_txt.split("\n")
		for i, line in enumerate(ssidLines):
			
			# add dict to master list if final line
			if ssidDict != None:
				if i+1 < len(ssidLines):
					if ssidLines[i+1].startswith("          Cell"):
						HOSTS += [ssidDict]
				elif i+1 == len(ssidLines):
					HOSTS += [ssidDict]
				
			# Cell marks beginning of interface
			if line.startswith("          Cell"):
				ssidDict = {}
				ssidDict["ADDRESS"] = line.split("Address:")[1].strip()
			else:
				try:
					key, value = [s.strip() for s in line.split(":")]
					ssidDict[key] = value
					ssidDict[key] = float(value)
				except:
					pass
		print(json.dumps(HOSTS, indent = 4))
		HOSTS = [hostDict for hostDict in HOSTS if hostDict.get("ESSID").replace("\"","").strip() != "" ] # remove empty string elements
		HOSTS = sorted(HOSTS, key = lambda i: i['ESSID'])
		SSIDs = [hostDict.get("ESSID").replace("\"","") for hostDict in HOSTS]
		FREQs = [hostDict.get("Frequency").split(" ")[0].replace("\"","") for hostDict in HOSTS]
		ADDRs = [hostDict.get("ADDRESS") for hostDict in HOSTS]
		#SSIDs = [s for s in SSIDs if s != ""]
		print(SSIDs)
		ssid_freq = []
		for s, f, a in zip(SSIDs, FREQs, ADDRs):
			ssid_freq += [s + "✵" + f + "✵" + a]
		self.layout.slice.setItems(ssid_freq)
		self.layout.slice.hosts=HOSTS
		
	def __init__(self, parent=None):
		super().__init__(parent)
		self.layout = SelectItemFromList(self, [""])
		self.setLayout(self.layout)
		self.scanSSIDs()
		
		
	
class MainWindow(QWidget):

	def anyButtonPressed(self, instance):
		layout = instance.parentLayout
		if layout == self.folderSlice:
			self.fileSlice.setItemsFromDirectory(os.path.join(self.folderSlice.basePath, self.folderSlice.selectedText))
		elif layout == self.fileSlice:
			sendpath = os.path.join(layout.basePath, layout.selectedText) + ".json"
			self.socket.send_string(sendpath)
			
			
	def settings(self, instance = None):
		SSIDWindow_inst = SSIDWindow()
		if "aarch64" in platform.platform():
			SSIDWindow_inst.showFullScreen()
		else:
			SSIDWindow_inst.show()
		#self.hide()
	
	def __init__(self, parent=None):
		super().__init__(parent)
		
		context = zmq.Context()
		self.socket = context.socket(zmq.PUB)
		self.socket.bind("tcp://*:5555")
		
		self.allCategoriesDir = os.path.join(sys.path[0], 'patches/')
		self.folderSlice = SliceViewSelect(self, [""]*4)
		self.folderSlice.buttons[0].size_hint = (0.5, 1.0)
		self.folderSlice.setItemsFromDirectory(self.allCategoriesDir)
		self.fileSlice   = SliceViewSelect(self, [""]*4) # start fileslice empty for now
		
		self.folderSlice.buttons[0].select() #select the first one
		self.fileSlice.buttons[0].select()  #select the first one
		
		self.navbox = NavBox(self)
   
		self.filefolderSlice   = QHBoxLayout()
		self.filefolderSlice.addLayout(self.folderSlice )
		self.filefolderSlice.addLayout(self.fileSlice )
		
		self.verticalBox	 = QVBoxLayout()
		self.verticalBox.addLayout(self.filefolderSlice )
		self.verticalBox.addLayout(self.navbox )

		self.setLayout(self.verticalBox)
		
		
		return None

def CheckReturn(retval):
	print(retval)
	
if __name__ == '__main__':
	app = QApplication(sys.argv)
	main_window = MainWindow()
	#tew = TextEntryWindow(None, CheckReturn)
	#print(platform.platform())
	conditionalShow(main_window)
		
	sys.exit(app.exec_())

 
