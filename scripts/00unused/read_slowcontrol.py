#!/usr/bin/env python
#######################
# read slowcontrol information from:
#     - ACNET (beam)
#     - Target
#     - Chamber HV (not active)
#     - Keithley temperature monitors
#     - vxticks
# put information into a text file and insert into mainDAQ
# post spillcount to EPICS
# insert spillcount into mainDAQ and scalerDAQ coda stream as event 0x81
#-----------------------
# maintainer: Brian Tice - tice@anl.gov
# original author: Kaz Nakahara
########################
import os, sys, datetime, time, re
import DAQUtils

##########
#constants
##########

#ROOT area of slow control scripts
logdir_root   = "/data2/log/slowcontrol/read_slowcontrol/"
codaFilename   = "/data2/data/slowcontrol/slowcontrol/slowcontrol_codadata.txt"

#how long before we need to be ready for next spill in seconds
#give it an 8s buffer
maxCycleTime = DAQUtils.super_cycle_time - 13

#how many seconds after BOS will we look for EOS
maxTimeBetweenBOSandEOS = 12

#who you gonna call?
emailList        = [ "arun.tadepalli1@gmail.com", "chenyc@fnal.gov", "reimer@anl.gov"]
#emailList_target = ["reimer@anl.gov", "jgrubin@umich.edu", "bjrams@umich.edu"]
emailList_target = ["jgrubin@umich.edu", "bjrams@umich.edu"]


###########################
# Utility Functions
###########################
def GetTimestamp():
  """Return the timestamp that we want to put into coda for this data"""
  return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def Log( message ):
  """Print message to stdout and logfile."""
  global logfile
  print message
  timestr = datetime.datetime.now().ctime()
  logfile.write( "%s - %s\n" % (timestr, message) )


#--- insert file into coda
def InsertIntoMainDAQ():
  """Insert the slowcontrol file into mainDAQ codastream"""
  inserted = False
  nAttempts = 0
  while not inserted:
    nAttempts += 1
    #limit the time 
    timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
    if nAttempts > 1 and maxCycleTime < timeSinceLastBOS:
      Log( "Ran out of time to insert file into main DAQ." )
      break

    command = ["ssh", "-x", "e906daq@e906daq1", r'ps -a |grep coda_eb_rc3' ]
    rval, output = DAQUtils.GetOutput(command, timeout=5)
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    #if there were lines of output, then the ps found something
    if len(output) > 0:
      command = ["ssh", "-x", "e906daq@e906daq1", r'plask -rt Sea2 -spState' ]
      rval, output = DAQUtils.GetOutput(command, timeout=5)
      if rval is None:
        Log("Timed out executing command %s" % str(command) )
      if len(output) != 1:
        continue
      state = output[0].strip().lower()
      if state == "active":
        Log( "Insert slowcontrol into mainDAQ" )
        insertCodaCommand = r'/data2/e906daq/slowcontrols/scripts/c/fileToEvent %s 130 3' % codaFilename
        command = ["ssh", "-x", "e906daq@e906daq1", insertCodaCommand ]
        rval, output = DAQUtils.GetOutput(command, timeout=5)
        if rval is None:
          Log("Timed out executing command %s" % str(command) )
        else:
          inserted = True
          break
      else:
        Log( "mainDAQ exists but its state is '%s'.  Not inserting slowcontrol." % state )
    else:
      Log( "Cannot connect to mainDAQ" )

  return inserted

#
def InsertIntoScalerDAQ():
  """Insert the slowcontrol file into scalerDAQ codastream"""
  inserted = False
  nAttempts = 0
  while not inserted:
    nAttempts += 1
    #limit the time 
    timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
    if nAttempts > 1 and maxCycleTime < timeSinceLastBOS:
      Log( "Ran out of time to insert file into scaler DAQ." )
      break 

    command = ["ssh", "-x", "-l", "e906daq", DAQUtils.ScalerDAQ_host, r'ps -a |grep coda_eb_rc3' ]
    rval, output = DAQUtils.GetOutput(command, timeout=5)
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    #if there were lines of output, then the ps found something
    if len(output) > 0:
      command = ["ssh", "-x", "-l", "e906daq", DAQUtils.ScalerDAQ_host, r'plask -rt Sea2sc -spState' ]
      rval, output = DAQUtils.GetOutput(command, timeout=5)
      if rval is None:
        Log("Timed out executing command %s" % str(command) )
      if len(output) != 1:
        continue
      state = output[0].strip().lower()
      if state == "active":
        Log( "Insert slowcontrol into scalerDAQ" )
        insertCodaCommand = r'/data1/c/fileToEvent %s 130 3' % codaFilename
        if "e906sc3" in DAQUtils.ScalerDAQ_host:
          insertCodaCommand = r'/software/fileToEvent/fileToEvent %s 130 3' % codaFilename
        command = ["ssh", "-x", "-l", "e906daq", DAQUtils.ScalerDAQ_host, insertCodaCommand]
        rval, output = DAQUtils.GetOutput(command, timeout=5)
        if rval is None:
          Log("Timed out executing command %s" % str(command) )
        else:
          inserted = True
          break
      else:
        Log( "scalerDAQ exists but its state is '%s'.  Not inserting slowcontrol." % state )
    else:
      Log( "Cannot connect to scalerDAQ" )

  return inserted


###################################
# Functions that fetch slowcontrol data
###################################
def GetSpillcount( ):
  """Get spillcount and prepare the data for insertion into coda"""
  Log( "Getting spill count" )
  #make sure file exists
  spillno = DAQUtils.GetSpillcount()
  return [ (GetTimestamp(), "local_spillcount", str(spillno), "DAQ") ]

def GetACNET():
  """Get ACNET data, enter some into gat EPICS, and prepare the data for insertion into coda"""
  Log("Grabbing ACNET data.")
  #these devices will be entered into slowcontrol datastream
  acnetDevices = [ \
      "F:NS2FLO","F:NS2SUP","F:NS2RET","F:NM2V", \
      "F:NM2D1", "F:NM2H", "F:NM3S", "F:NM4AN", \
      "I:BEAM21", "I:VFOUT", "E:M3TGHM", \
      "E:M3TGHS", "E:M3TGVM", "E:M3TGVS", "E:M3TGHI", \
      "E:M3TGHF", "E:M3TGVI", "E:M3TGVF", "E:M2C2HM", \
      "E:M2C2HS", "E:M2C2VM", "E:M2C2VS", "E:M2C2HI", \
      "E:M2C2HF", "E:M2C2VI", "E:M2C2VF", "L:CBAR", \
      "S:KTEVTC","F:NM2ION", "F:NM3ION", "F:NM3RST", \
      "F:NM3SEM", "F:NS7DFP", \
      "M:OUTTMP", "F:E906BM", "S:G2SEM", "F:NM3RRT", \
      "G:TURN13", "G:BNCH13", "G:NBSYD", "S:MSEP1U", \
      "S:F1SEM", "F:NM2Q1", "F:NM2Q2", "U:TODB25", \
      "G:RD3161", "G:RD3162", "I:FTSDF", \
      "F:MT6SC1", "F:MC7SC1", "F:MC1D", "F:MW1W" \
      ]

  #these devices will be entered into EPICS
  acnetDevicesToEPICS = [ \
      "I:FTSDF", "F:NM2ION", "F:NM3ION", "F:NM3RST", \
      "G:TURN13", "G:BNCH13", "G:NBSYD", "F:NS2RET", \
      "F:NM3S", "F:NM4AN", "S:G2SEM", "S:N2N3EF", \
      "F:NS7DFP", "G:RD3161", "G:RD3162", "F:NM3RRT", \
      "F:NM3SEM", "F:NS2SUP", "M:OUTTMP"\
      ]

  rval = []
  Log("Getting from acnet...")
  devl = DAQUtils.GetFromACNET(acnetDevices)
  Log("Got from acnet...")
  for dev in devl:
    val = "-9999"
    if dev.has_key("scaled"):
      val = dev["scaled"]
    elif dev.has_key("devicestatus"):
      val = dev["devicestatus"]

    #ensure string rep
    val = str(val)
    rval.append( (GetTimestamp(), dev["name"], val, "beam") )
  
    DAQUtils.UseGatEPICS()
    if dev["name"] in acnetDevicesToEPICS:
      #don't use the prefix letter for EPICS variable name
      epicsName = dev["name"].split(":")[1]
      os.system( "caput %s %s" % (epicsName, val ) )
  return rval
#end GetACNET()


nConsecutiveAlarms = 0 #keeps track of how many times target is in alarm in a row
def GetTarget():
  """Get Target data, enter some into gat EPICS, and prepare the data for insertion into coda"""
  Log("Grabbing Target data.")
  global nConsecutiveAlarms
  DAQUtils.UseTargetEPICS()

  #define map from targetID to proximity sensor name
  #note that there is no proximity sensor at position 4 (none)
  targToProx = { 1 : "PROXIMITY_LH2", 2 : "PROXIMITY_EMPTY", 3 : "PROXIMITY_LD2", 5 : "PROXIMITY_SOLID2", 6 : "PROXIMITY_SOLID3", 7 : "PROXIMITY_SOLID4" }

  #read list of EPICS process variables to fetch from target PC
  #todo: epics stuff should move to repository control
  epicsParamFile = "/data2/e906daq/slowcontrols/scripts/epics/epics_parameters.dat"
  if not os.path.isfile( epicsParamFile ):
    Log("ERROR - Cannot see epics file %s.  Can't get target data." % epicsParamFile )
  targetEPICSList = open( epicsParamFile ).readlines()
  targetEPICSList = [ line.strip() for line in targetEPICSList ]

  nextTarg = 0

  rval = []
  for pv in targetEPICSList:
    #skip proximity sensors until target stops moving
    if "PROXIMITY" in pv:
      continue

    val = DAQUtils.GetFromEPICS( pv )
    if val is None:
      Log( "ERROR - EPICS value is none.  Probably will crash..." )

    #if there was an epics connection issue try again
    if "Read" in val:
      Log( "Problem reading EPICS variable %s. Try three more times." % pv )
      gotIt = False
      for ntries in range(0,3):
        val = DAQUtils.GetFromEPICS( pv )
        Log( "Retry %d for variable %s got result: %s" % (ntries, pv, val ) )
        if "Read" not in val:
          gotIt = True
          break
      if gotIt:
        Log("Was able to recover EPICS variable %s on further attempts." % pv )
      else:
        Log("Could not get EPICS variable %s.  Set value to -9999" % pv )
        val = "-9999"

    #if there is no such variable, use value -9999
    if "not found" in val or val == "":
      Log("Bad value %s for target epics variable %s.  Set to -9999 instead." % (val, pv) )
      val = "-9999"

    #add this variable to list of lines for slowcontrol's codastream
    rval.append( ( GetTimestamp(), pv, val, "target" ) )

    #broadcast target position to gat epics
    if "targpos_control" == pv.lower():
      Log( "Output TARGPOS=%s to gat EPICS" % val )
      DAQUtils.UseGatEPICS()
      os.system( "caput TARGPOS %s" % val )
      DAQUtils.UseTargetEPICS()
      nextTarg = int(val)


    #if target is in alarm N times in a row, alert the experts
    emailExpertInterval = 5
    if "alarm" == pv.lower():
      if "1" == val:
        nConsecutiveAlarms += 1
        Log( "Target is in alarm %d times in a row" % nConsecutiveAlarms )
        if nConsecutiveAlarms % emailExpertInterval == 0:
          DAQUtils.EmailExperts( emailList_target, "E906 Alert: Target has been in alarm for %d spills in a row." % nConsecutiveAlarms, sender="slowcontrol@e906-gat6.fnal.gov" )
      else:
        nConsecutiveAlarms = 0

  #end loop over process variables

  #now check the appropriate proximity sensor to see when the target stopped moving
  foundProx = False
  if nextTarg in targToProx.keys():
    pv = targToProx[nextTarg]
    #keep reading until this variable is 1 or we are out of time
    val = DAQUtils.GetFromEPICS( pv )
    if val == "1":
      timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
      Log( "Found %s true on first try for target %d, %ds after BOS" % (pv, nextTarg, timeSinceLastBOS ) )
      foundProx = True
    while val != "1":
      timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
      Log( "Looking for %s for target %d, %ds after BOS" % (pv, nextTarg, timeSinceLastBOS ) )
      val = DAQUtils.GetFromEPICS( pv )
      Log( "%s = %s, %ds after BOS" % (pv, val, timeSinceLastBOS ) )
      if val == "1":
        foundProx = True
        Log( "%d seconds after BOS proximity sensor %s for target %d is %s" % ( timeSinceLastBOS, pv, nextTarg, val ) )
      if maxCycleTime < timeSinceLastBOS:
        Log("Never saw proximity sensor %s for target %d go to 1 after waiting %ds.  Reading sensors in possibly bad state." % (pv, nextTarg, timeSinceLastBOS ) )
        break
      #sleep a quarter second before trying again
      time.sleep( .25 )
  else:
    Log("Target position is %d, no proximity sensor exists" % nextTarg )

  #broadcast which target proximity sensor is true to gat epics
  proxTarg = 0
  if foundProx:
    proxTarg = nextTarg
  DAQUtils.UseGatEPICS()
  os.system( "caput TARGPROX %d" % proxTarg )
  DAQUtils.UseTargetEPICS()

  #now read the proximity values
  for pv in targToProx.values():
    val = DAQUtils.GetFromEPICS( pv )
    #add this variable to list of lines for slowcontrol's codastream
    rval.append( ( GetTimestamp(), pv, str(val), "target" ) )

  return rval
#end GetTarget()
    

def GetKeithley():
  """Get environmental data from Keithely monitor"""
  Log("Getting Keithley information.  Takes ~11 seconds...")

  keithley_vars = []
  keithley_vars.extend( ["T1", "T2", "T3", "T4", "T5", "T6", "T7"] )
  keithley_vars.extend( ["HT1", "HT2", "HT3", "HT4"] )
  keithley_vars.extend( ["HH1", "HH2", "HH3", "HH4"] )
  keithley_vars.extend( ["P1", "P2", "P3"] )

  keithley_data = {}
  for var in keithley_vars:
    keithley_data[var] = "-9999"

  if DAQUtils.KeithleyIsOK():
    keithleyRead_command = os.path.join( DAQUtils.slowcontrol_root, "scripts/acu/kscan")
    rcode, outLines = DAQUtils.GetOutput( keithleyRead_command, timeout=15 )
    if rcode is None:
      Log("Timed out executing command %s" % str(keithleyRead_command) )
    for line in outLines:
      line = line.strip()
      if len(line) == 0:
        continue
      #output looks like  'HT2 67.8473'
      pieces = line.split( )
      if len(pieces) < 2:
        continue
      key = pieces[0]
      val = " ".join( pieces[1:] ) #value is all the rest

      #only add the data if the key is known
      if key not in keithley_vars:
        Log("Found bad Keithley variable: %s=%s" % (key,val) )
      else:
        keithley_data[key] = val

  #format data into standard tuple
  timestamp = GetTimestamp()
  rval = []
  for key,val in keithley_data.iteritems():
    rval.append( (timestamp, key, val, "environment") )

  return rval

def GetVXTicks():
  """Get vxTicks from the mainDAQ computer and prepare data for insertion into coda"""
  Log( "Getting vxticks from mainDAQ" )

  #output of the vxticks command looks something like this
  # VXTicks Out: Connecting to database (e906) on host e906daq1.fnal.gov
  # vxTicks = 0x2b1b88: value = 2218443 = 0x21d9cb = xdr_MEM_WIDTH_COPY_ALLOC + 0x57
  # search for value = XXXXX
  #--
  # this fails and hangs if parts of mainDAQ are disconnected.  Use a timeout so the whole script doesn't stall
  vxticks = "-9999"
  command = ["ssh", "-x", "e906daq@e906daq1", r'/data2/e906daq/coda/2.6/extensions/slow_control/insert/Abbott/codadp/vxcmd TSe906 "vxTicks"' ]
  rval, output = DAQUtils.GetOutput( command, timeout = 5 )
  if rval is None:
    Log("Timed out executing command %s" % str(command) )
  else:
    for line in output:
      line = line.strip()
      m = re.search( r'value = (\d+) ', line )
      if m:
        vxticks = m.group(1)
        break

  return [ (GetTimestamp(), "vxticks", vxticks, "DAQ") ]

#end GetVXTicks)


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
nSpillsSeen   = 0

print "======== Initializing script ========"

#loop forever
while True:
  #sleep one second
  time.sleep(1)
  secondsSinceLastSpill = int(time.time()) - secondsAtLastBOS

  #get current datetime
  timenow   = datetime.datetime.now()
  daystamp  = timenow.strftime( "%Y-%m-%d" )

  #use a new debug file each day
  if daystamp != last_daystamp:
    last_daystamp = daystamp
    if logfile:
      logfile.close()
    #a new directory each month
    monthstamp = timenow.strftime( "%Y-%m" )
    logdir = os.path.join( logdir_root, monthstamp )
    os.system( "mkdir -p %s" % logdir )
    logfilename = os.path.join( logdir, "slowcontrol_%s.log" % daystamp )
    print "using logfile = ",logfilename
    #mode "a" appends if file exists and makes a new one if it doesn't
    logfile = open(logfilename, "a")
    Log( "Begin appending to logfile %s" % logfilename )


  #look for bos/eos on target EPICS
  DAQUtils.UseTargetEPICS()
  bosflag = DAQUtils.GetFromEPICS( "BOSFLAG" )
  eosflag = DAQUtils.GetFromEPICS( "EOSFLAG" )
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
    nSpillsSeen += 1
    Log( "Found EOS.  Updating slowcontrol iteration %d." % nSpillsSeen )

    #get lines of [ timestamp, key, val, type ] from all sources
    #the order matters because several things are racing
    #the target position information takes 3 seconds after EOS before it is reliable
    #vxticks should be read quickly so it is closer to the actual time of the spill
    allLines = []
    allLines += GetVXTicks()
    allLines += GetSpillcount()
    allLines += GetACNET()
#    allLines += GetChamber()
    allLines += GetKeithley()
    allLines += GetTarget()

    #if it has been more time since last BOS than a cycle will allow, then we do not trust this spill
    timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
    scDataIsGood = "1"
    if timeSinceLastBOS > DAQUtils.super_cycle_time:
      scDataIsGood = "0"
    print "SC DATA IS GOOD = ",scDataIsGood,"when it took this long:",timeSinceLastBOS
    allLines.append( (GetTimestamp(), "SLOWCONTROL_IS_GOOD", scDataIsGood, "DAQ") )

    
    #convert our tuples into string lines to be written to file
    linesForFile = [  " ".join(line) + "\n" for line in allLines ]

    #remove the last newline because the decoder gets confused by whitespace
    #this strips the last line of the last character (\n)
    linesForFile[-1] = linesForFile[-1][:-1]

    #write lines to logfile and to files to be inserted into coda
    Log( "Writing slowcontrol lines to 'tmp' file: %s" % codaFilename )
    codaFile = open(codaFilename, "w")
    codaFile.writelines( linesForFile )
    codaFile.close()
    #note: old version created a file for scalerDAQ at /sc2/slowcontrol_data/tmp.txt but this was not actually used

    #write all vars to logfile
    logfile.writelines( linesForFile )
    logfile.write("\n")

    #wait until 5s before cycle is over before inserting.
    #this minimizes the risk of inserting too soon if DAQ is starting a new run
    timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
    minInsertTime = maxCycleTime - 10
    while timeSinceLastBOS < minInsertTime:
      timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
      print "Wait to insert slowcontrol event.  %ds have passed since last BOS, wait until %ds." % (timeSinceLastBOS, minInsertTime)
      time.sleep(1)

    #insert the codafile into datasream on mainDAQ
    inserted = InsertIntoMainDAQ()
    Log( "Slowcontrol inserted into Main DAQ? %s" % str(inserted) )

    #insert the codafile into datasream on scalerDAQ
    inserted = InsertIntoScalerDAQ()
    Log( "Slowcontrol inserted into Scaler DAQ? %s" % str(inserted) )

    timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
    Log( "All done %ds after BOS" % timeSinceLastBOS )
    logfile.flush()
    #end of what to do at EOS

  #end of forever loop

#end of program
