#!/usr/bin/env python
import os, datetime, time, subprocess, sys, re
import DAQUtils
from StatMonUtils import Log, LogFlush, LogClose, SecondsToTime, fileAgeWarnTimeBuffer, fileAgeWarnTime, lastSpillHadBeam
from StatusChecker import StatusDatum
import Target
import Magnet
import Spillcounter
import SlowControl
import BeamDAQ
import MainDAQ
import ScalerDAQ
import Decoder
import DiskSpace
import StatusMonitor

# Frequency to update the meta information on the webpage about this script
checkInterval = 10 # 3

# How many seconds after BOS will we look for EOS
maxTimeBetweenBOSandEOS = 12

# Execute once, ignoring EOS/BOS signals, then quit - for debugging
oneShot = False # True or False

# These shifters want to know when it is time to start a new run
eagerShifterList = [] # [ "knakano@nucl.phys.titech.ac.jp" ]

##########################
# Start main program here
##########################

eosflag = False
bosflag = False
readyForEOS = False
secondsAtScriptStart   = int(time.time())
secondsAtLastBOS       = int(time.time())
secondsAtLastEOS       = int(time.time())
secondsAtLastBeam      = int(time.time())
secondsAtLastGoodEPICS = int(time.time())
secondsAtLastEPICSAlarm = 0 #will be used to limit EPICS warning emails to once per minute

#a special checker for the status of this script
statMonChecker = StatusMonitor.StatusMonitor()

allCheckers = [
  #Target      .Target(),
  Magnet      .Magnet(),
  #Spillcounter.Spillcounter(),
  BeamDAQ     .BeamDAQ(),
  MainDAQ     .MainDAQ(),
  ScalerDAQ   .ScalerDAQ(),
  #Decoder     .Decoder(),
  DiskSpace   .DiskSpace(),
  SlowControl .SlowControl(),
  ]

#DAQUtils.UseGatEPICS()
#loop forever
while True:
  secondsSinceScriptStart = int(time.time()) - secondsAtScriptStart
  secondsSinceLastBOS     = int(time.time()) - secondsAtLastBOS
  secondsSinceLastEOS     = int(time.time()) - secondsAtLastEOS
  secondsSinceLastBeam    = int(time.time()) - secondsAtLastBeam

  #look for bos/eos on target EPICS
  time.sleep(1)
  #DAQUtils.UseTargetEPICS()
  bosflag = DAQUtils.GetFromEPICS("BOS") # ( "BOSFLAG" )
  eosflag = DAQUtils.GetFromEPICS("EOS") # ( "EOSFLAG" )
  Log( "BOS = %s, EOS = %s, readyForEOS = %s, seconds since last spill = %d" % (bosflag, eosflag, str(readyForEOS), secondsSinceLastBOS ), debug = True )

  if secondsSinceLastBOS % checkInterval == 1:
    #clear old data
    statMonChecker.data = []
    #check the checkers for problems
    #for checker in allCheckers:
    #  if checker.HasProblems():
    #    statMonChecker.data.append( StatusDatum( checker.__class__.__name__, "Not OK", problem=True ) )
    #  elif checker.HasWarnings():
    #    statMonChecker.data.append( StatusDatum( checker.__class__.__name__, "In Warning", warning=True ) )
        

    #print times
    statMonChecker.data.append( StatusDatum( "Time since this script started", SecondsToTime(secondsSinceScriptStart) ) )
    statMonChecker.data.append( StatusDatum( "Time since last BOS", SecondsToTime(secondsSinceLastBOS) ) )
    statMonChecker.data.append( StatusDatum( "Time since last EOS", SecondsToTime(secondsSinceLastEOS) ) )
    statMonChecker.data.append( StatusDatum( "Time since last Beam", SecondsToTime(secondsSinceLastBeam) ) )

    #if epics returns empty string, then there was an EPICS timeout and there could be a problem with the target computer
    #targetEpicsVariable = "ALARM_TARGET_EPICS"
    #if not eosflag or not bosflag:
    #  #send warnings every minute
    #  #EPICS takes 10s to restart every hour.  Ignore don't send notification for the first 60s of the problem
    #  sendWarning = False
    #  secondsSinceLastEPICSProblem = int(time.time()) - secondsAtLastEPICSAlarm
    #  secondsSinceLastGoodEPICS    = int(time.time()) - secondsAtLastGoodEPICS
    #  if 60 < secondsSinceLastEPICSProblem and 60 < secondsSinceLastGoodEPICS:
    #    sendWarning = True
    #    secondsAtLastEPICSAlarm = int(time.time())
    #    DAQUtils.UseGatEPICS()
    #    os.system( "caput %s 1" % targetEpicsVariable )
    #  statMonChecker.data.append( StatusDatum( "Target Computer", "EPICS Problem", problem=True, alarm=sendWarning, email=sendWarning ) )
    #else:
    #  secondsAtLastGoodEPICS = int( time.time() )
    #  DAQUtils.UseGatEPICS()
    #  os.system( "caput %s 0" % targetEpicsVariable )

    #check target status every 3s
    #targetChecker.CheckStatus()

    #print to page
    statMonChecker.CheckStatus()
    statMonChecker.SendMailIfNeeded()
    statMonChecker.SetAlarmIfNeeded()
    LogFlush()
    

  if bosflag is "1":
    readyForEOS = True
    Log("Found BOS %d seconds after previous BOS.  Now look for EOS before taking action." % secondsSinceLastBOS )
    secondsAtLastBOS = int(time.time())

  #if we get BOS and no EOS for a while the something is wrong with spill signals, reset spill flags
  timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
  if readyForEOS and maxTimeBetweenBOSandEOS < timeSinceLastBOS:
    readyForEOS = False
    Log("Waited %d seconds after BOS but found no EOS.  Something is wrong with EOS.  Waiting for another BOS." % timeSinceLastBOS )


  if (readyForEOS and eosflag is "1") or oneShot:
    readyForEOS = False
    secondsAtLastEOS = int(time.time())
    fileAgeWarnTime = secondsSinceLastEOS + fileAgeWarnTimeBuffer
    Log( "Found EOS.  Run the script - %s" % time.ctime() )
    
    #did we really get beam
    #acnetVars = DAQUtils.GetFromACNET( ["S:G2SEM"] )
    #lastSpillHadBeam = False
    #if len(acnetVars) == 1 and "scaled" in acnetVars[0].keys():
    #  nm3sem = acnetVars[0]["scaled"]
    #  if nm3sem > 1E10:
    #    secondsAtLastBeam = int(time.time())
    #    lastSpillHadBeam = True

    time.sleep(20) # To avoid the busy time when other scripts run
    for checker in allCheckers:
      checker.CheckStatus()
    
    #make sure logfile is up to date at this spills end
    LogFlush()

    if oneShot:
      sys.exit(0)

LogClose()
#this is the end of main
