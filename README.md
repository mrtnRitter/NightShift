# NightShift
A specialized backup scheduler for a small enviroment.

### General
NightShift checks connected computers regularly and initiate a backup, if no computers are reachable any more. It will also initiate the backup at a given timespan or through the -manualmode flag.
It handles remote backup computers by itself and takes care about a correctly synced time on the remote backup computers. NightShift will hibernate the host computer after the backup, if it is not needed anymore. 

### Environment
NightShift is written to run on the central Windows node (NAS) of a small, static office network with only a handful computers. The network is not connected to the internet, but some of the clients are (through a secondary NIC). This requires a time synchronization, because the offline computers loose track very fast. In the given example, and how it is implemented, the NAS computer has several NICs which are all connected to a client computer.  
On a daily basis, client computers will start and shutdown and so should the NAS, always doing a backup after a working day. Sometimes a client computer will run for several days during those the NAS should stay present all the time.

### Dependencies
NightShift is only a scheduler and requires external software to perform all actions. 
- [PsExec](https://docs.microsoft.com/en-us/sysinternals/downloads/psexec) to run commands on remote computers
- [pywakeonlan by Remco Haszing](https://github.com/remcohaszing/pywakeonlan) to wake remote computers (to handle several NICs, my fork is required  [mrtnRitter/pywakeonlan](https://github.com/mrtnRitter/pywakeonlan))
- [FreeFileSync](https://freefilesync.org/) to do the actually backup

In addition to the software above, NightShift requires some external data.
- [Computers.txt](/Computers.txt), which contains all needed information about the network members
- [FreeFileSync-BatchScripts](/BackupJobs), which contains the backup job

During the first run, NightShift creates additional files.
- Backup Log
- temporary log file with the state of each client

### Detail
NightShift is written in small modules to keep it flexible and scalable, yet specialized for the given environment and its conditions.
Most of its modules have different options to control their behavior, e.g. run a command locally or on a remote machine.

To keep track of the modules, there is a debug mode implemented, which will help a lot during development. 

NightShift will write a backup log, while performing console outputs. The Logger module can be used to write in both or just one of them in order to get clear to read outputs (e.g. the countdown timer will produce a lot of unnecessary lines in the log, but it's output is quite useful for the console). 

Also, the temporary client state is used to overwrite the static "after backup" behavior. This ensures, that no network member is accidental shut down. 









