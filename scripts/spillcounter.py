#!/usr/bin/env python
#######################
# read spillcount from file
# post spillcount to EPICS
# insert spillcount into mainDAQ and scalerDAQ coda stream as event 0x81
#
########################
import os, sys, datetime, time
import DAQUtils

##########
#constants
##########

#ROOT area of slow control scripts (todo: environmental)
logdir_root   = "/data2/log/slowcontrol/spillcounter/"

c_maxSpillDiff = 2 #if beam/scaler spillcounters are more than this amount behind, issue an alarm

waitTimeAfterEOS = 20 #wait this number of seconds after EOS before updating spillcount file and waiting for next EOS

#how many seconds after BOS will we look for EOS
maxTimeBetweenBOSandEOS = 12


#who you gonna call?
#emailList        = ["grass@phys.sinica.edu.tw", "arun.tadepalli1@gmail.com", "reimer@anl.gov", "chenyc@fnal.gov"]
#emailList        = ["grass@phys.sinica.edu.tw", "arun.tadepalli1@gmail.com", "chenyc@fnal.gov"]
emailList        = ["zhangzw@hust.edu.cn", "chenyc@fnal.gov"]

def Log( message ):
  """Print message to stdout and logfile."""
  global logfile
  print message
  timestr = datetime.datetime.now().ctime()
  logfile.write( "%s - %s\n" % (timestr, message) )

def GetSpillcountFromFile(filename):
  """Open the file and extract the spillcount"""
  #make sure file exists
  if not os.path.isfile(filename):
    message = "ERROR - No such spillcount file '%s'.  Cannot update spillcount!" % filename
    logfile.write( "%s\n" % message )
    #DAQUtils.EmailExperts(emailList, message, sender="spillcounter@e906-gat6.fnal.gov")
    return 0

  #read the file
  lines = open(filename).readlines()

  if len(lines) == 0:
    message = "ERROR - spillcount file '%s' has 0 lines.  Cannot update spillcount!" % filename
    logfile.write( "%s\n" % message )
    #DAQUtils.EmailExperts(emailList, message, sender="spillcounter@e906-gat6.fnal.gov")
    return 0

  if len(lines) > 1:
    logfile.write( "Warning - spillcount file '%s' has %d lines, expected 1.\n" % ( filename, len(lines) ) )

  spillcount = int(lines[0])
  return spillcount

def Log( message ):
  """Print message to stdout and logfile."""
  print message
  timestr = datetime.datetime.now().ctime()
  logfile.write( "%s - %s\n" % (timestr, message) )


######################
######################
# Main program
######################
######################

##################
# global variables
##################
#we will create a new debug file each day
last_daystamp = ""
logfile       = None

secondsAtLastBOS = int(time.time()) #time since epoch at last BOS
readyForEOS = False       #make sure we only one once per spill by requiring EOS after BOS

iteration = 0

print "======== Initializing script ========"

#loop forever
while True:
  #sleep one second
  time.sleep(1)
  secondsSinceLastSpill = int(time.time()) - secondsAtLastBOS

  #get current datetime
  timenow = datetime.datetime.now()
  daystamp = timenow.strftime( "%Y-%m-%d" )

  #use a new debug file each day
  if daystamp != last_daystamp:
    last_daystamp = daystamp
    if logfile:
      logfile.close()
    #a new directory each month
    monthstamp = timenow.strftime( "%Y-%m" )
    logdir = os.path.join( logdir_root, monthstamp )
    os.system( "mkdir -p %s" % logdir )
    logfilename = os.path.join( logdir, "spillcounter_%s.log" % daystamp )
    print "using logfile = ",logfilename
    #mode "a" appends if file exists and makes a new one if it doesn't
    logfile = open(logfilename, "a")
    Log( "Begin appending to logfile %s" % logfilename )

  #look for bos/eos on target EPICS
  #DAQUtils.UseTargetEPICS()
  DAQUtils.UseGatEPICS()
  print "checks using logfile = ",logfilename
  #bosflag = DAQUtils.GetFromEPICS( "BOSFLAG" )
  #eosflag = DAQUtils.GetFromEPICS( "EOSFLAG" )
  bosflag = DAQUtils.GetFromEPICS( "BOS" )
  eosflag = DAQUtils.GetFromEPICS( "EOS" )
  print "BOS = %s, EOS = %s, readyForEOS = %s, seconds since last spill = %d" % (bosflag, eosflag, str(readyForEOS), secondsSinceLastSpill )

  if bosflag is "1":
    readyForEOS = True
    Log("Found BOS %d seconds after previous BOS.  Now look for EOS before taking action." % secondsSinceLastSpill )
    secondsAtLastBOS = int(time.time())

  #if we get BOS and no EOS for a while the something is wrong with spill signals, reset spill flags
  timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
  if readyForEOS and maxTimeBetweenBOSandEOS < timeSinceLastBOS:
    readyForEOS = False
    Log("Waited %d seconds after BOS but found no EOS.  Something is wrong with EOS.  Waiting for another BOS." % timeSinceLastBOS )


  if readyForEOS and eosflag is "1":
    readyForEOS = False
    Log( "Found EOS.  Updating spillcount for iteration %d." % iteration )
    iteration += 1

    #get spillcount from files
    #note: spillcount should be 1 higher than the other two.
    #      this is because this script incremented spillcount on the previous spill
    #      the DAQs will increment during this spill
    spillcount           = GetSpillcountFromFile( DAQUtils.spillcount_filename )
    spillcount_beamDAQ   = GetSpillcountFromFile( DAQUtils.spillcount_filename_beamDAQ )
    spillcount_scalerDAQ = GetSpillcountFromFile( DAQUtils.spillcount_filename_scalerDAQ )
    Log( "Spillcount = %d, from BeamDAQ = %d, from ScalerDAQ = %d" % (spillcount, spillcount_beamDAQ, spillcount_scalerDAQ) )

    #broadcast EOS and spillcounter to internal network
    #DAQUtils.UseGatEPICS()
    #Log("Setting E906EOS=1 and SPILLCOUNTER=%d on gat EPICS" % spillcount)
    #os.system( "caput E906EOS 1" )
    #os.system( "caput SPILLCOUNTER %d" % spillcount )
    #time.sleep(1)  #let EPICS catch up


    #check to see if mainDAQ is alive and insert spillcount if it is active
    command = ["ssh", "-x", "e1039daq@e1039daq1", r'ps -a |grep coda_eb_rc3' ]
    rval, output = DAQUtils.GetOutput(command, timeout=5)
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    #if there were lines of output, then the ps found something
    if len(output) > 0:
      command = ["ssh", "-x", "e1039daq@e1039daq1", r'plask -rt Spin -spState' ]
      rval, output = DAQUtils.GetOutput(command, timeout=5)
      if rval is None:
        Log("Timed out executing command %s" % str(command) )
      if len(output) == 1:
        state = output[0].strip().lower()
        if state == "active":
          Log( "Insert spillcount into mainDAQ" )
          insertCodaCommand = r'/data2/e906daq/slowcontrols/scripts/c/fileToEvent %s 129 3' % DAQUtils.spillcount_filename
          command = ["ssh", "-x", "e1039daq@e1039daq1", insertCodaCommand]
	  rval, output = DAQUtils.GetOutput(command, timeout=5)
          if rval is None:
            Log("Timed out executing command %s" % str(command) )
        else:
          Log( "mainDAQ exists but its state is '%s'.  Not inserting spillcount." % state )
      else:
        Log( "Cannot parse mainDAQ state.  Plask output was %s." % str(output) )
    else:
      Log( "Cannot connect to mainDAQ" )

    #check to see if scalerDAQ is alive and insert spillcount if it is active
    scalerDAQDead = False
    command = ["ssh", "-x", "e906daq@e906sc3", r'ps -a |grep coda_eb_rc3' ]
    rval, output = DAQUtils.GetOutput(command, timeout=5)
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    #if there were lines of output, then the ps found something
    if len(output) > 0:
      command = ["ssh", "-x", "e906daq@e906sc3", r'plask -rt Sea2sc -spState' ]
      rval, output = DAQUtils.GetOutput(command, timeout=5)
      if rval is None:
        Log("Timed out executing command %s" % str(command) )
      if len(output) == 1:
        state = output[0].strip().lower()
        if state == "active":
          Log( "Insert spillcount into scalerDAQ" )
          #todo: why is this a different fileToEvent
          #insertCodaCommand = r'/data1/c/fileToEvent %s 129 3' % DAQUtils.spillcount_filename
          insertCodaCommand = r'/data2/e906daq/slowcontrols/scripts/c/fileToEvent %s 129 3' % DAQUtils.spillcount_filename
          command = ["ssh", "-x", "e906daq@e906sc3", insertCodaCommand]
          rval, output = DAQUtils.GetOutput(command, timeout=5)
          if rval is None:
            Log("Timed out executing command %s" % str(command) )
        else:
          Log( "Cannot parse scalerDAQ state.  Plask output was %s." % str(output) )
      else:
        Log( "scalerDAQ exists but its state is %s.  Not inserting spillcount." % state )
    else:
      Log( "Cannot connect to scalerDAQ." )


    #set EOS to 0
    #todo: after certain time or check target EPICS EOS?
    time.sleep(1)
    DAQUtils.UseGatEPICS()
    #Log("Setting E906EOS=0 on gat EPICS")
    #os.system( "caput E906EOS 0" )

    logfile.flush()
    #print "Sleeping for %d seconds before incrementing spillcount (do not restart script now)..." % waitTimeAfterEOS
    #time.sleep( waitTimeAfterEOS )
    # spillcount += 1
    spillcount = DAQUtils.GetFromEPICS( "SPILLCOUNTER" ) 
    print (spillcount)

    # DAQUtils.GetFromEPICS( "EOS" )
    spillcountFile = open(DAQUtils.spillcount_filename,"w")
    spillcountFile.write( str(spillcount) )
    spillcountFile.close()

    Log( "Updated spillcount to %s." % spillcount )
    #this is the end of what to do in case of EOS

  #this is the end of what to do in forever loop

if logfile:
  logfile.close()
#this is the end of main
