#!/data2/epics-7.06.1/base-7.0.6/bin/linux-x86_64/softIoc

#PEReimer  Kaz had this code, but it doesn't seem to be needed
## Register all support components
#dbLoadDatabase "${TOP}/dbd/softIoc.dbd"
#dbLoadDatabase "/data2/epics-7.0.2.2/base-7.0.2.2/dbd/softIoc.dbd"
#softIoc_registerRecordDeviceDriver pdbbase

## Load SpinQuest db
dbLoadDatabase "/data2/e1039/daq/slowcontrols/epics/spinQuest.db"

iocInit
