# NightShift
A specialized backup scheduler for a small environment.  
Written in Python 3.x, tested and still running in Pyhton 3.7.2

### General
NightShift checks connected computers regularly and initiate a backup, if no computers are reachable any more. It will also initiate the backup at a given timespan or through the -manualmode flag.
It handles remote backup computers by itself and takes care about a correctly synced time on the remote backup computers. NightShift will hibernate the host computer after the backup, if it is not needed anymore. 

### Environment
NightShift is written to run on the central Windows node (NAS) of a small, static office network with only a handful computers. The network is not connected to the internet, but some of the clients are (through a secondary NIC). This requires a time synchronization, because the offline computers loose track very fast.  
In the given example the NAS computer has several NICs which are all in use. On the NAS, all computers which are involved in the backup are linked as network resource in Explorer.  
On a daily basis, client computers will start and shutdown and so should the NAS, always doing a backup after a working day. Sometimes a client computer will run for several days during those the NAS should stay present all the time.

### Dependencies
NightShift is only a scheduler and requires external software to perform all actions. 
- [PsExec](https://docs.microsoft.com/en-us/sysinternals/downloads/psexec) to run commands on remote computers
- [pywakeonlan by Remco Haszing](https://github.com/remcohaszing/pywakeonlan) to wake remote computers (to handle several NICs, my fork is required  [mrtnRitter/pywakeonlan](https://github.com/mrtnRitter/pywakeonlan))
- [FreeFileSync](https://freefilesync.org/) to do the actually file diff and copy work

In addition to the software above, NightShift requires some external data.
- [Computers.txt](/Computers.txt), which contains all needed information about the network members
- [FreeFileSync-BatchScripts](/BackupJobs), which contains the backup job

During the first run, NightShift creates additional files.
- ongoing Backup Log
- temporary log file with the state of each client

### Detail
NightShift is written in small modules to keep it flexible and scalable, yet specialized for the given environment and its conditions.

To keep track of the modules, there is a debug mode implemented, which will help a lot during development. 

NightShift will write a backup log, while performing console outputs. The Logger module can be used to write in both or just one of them in order to get clear to read outputs (e.g. the countdown timer will produce a lot of unnecessary lines in the log, but it's output is useful for the console). 

Also, the temporary client state is used to overwrite the static "after backup" behavior. This ensures, that no network member is accidentally shutdown. 

The routine in general looks like:
- read Computers.txt into a dictionay to get easy access to all attributes
- perform a ping text on all computers in this dict, exclude the host
- store the result of the ping test in a temporary file
- if all computers are marked as offline, initiate the backup job
- if at least one computer is online, skip and start over after a given time span

While initiating the backup:
- check the status of the involved computers
- wake them if necassary
- check status again to ensure they are online
- synchronize time between all involved computers (due to the special network layout, the NAS-node has to be synchronized too, even if it's not involved in the backup)
- start FreeFileSync with the corresponding ffs_batch file as subprocess
- if given, shutdown or hibernate the involved computers (currently implemented only for the target computer due to the two-stage backup process)
- if given, perform additional backup jobs
- eventually, perform the ping test again and but host into hibernation if no computers are online

Due to the flexibility of the modules, which often have several options, the current implementation can easily be adjusted to a new situation, like network layout, backups, computers and so on. E.g. an earlier implementation could perform a backup remotely on computers, with the host involved only as initiation, but not as central node. 

---
*NightShift* is licensed under the [MIT License](https://github.com/hoffstadt/DearPyGui/blob/master/LICENSE).
