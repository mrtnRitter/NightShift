# ---------- Import Dependencies
#
#
import subprocess
import time
import sys
import os
import inspect
import platform
from wakeonlan import send_magic_packet
from datetime import datetime

# ---------- Globals
#
#
debug = False
#debug = True

psexec = "psexec -nobanner -accepteula"
logpath = ""
serverroot = ""
jobpath_local = "BackupJobs/"

timeToWaitAfterWake = 120
timeToWaitAfterCopy = 300
NetworkCheckIntervall = 3600
timeToWaitAfterShutdown = 120

StartTimeForceNightShift = "030000"
EndTimeForceNightShift = "050000"


# ====================================================================== Logger
#
#
class Logger(object):
	def __init__(self):
		self.terminal = sys.stdout
		self.log = open(os.path.join(logpath, "BackupLog.txt"), "a+", encoding="utf-8")
		
	def timestamp(self, message):
		if (message != "\n"):
			message = "[" + (str(datetime.now().date())) + " @ " + (datetime.now().strftime("%H:%M:%S")) + "]	" + message
		return message
		
	def write(self, message):
		self.terminal.write(self.timestamp(message))
		self.log.write(self.timestamp(message))
		self.log.flush()
			
	def onlylog(self, message):
		self.log.write(self.timestamp(message))
		
	def onlyterminal(self, message):
		self.terminal.write(self.timestamp(message))
		
	def terminalcounter (self, message):
		message = "\r" + self.timestamp(message)
		self.terminal.write(message)
		
	def notimestamp(self, message):
		self.terminal.write(message)
		self.log.write(message)
	
	def close(self):
		self.log.close()

	def flush(self):
		pass    

sys.stdout = Logger()


# ====================================================================== backupError
#
#
def backupError(filename):

	if (debug):
		print("DEBUG	call " + inspect.stack()[0][3] + "\n")

	with open(os.path.join(logpath, "BackupLog.txt"), "r", encoding="utf-8") as source:
		with open(os.path.join(serverroot, filename + ".txt"), "w+", encoding="utf-8") as target:
			for line in source:
				target.write(line)


# ====================================================================== Countdown
#
#
def countdown(timer, text):

	if (debug):
		print("DEBUG	call " + inspect.stack()[0][3] + "\n")

	print("Warte eine Weile ...\n")
	
	for i in range(timer,0,-1):
		sys.stdout.terminalcounter("Warte " + str(i) + " Sekunden" + " " + text + " ")
		sys.stdout.flush()
		time.sleep(1)
		
		if i == 1:
			print("\n")
			
	print(str(timer) + " Sekunden gewartet. \n")


# ====================================================================== Read Computer List and create dictionary
#
#
def readComputerList(listfile):

	if (debug):
		print("DEBUG	call " + inspect.stack()[0][3] + "\n")


	computers = {}
	computer = {}

	with open(os.path.join(logpath, listfile), "r") as file:
		for line in file:
			if line[0] == "\n":												# escape empty lines
				continue
			
			if line[0] == "[":
				computername = line[1 : line.find("]")]						# Python Slice -> array[start index : end index]
				computer = {}
				continue
			
			(none, key, val) = line.split("\t")
			computer[key.strip("\n")] = val.strip("\n")
			
			computers[computername] = computer
	
	if (debug):
		print ("DEBUG	dict created as follows:\n\n" + str(computers) + "\n")
	
	return computers


# ====================================================================== RUN C M D
#
#
def runcmd(*args):																# args = command, remote-computer

	if (debug):
		print("DEBUG	call " + inspect.stack()[0][3] + "\n")
	
	if len(args) == 1: 
		command = args[0]
			
	elif len(args) == 2:
		remote_computer = args[1]
		remote_ip = computer_getProp(remote_computer, "IP")
		remote_user = computer_getProp(remote_computer, "User")
		command = psexec + " \\\\" + remote_ip + " -u " + remote_user + " -p \"\" " + args[0]
	
	if debug:
		print ("DEBUG	running command is: " + command + "\n")
	
	sp = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	
	msg = sp.stdout.decode("unicode-escape")
	err = sp.stderr.decode("unicode-escape")
	rtc = sp.returncode
		
	if debug:
		print("DEBUG	message: \n" + msg)
		print("DEBUG	error msg: \n" + err)
		print("DEBUG	exitcode: " + str(rtc) +  "\n")

	return msg, err, rtc


# ====================================================================== Computer_getProp
#
#
def computer_getProp(computer, prop):

	if (debug):
		print("DEBUG	call " + inspect.stack()[0][3] + "\n")

	property = computers[computer].get(prop, False)
	
	if debug: 
		print ("DEBUG	requested property from " + computer + " is " + prop + ": " + property + "\n")
	
	return property


# ====================================================================== create_computerlist
#
#
def create_computerlist(*args):

	if (debug):
		print("DEBUG	call " + inspect.stack()[0][3] + "\n")

	computerlist = []
	
	if args[0] == "all":
		computerlist = list(computers)
	else:
		for computer in args:
			computerlist.append(computer)

	if (debug):
		print ("DEBUG	list created as: " + str(computerlist))
	
	return computerlist


# ====================================================================== syncTime
#
#
def syncTime(*args):																# args = computer, remote computer

	if (debug):
		print("DEBUG	call " + inspect.stack()[0][3] + "\n")
		
	computer = args[0]
		
	if len(args) == 1: 
		ip = computer_getProp(computer, "IP")
		command = "net time \\\\" + ip + " /set /yes"
		print("Hole Uhrzeit von " + computer + " mit der IP " + ip + "\n")
		exitcode = runcmd(command)[2]
	
	elif len(args) == 2:
		remote_computer = args[1]
		remote_ip = computer_getProp(remote_computer, "IP")
		s_ip = computer_getProp(remote_computer, "Server")
		
		command = "net time \\\\" + s_ip + " /set /yes"
		print("Sende Uhrzeit von " + computer + " an " + remote_computer + " mit der IP " + remote_ip + "\n")
		exitcode = runcmd(command, remote_computer)[2]

	if exitcode == 0:
		print("Uhrzeit erfolgreich synchronisiert! \n")
	else:
		print("Fehler bei der Synchronisation! \n")


# ====================================================================== getStatus
#
#
def getStatus(*args):														# computer = computername or "all"

	if (debug):
		print("DEBUG	call " + inspect.stack()[0][3] + "\n")

	status = ""
	computer_status = {}
	
	computerlist = create_computerlist(*args)
	
	for computer in computerlist:
		if (computer == platform.node()):
			status = "online"
			computer_status[computer] = status
			continue
		
		ip = computer_getProp(computer, "IP")
		s_ip = computer_getProp(computer, "Server")
		
		sys.stdout.write("Suche Computer: " + computer + "\t")
				
		command = r"ping -n 1 " + ip + " -S " + s_ip
		messagefind = runcmd(command)[0].find("TTL=")
	
		if debug:
			print("DEBUG	find string in message ... \n")
			print("DEBUG	result of find: " + str(messagefind) +"\n")
			
		if messagefind != -1:
			status = "online"
			sys.stdout.notimestamp("Status: O N L I N E \n \n")
			
		else:
			status = "offline"
			sys.stdout.notimestamp("Status: offline  \n \n")
			
		computer_status[computer] = status

	return computer_status


# ====================================================================== wake
#
#
def wake(*args):																# *args = computer1, computer2, ... or "all"

	if (debug):
		print("DEBUG	call " + inspect.stack()[0][3] + "\n")
	
	wakeEvent = False
	activeComputers = {}
			
	computerlist = create_computerlist(*args)		
	
	for computer in computerlist:
		
		prewake = getStatus(computer)
		if (prewake[computer] == "online"):
			activeComputers.update(prewake)
			continue
		
		macs = computer_getProp(computer, "MAC").split(", ")
		s_ip = computer_getProp(computer, "Server")
		print(computer + " wird hochgefahren ... \n")
		
		for mac in macs:
			if (debug):
				print("DEBUG	send WOL package to " + macs + "\n")
			
			send_magic_packet(mac, interface=s_ip)
			wakeEvent = True
			time.sleep(1)
	
	if (wakeEvent):
		countdown(timeToWaitAfterWake, "bis Computer bereit sind ...")
		activeComputers = getStatus(*args)
	
	return activeComputers
	

# ====================================================================== shutdown
#
#
def shutdown(*args):																# args = computer, mode [sleep, shutdown]

	if (debug):
		print("DEBUG	call " + inspect.stack()[0][3] + "\n")
	
	computer = args[0]
	
	with open(os.path.join(logpath, "computerstatus.txt"), "r", encoding="utf-8") as file:
		computerstatus = eval(file.read())
			
	if (computerstatus[computer] == "offline"):
		mode = args[1]
		
		print (computer + " wird heruntergefahren ... \n")
		
		if (mode == "sleep"):
			command = "-d rundll32.exe powrprof.dll,SetSuspendState 0,1,0"
		
		elif (mode == "shutdown"):
			command = "shutdown -s"
		
		runcmd(command, computer)


# ====================================================================== BackupJob
#
#
def BackupJob(*args):																# args = Job, Quelle, Ziel

	if (debug):
		print("DEBUG	call " + inspect.stack()[0][3] + "\n")
		
	job = args[0]
	job_fullname = job + ".ffs_batch"
	source = args[1]
	target = args[2]
	shutdownMode = args[3]
	
	print("* * * Starte Backup-Job: " + job + " * * *\n")
		
	status = wake(source, target)

	if (status[source] == "online" and status[target] == "online"):

		if (computer_getProp(source, "Timesrc")):
			syncTime(source, target)
		
		elif (computer_getProp(target, "Timesrc")):
			syncTime(target)
			syncTime(target, source)

		print("Sichere " + source + " auf " + target + " ...\n")
		
		command = jobpath_local + job_fullname
		runcmd(command)
		
		print("Sicherung auf " + target + " abgeschlossen.\n")
		
		countdown(timeToWaitAfterCopy, "")
		
		if len(args) == 4: 
			shutdown(target,shutdownMode)
					
	elif (status[source] == "offline" or status[target] == "offline"):
		print("        * * *   E R R O R   * * *\n")
		print("* * * Backup-Job: " + job + " ist fehlgeschlagen! * * *\n")
		backupError("Backup Job " + job + " fehlgeschlagen")
		

# ====================================================================== networkcheck
#
#
def networkcheck():

	print ("Suche aktive Computer im Netzwerk ... \n")

	computerstatus = getStatus("all")

	with open(os.path.join(logpath, "computerstatus.txt"), "w+", encoding="utf-8") as file:
		file.write(str(computerstatus))

	computerlist = create_computerlist("all")

	for computer in computerlist:
		if (computer == platform.node()):
			continue
				
		if (computerstatus[computer] == "online"):
			allOffline = False
			print ("Aktive Computer gefunden. \n")
			break
		
		allOffline = True

	if allOffline:
		print ("Keine aktiven Computer gefunden. \n")
	
	return allOffline


# ====================================================================== timecheck
#
#
def timecheck():																	# z.B 030000

	return datetime.now().strftime("%H%M%S")


# ========================================================================================================================

print("\n")
print("* * * NightShift gestartet am " + str(datetime.now().date()) + " * * * \n")

computers = readComputerList("Computers.txt")

manualmode = False

if (len(sys.argv) > 1) and (sys.argv[1] == "-manualmode"):
	manualmode = True

while True:

	if not manualmode:
		countdown(NetworkCheckIntervall, "bis das Backup gestartet wird ...")

	startjob = networkcheck()
	
	if (timecheck() >= EndTimeForceNightShift):
		nightshift = True
	
	if (timecheck() > StartTimeForceNightShift) and (timecheck() < EndTimeForceNightShift) and (nightshift):
		nightshift = False
		startjob = True
		
	if manualmode:
		manualmode = False
		startjob = True
		
	if startjob:
		print ("* * * Backupvorgang gestartet am " + str(datetime.now().date()) + " um " + str(datetime.now().strftime("%H:%M:%S")) + " * * *\n")
		
		BackupJob("Backup1ZuBackup2", "Backup2", "Backup1", "shutdown")
		BackupJob("ServerZuBackup1", "Server", "Backup1", "sleep")
		
		countdown(timeToWaitAfterShutdown, "bis Computer heruntergefahren ist ...")
		
		selfshutdown = networkcheck()
		
		if selfshutdown:
			print ("Keine weiteren Computer im Netzwerk gefunden.\n")
			print ("Fahre " + platform.node() + " herunter ...\n")
			#runcmd("shutdown -s")
			runcmd("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
			quit()


