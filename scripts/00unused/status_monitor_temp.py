#!/usr/bin/env python
import os, datetime, time, subprocess, sys, re
import DAQUtils

#global variables that you might want to change

checkInterval = 3  #Frequency to update the meta information on the webpage about this script

#how many seconds after BOS will we look for EOS
maxTimeBetweenBOSandEOS = 12

#statusDir = "/var/lib/tomcat6/webapps/SeaQuestDAQStatus-dev" #where to write output html stuff - for debugging
statusDir = "/var/lib/tomcat6/webapps/SeaQuestDAQStatus" #where to write output html stuff - for normal operation

#oneShot = False  #execute once, ignoring EOS/BOS signals, then quit - for debugging
oneShot = True  #execute once, ignoring EOS/BOS signals, then quit - for debugging

logdir_root   = "/data2/log/slowcontrol/status_monitor/" #where should logfiles for this script go

#these shifters want to know when it is time to start a new run
#eagerShifterList = [ "knagai@nucl.phys.titech.ac.jp" ]
eagerShifterList = []

#do you want target alarms and email?
do_alarms = True
do_email = True  ## put it back when run4 start ## grass
#do_email = False

#do you want to print debug lines to file?
do_debug = True

magnets_are_off = True
fmag_low_current = 50
kmag_low_current = 50
      
#####################################
##########################
# Utility Functions
##########################
#####################################
def Log( message, debug = False ):
  """Print message to stdout and logfile."""
  global logfile
  timestr = datetime.datetime.now().ctime()
  line = "%s - %s" % (timestr, message)
  print line
  if logfile:
    if (not debug) or (debug and do_debug):
      logfile.write( line + "\n" )

def SecondsToTime( sec ):
  """Turn seconds into the time we want to show"""
  sec = int(sec)
  if sec < 300:
    return "%d s" % sec
  min = sec/60.
  if min < 300:
    return "%.1f min" % min
  hr = min/60.
  if hr < 24*3:
    return "%.1f hr" % hr
  day = hr/24.
  return "%.1f days" % day
  
def KillScreenSession( name ):
  """Kills a screen session that matches the pattern name."""
  command = "screen -ls | grep %s" % name
  p = subprocess.Popen( command.split(), stdout=subprocess.PIPE )
  out, err = p.communicate()
  out = out.strip()
  if "" != out:
    screenID = out.split(".")[0]
    Log( "Killing screen session with name: %s" % name )
    os.system( "screen -S %s -X quit" % screenID )
  else:
   Log("Failed to kill screen session with name: %s" % name )
  
def CodaComponentOK( state ):
  goodStates = ["active", "activating", "downloaded", "downloading", "configured", "configuring", "paused", "prestarted", "prestarting", "ending"]
  return state.lower() in goodStates

def GetRunAge( startTime ):
  """Parse the output of plask -spRunStartTime to calculate how old a run is"""
  startTime = startTime.strip()
  FMT = '%H:%M:%S'
  try:
    tstart = datetime.datetime.strptime(startTime, FMT)
  except:
    return 0

  #put timenow into the same formatting, this removes the date comonent and assumes both datetimes happen on the same day
  tdnow = datetime.datetime.now()
  tnowstr = "%02d:%02d:%02d" % ( tdnow.hour, tdnow.minute, tdnow.second )
  tnow = datetime.datetime.strptime( tnowstr, FMT )

  diff = tnow - tstart
  return diff.seconds

def DoDFCommand( disk, machine = None ):
  """Execute df command and organize output"""
  KB_TO_TB = 1. / (1024*1024*1024)
  rval = None  # function will return this

  cmd = [ "df", "-P", disk ]
  if machine:
    cmd = ["ssh", "-x", "e906daq@"+machine, r'df -P %s' % disk ]

  rcode, output = DAQUtils.GetOutput( cmd, timeout=5 )
  if rcode is None:
    Log("Timed out executing command %s" % str(cmd) )

  if len(output) > 1:
    myline = output[1].strip()
    if "No such file " not in myline and 6 == len( myline.split() ):
      device, size, used, available, percent, mountpoint = myline.split()
      rval = { \
"device" : device, \
"size" : int(size)*KB_TO_TB, \
"used" : int(used)*KB_TO_TB, \
"available" : int(available)*KB_TO_TB, \
"percent" : int(percent[0:-1]), \
"mountpoint" : mountpoint }
    else:
      if machine:
        Log( "Error getting status on %s:%s - line = %s" % (machine, disk, myline) )
      else:
        Log( "Error getting status on %s - line = %s" % (disk, myline) )
      
  return rval

def GetTargetString( x ):
  """Return display string for target position"""
  if "" == x:
    return "Unknown"
  if "1" == x:
    return "1 (LH2)"
  if "2" == x:
    return "2 (Empty)"
  if "3" == x:
    return "3 (LD2)"
  if "4" == x:
    return "4 (None)"
  if "5" == x:
    return "5 (C)"
  if "6" == x:
    return "6 (Fe)"
  if "7" == x:
    return "7 (W)"
  if "0" == x:
    return "Not Found"
  return "ERROR"

#####################################
##########################
# Class definitions
##########################
#####################################

#enum for status type
class StatusType:
  GOOD = "good"
  WARNING = "warning"
  PROBLEM = "problem"

######################
# StatusDatum
######################
class StatusDatum:
  """A specific item checked during status check"""
  def __init__(self, name, value, status = StatusType.GOOD, alarm = False, email = False, problem = None, warning = None ):
    self.name   = name
    self.value  = value
    self.status = status #status of this datum (e.g. is it a problem?)
    self.alarm  = alarm  #boolean to indicate if there should be an uh-oh target computer alarm
    self.email  = email   #boolean to indicate if there an email should be sent to expert

    #if warning or problem are given explicitly, use them
    if warning:
      self.status = StatusType.WARNING
    if problem:
      self.status = StatusType.PROBLEM

  def __str__(self):
    """String representation"""
    rval = "%s = %s, status=%s, InAlarm=%s, InEmail=%s" % (self.name, self.value, self.status, self.alarm, self.email)
    return rval
  
#########################
# StatusChecker
#########################
class StatusChecker:
  """Base class for checking the status of DAQ-related systems."""
  def __init__(self):

    self.data = []           # a list of StatusDatum
    self.pageHeader = self.__class__.__name__ + " Status" #what to write above the data for this subsytem on the webpage
    self.outputFile = os.path.join( statusDir, self.__class__.__name__ + "_Status.html" ) #where to output html status
    self.timeOfLastUpdate = int( time.time() )
    self.alarmName = None #none means there is no alarm
    self.emailList = [ "arun.tadepalli1@gmail.com", "reimer@anl.gov", "chenyc@fnal.gov" ]

    self.inAlarm   = False #remember if we are in alarm state

  def CheckStatus(self):
    """Pure virtual function to check the status.  Must be defined in inheriting classes."""
    raise Exception( "Check Status is not defined for class " + self.__class__.__name__ )

  def HasProblems(self):
    """Returns true if at least one datum says there is a problem"""
    for datum in self.data:
      if datum.status == StatusType.PROBLEM:
        return True
    return False

  def HasWarnings(self):
    """Returns true if at least one datum says there is a warning"""
    for datum in self.data:
      if datum.status == StatusType.WARNING:
        return True
    return False

  def SetAlarmIfNeeded(self):
    """Returns true if at least one datum says there should be an alarm and set the alarm.  Turn off alarm if everything is fine."""
    if not self.alarmName:
      return False
    if not do_alarms:
      return False

    #look for data that are in alarm mode
    for datum in self.data:
      if datum.alarm:
        DAQUtils.UseTargetEPICS()
        os.system( "caput %s 1" % self.alarmName )
        Log( "Issuing alarm %s. For datum: %s" % (self.alarmName, str(datum) ) )
        self.inAlarm = True
        return True
    
    #there should not be an alarm, turn it off if it is on
    if self.inAlarm:
      DAQUtils.UseTargetEPICS()
      os.system( "caput %s 0" % self.alarmName )
      Log( "Turning off alarm %s." % self.alarmName)
     
    self.inAlarm = False
    return False

  def SendMailIfNeeded(self):
    """Email the experts if necessary"""
    #loop for data saying we should email
    if not do_email:
      return False

    emailLines = []    
    emailNeeded = False
    for datum in self.data:
      emailLines.append( str(datum) )
      if datum.email:
        emailNeeded = True

    #if data has email, then send the email
    if emailNeeded:
      subject = "%s Problem" % self.__class__.__name__
      message = "\n\n".join(emailLines)
      DAQUtils.SendMail( self.emailList, subject, message=message )
      Log( "Sending email to %s for problem in %s" % (str(self.emailList), self.__class__.__name__ ) )


  def OutputToHTML(self):
    """Write the status information to HTML."""
    Log( "%s::OutputToHTML" % self.__class__.__name__ )
    lines = []

    if self.HasProblems():
      lines.append( "<span class='header problem'>%s</span>" % self.pageHeader )
    elif self.HasWarnings():
      lines.append( "<span class='header warning'>%s</span>" % self.pageHeader )
    else:
      lines.append( "<span class='header'>%s</span>" % self.pageHeader )

    lines.append("<br />")
    lines.append( "Last Updated: " + datetime.datetime.fromtimestamp( self.timeOfLastUpdate ).strftime('%Y-%m-%d %H:%M:%S') )

    lines.append( "<table>" )
    for datum in self.data:
      if datum.status == StatusType.PROBLEM:
        lines.append( "<tr class='problem'>" )
      elif datum.status == StatusType.WARNING:
        lines.append( "<tr class='warning'>" )
      else:
        lines.append( "<tr>" )
      lines.append( "<td> %s </td>" % datum.name )
      lines.append( "<td> %s </td>" % datum.value )
      lines.append( "</tr>" )
    lines.append("</table>")
    lines.append("<hr />")

    #add newline
    lines = [ line + "\n" for line in lines ]

    fout = open(self.outputFile, "w")
    fout.writelines( lines )
    fout.close()


###################
# Decoder
###################
class Decoder(StatusChecker):
  """Check what the decoders are doing"""
  def __init__(self):
    StatusChecker.__init__(self)

  def CheckStatus(self):
    Log( "%s::CheckStatus" % self.__class__.__name__ )
    self.timeOfLastUpdate = int( time.time() )
    self.data = []

    #-----------------
    #scalerDAQ decoder
    
    #is the daemon running./scalerDecoding
    command = ["ssh", "-x", "-l", "e906daq", DAQUtils.ScalerDAQ_host, 'ps -fu online |grep scalerdaq-decoding-daemon' ]
    rval, output = DAQUtils.GetOutput( command, timeout=5 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )

    if len(output)==0:
      self.data.append( StatusDatum( "Scaler Decoder Daemon", "Dead", problem=True ) )
    else:
      self.data.append( StatusDatum( "Scaler Decoder Daemon", "Alive" ) )
   
    command = ["ssh", "-x", "-l", "e906daq", DAQUtils.ScalerDAQ_host, r'ps -fu online |grep scalerdaq-decoding-daemon' ]
    rval, output = DAQUtils.GetOutput( command, timeout=5 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    scalerRuns = []
    for decoder in output:
      decoder = decoder.strip()
      m = re.search( r'/scaler_(\d+).dat', decoder )
      if m:
        runno = m.group(1)
        scalerRuns.append( runno )

    if len(scalerRuns) > 0:
      self.data.append( StatusDatum( "Decoding Scaler Runs", ",".join(scalerRuns) ) )

    self.OutputToHTML()
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()

###################
# CAENChecker
###################
class CAEN(StatusChecker):
  """Check that status of the rampCAEN program"""
  def __init__(self):
    StatusChecker.__init__(self)
  
  def CheckStatus(self):
    Log( "%s::CheckStatus" % self.__class__.__name__ )
    self.timeOfLastUpdate = int( time.time() )
    self.data = []

    #check to see if rampCAEN is alive
    command = ["ssh", "-x", "-b",  "192.168.24.114", "e906daq@e906-gat6", r'ps -a |grep rampCAEN' ]
    rval, output = DAQUtils.GetOutput( command, timeout=5 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    CAENDead = (len(output)==0)

    #if there is no rampCAEN then there is a problem
    if CAENDead:
      self.data.append( StatusDatum( "rampCAEN", "DEAD", problem=True, warning=True, alarm=True, email=True ) )
      CAENOK = False
    else:
      self.data.append( StatusDatum( "rampCAEN", "Alive", warning=False ) )
      CAENOK = True

    DAQUtils.UseGatEPICS()
    noSpillI = DAQUtils.GetFromEPICS( "ST1_IXX" )
    CAENStatus = int ( DAQUtils.GetFromEPICS( "CAENSTAT" ) )

    if (CAENStatus & 0x00000001) :
      self.data.append( StatusDatum( "Pw", "on" ) )

    if (CAENStatus & 0x00000002) :
      self.data.append( StatusDatum( "Channel Ramp", "UP", warning=True, problem=True, alarm=True ) )

    if (CAENStatus & 0x00000004) :
      self.data.append( StatusDatum( "Channel Ramp", "DOWN", warning=True, problem=True, alarm=True ) )

    if (CAENStatus & 0x00000008) :
      self.data.append( StatusDatum( "IMON >= ISET", " ", warning=True, problem=True, alarm=True ) )

    if (CAENStatus & 0x00000010) :
      self.data.append( StatusDatum( "VMON > VSET + 250V", " ", warning=True, problem=True, alarm=True ) )

    if (CAENStatus & 0x00000020) :
      self.data.append( StatusDatum( "VMON < VSET - 250 V", " ", warning=True, problem=True, alarm=True ) )

    if (CAENStatus & 0x00000040) :
      self.data.append( StatusDatum( "VOUT in MAXV protection", " ", warning=True, problem=True, alarm=True ) )

    if (CAENStatus & 0x00000080) :
      self.data.append( StatusDatum( "Ch OFF via TRIP", " ", warning=True, problem=True, alarm=True ) )

    if (CAENStatus & 0x00000100) :
      self.data.append( StatusDatum( "Power Max", " ", warning=True, problem=True, alarm=True ) )

    if (CAENStatus & 0x00000200) :
      self.data.append( StatusDatum( "TEMP > 105C", " ", warning=True, problem=True, alarm=True ) )

    if (CAENStatus & 0x00000400) :
      self.data.append( StatusDatum( "Ch disabled (REMOTE Mode and Switch on OFF position)", " ", warning=True, problem=True, alarm=True ) )

    if (CAENStatus & 0x00000800) :
      self.data.append( StatusDatum( "Ch in KILL via front panel", " ", warning=True, problem=True, alarm=True ) )
    
    if (CAENStatus & 0x00001000) :
      self.data.append( StatusDatum( "INTERLOCK via front panel", " ", warning=True, problem=True, alarm=True ) )

    if (CAENStatus & 0x00002000) :
      self.data.append( StatusDatum( "Calibration Error", " ", warning=True, problem=True, alarm=True ) )

    if (CAENStatus & 0x00004000) :
      self.data.append( StatusDatum( "Bit 14 Not Used", " " ) )

    if (CAENStatus & 0x00008000) :
      self.data.append( StatusDatum( "Bit 15 Not Used", " " ) )

    if (CAENStatus & 0x00010000) :
      self.data.append( StatusDatum( "Current w/o Beam", " %s " % noSpillI, warning=True, problem=True, alarm=True ) )
    else:
      self.data.append( StatusDatum( "Current w/o Beam", " %s " % noSpillI ) )

    if (CAENStatus & 0x00020000) :
      self.data.append( StatusDatum( "Control File", "Unreadable", warning=True, problem=True, alarm=True ) )
    

    self.OutputToHTML()
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()

###################
# Disk
###################
class DiskSpace(StatusChecker):
  """Check that status of Disks"""
  def __init__(self):
    StatusChecker.__init__(self)

  def CheckStatus(self):
    Log( "%s::CheckStatus" % self.__class__.__name__ )
    self.timeOfLastUpdate = int( time.time() )
    self.data = []

    #check shared disk
    diskname = "/data2"
    disk = DoDFCommand( diskname )
    if not disk:
      self.data.append( StatusDatum( "Available on %s" % diskname, "Disk not found", warning=True ) )
    else:
      available = disk["available"]
      isProblem = available < 1.
      self.data.append( StatusDatum( "Available on %s" % diskname, "%.1f T" % available, warning=isProblem ) )

    #-----------
    #check daq1
    diskname = "/localdata"
    hostname = "e906daq1"
    disk = DoDFCommand( diskname, hostname )
    if not disk:
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "Disk not found", warning=True ) )
    else:
      available = disk["available"] * 1024
      isProblem = available < 50.
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "%.1f G" % available, warning=isProblem ) )

    diskname = "/"
    hostname = "e906daq1"
    disk = DoDFCommand( diskname, hostname )
    if not disk:
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "Disk not found", warning=True ) )
    else:
      available = disk["available"] * 1024
      isProblem = available < 20.
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "%.1f G" % available, warning=isProblem ) )

    #-----------
    #check beam3
    diskname = "/"
    hostname = "e906beam3"
    disk = DoDFCommand( diskname, hostname )
    if not disk:
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "Disk not found", warning=True ) )
    else:
      available = disk["available"] * 1024
      isProblem = available < 5.
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "%.1f G" % available, warning=isProblem ) )

    diskname = "/home"
    hostname = "e906beam3"
    disk = DoDFCommand( diskname, hostname )
    if not disk:
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "Disk not found", warning=True ) )
    else:
      available = disk["available"] * 1024
      isProblem = available < 50.
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "%.1f G" % available, warning=isProblem ) )

    #-----------
    #check sc2
    # the computer e906sc2 developped harddisk issue. It is now decommissioned. Andrew Chen, Nov. 3, 2015
    #diskname = "/data1"
    #hostname = "e906sc2"
    #disk = DoDFCommand( diskname, hostname )
    #if not disk:
    #  self.data.append( StatusDatum( hostname + ":" + diskname, "Disk not found", warning=True ) )
    #else:
    #  available = disk["available"] * 1024
    #  isProblem = available < 50.
    #  self.data.append( StatusDatum( hostname + ":" + diskname + " Available", "%.1f G" % available, warning=isProblem ) )

    #diskname = "/"
    #hostname = "e906sc2"
    #disk = DoDFCommand( diskname, hostname )
    #if not disk:
    #  self.data.append( StatusDatum( hostname + ":" + diskname, "Disk not found", warning=True ) )
    #else:
    #  available = disk["available"] * 1024
    #  isProblem = available < 5.
    #  self.data.append( StatusDatum( hostname + ":" + diskname + " Available", "%.1f G" % available, warning=isProblem ) )

    #-----------
    #check sc3
    diskname = "/home"
    hostname = "e906sc3"
    disk = DoDFCommand( diskname, hostname )
    if not disk:
      self.data.append( StatusDatum( hostname + ":" + diskname, "Disk not found", warning=True ) )
    else:
      available = disk["available"] * 1024
      isProblem = available < 50.
      self.data.append( StatusDatum( hostname + ":" + diskname + " Available", "%.1f G" % available, warning=isProblem ) )

    self.OutputToHTML()
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()



###################
# SlowControl
###################
class SlowControl(StatusChecker):
  """Check that the slowcontrol file is being updated"""
  def __init__(self):
    StatusChecker.__init__(self)

  def Restart(self):
    """Restart the slowcontrol process"""
    KillScreenSession( "read_slowcontrol" )  

  def CheckStatus(self):
    Log( "%s::CheckStatus" % self.__class__.__name__ )
    self.timeOfLastUpdate = int( time.time() )
    self.data = []
    global fileAgeWarnTime

    slowcontrolFilename = "/data2/data/slowcontrol/slowcontrol/slowcontrol_codadata.txt"
    timeSinceLastMod = int( time.time() ) - os.path.getmtime(slowcontrolFilename)
    
    isProblem = timeSinceLastMod > fileAgeWarnTime

    self.data.append( StatusDatum( "Slowcontrol file age", SecondsToTime(timeSinceLastMod), problem=isProblem, email=isProblem ) )

    lines = open(slowcontrolFilename).readlines()
    spillcount = 0
    keithley_good_count = 0
    keithley_bad_count = 0
    for line in lines:
      pieces = line.split()
      if "spillcount" in pieces[1]:
        spillcount = int( pieces[2] )
      if "environment" in pieces[3]:
        kread = float( pieces[2] )
        #print "--------------found ",pieces[1]," = ",kread
        if kread>0:
          keithley_good_count+=1
        else:
          keithley_bad_count+=1
    isProblem = spillcount == 0
    self.data.append( StatusDatum( "Slowcontrol spillID", "%d" % spillcount ) )

    # Keithley is alive and working if we have many good readings, 10 of 18 seems enough
    if keithley_good_count>10:
      self.data.append( StatusDatum( "Keithley Monitor", "%d sensors read" % keithley_good_count ) )
      # Produce warning if a sensor fails
      if keithley_bad_count>0:
         self.data.append( StatusDatum( "Keithley Bad Readings", "%d" % keithley_bad_count , warning=True ) )
        
    else:    # Keithley Problem
      self.data.append( StatusDatum( "Keithley Problem", "%d Good/%d Bad" % (keithley_good_count,keithley_bad_count), warning=True,problem=True ) )
      if DAQUtils.KeithleyIsOK():
        self.data.append( StatusDatum( "Keithley Monitor Pings?", "Yes" ) )
      else:
        self.data.append( StatusDatum( "Keithley Monitor Pings?", "NO", problem=True ) )

    self.OutputToHTML()    
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()


###################
# Spillcounter
###################
class Spillcounter(StatusChecker):
  """Check that the files holding spillcount are being updated"""
  def __init__(self):
    StatusChecker.__init__(self)

  def CheckStatus(self):
    Log( "%s::CheckStatus" % self.__class__.__name__ )
    self.timeOfLastUpdate = int( time.time() )
    self.data = []
    global fileAgeWarnTime

    #get file age
    shouldEmail = False
    local_spillcountAge = self.timeOfLastUpdate - os.path.getmtime(DAQUtils.spillcount_filename)
    isProblem = local_spillcountAge > fileAgeWarnTime
    self.data.append( StatusDatum( "SpillID age", SecondsToTime(local_spillcountAge), problem=isProblem, email=isProblem ) )

    #get spillcounts
    lines = open(DAQUtils.spillcount_filename).readlines()
    local_spillcount = int(lines[0])
    self.data.append( StatusDatum( "Local SpillID", local_spillcount ) )

    #todo: maybe warn if the spillID does not incremement

    self.OutputToHTML()
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()


###################
# Magnet
###################
class Magnet(StatusChecker):
  """Check that the target computer is OK"""
  def __init__(self):
    StatusChecker.__init__(self)
    #after 5 min: send text to Bryan (sprint), Andrew (verizon)
    #after 20 min: send email to Paul and text to Josh (t-mobile)
    self.emailList_5min = [  ]
    self.emailList_20min = [ "reimer@anl.gov"]
    self.emailList_20min.extend( self.emailList_5min )

    #remember last time alarm turned from off to on
    self.timeOfLastAlarmOnset = int( time.time() )
    #remember last time alarm turned from off to on
    self.timeOfLastAlarm      = int( time.time() )
    #remember time of last email
    self.timeOfLastEmail      = int( time.time() )
    #remember if the previous iteration was in alarm
    self.lastCheckInAlarm = False
   

  def CheckStatus(self):
    Log( "%s::CheckStatus" % self.__class__.__name__ )
    self.timeOfLastUpdate = int( time.time() )
    self.data = []
    global fileAgeWarnTime

    fmag = DAQUtils.GetFromACNET( "F:NM3S" )
    if fmag and fmag.has_key("scaled") and fmag.has_key("status"):
      curr = fmag["scaled"]
      status = fmag["status"]
      problem = False
      if not magnets_are_off:
        if curr < fmag_low_current and do_magnet_alarms:
          problem = True
        if status != 0:
          problem = True
          self.data.append( StatusDatum( "FMag Status", status, problem=problem, email=problem ) )
      self.data.append( StatusDatum( "FMag Current", "%.0f"%curr, problem=problem, email=problem ) )
    else:
      self.data.append( StatusDatum( "FMag", "Not Found", problem=True) )

    kmag = DAQUtils.GetFromACNET( "F:NM4AN" )
    if kmag and kmag.has_key("scaled") and kmag.has_key("status"):
      curr = kmag["scaled"]
      status = kmag["status"]
      problem = False
      if not magnets_are_off:
        if curr < kmag_low_current:
          problem = True
        if status != 0:
          problem = True
          self.data.append( StatusDatum( "KMag Status", status, problem=problem, email=problem ) )
      self.data.append( StatusDatum( "KMag Current", "%.0f"%curr, problem=problem, email=problem) )
    else:
      self.data.append( StatusDatum( "KMag", "Not Found", problem=True) )

    ns2sup = DAQUtils.GetFromACNET( "F:NS2SUP" )
    if ns2sup and ns2sup.has_key("scaled") and ns2sup.has_key("status"):
      waterTemp = ns2sup["scaled"]
      status = ns2sup["status"]
      problem = False
      if (waterTemp > 109) :
        problem = True

      self.data.append( StatusDatum( "F:NS2SUP Temp", "%.0f"%waterTemp, problem=problem, email=problem) )
    else:
      self.data.append( StatusDatum( "F:NS2SUP Temp", "Not Found", problem=True) )

    self.OutputToHTML()
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()

###################
# Target
###################
class Target(StatusChecker):
  """Check that the target computer is OK"""
  def __init__(self):
    StatusChecker.__init__(self)
    #after 5 min: send text to Bryan (sprint), Andrew (verizon)
    #after 20 min: send email to Paul and text to Josh (t-mobile)
    self.emailList_5min = [ "5048583136@messaging.sprintpcs.com", "6303101916@vtext.com" ]
    self.emailList_20min = [ "reimer@anl.gov", "2173599817@tmomail.net" ]
    self.emailList_20min.extend( self.emailList_5min )

    #remember last time alarm turned from off to on
    self.timeOfLastAlarmOnset = int( time.time() )
    #remember last time alarm turned from off to on
    self.timeOfLastAlarm      = int( time.time() )
    #remember time of last email
    self.timeOfLastEmail      = int( time.time() )
    #remember if the previous iteration was in alarm
    self.lastCheckInAlarm = False
   

  def CheckStatus(self):
    Log( "%s::CheckStatus" % self.__class__.__name__ )
    self.timeOfLastUpdate = int( time.time() )
    self.data = []
    global fileAgeWarnTime

    #check if the target is in alarm
    DAQUtils.UseTargetEPICS()
    alarmVar = DAQUtils.GetFromEPICS( "TARGET_ALARM_SOUNDING" )
    alarmStatus = "Unknown"
    alarmProblem = True
    if alarmVar == "0":
      alarmStatus = "No"
      alarmProblem = False
    if alarmVar == "1":
      alarmStatus = "Yes"

    #if we are in alarm, then mark the time
    if alarmProblem:
      self.timeOfLastAlarm = int( time.time() )
      #if this is the first alarm for some period, then mark time of onset
      if not self.lastCheckInAlarm:
        self.timeOfLastAlarmOnset = int( time.time() )

    self.lastCheckInAlarm = alarmProblem  

    self.data.append( StatusDatum( "Target Alarm Sounding?", alarmStatus ) )

    ageOfLastAlarm = int(time.time()-self.timeOfLastAlarm)
    self.data.append( StatusDatum( "Time Since Last Alarm", SecondsToTime(ageOfLastAlarm) ) )
    if alarmProblem:
      alarmAge = int(time.time()) - self.timeOfLastAlarmOnset
      timeSinceLastEmail = int(time.time()) - self.timeOfLastEmail
      doEmail = False
      timeToNotify = alarmAge > 5*60
      #send email if alarm is more than 5 minutes old and we haven't sent email in more than 1 min
      if timeToNotify and timeSinceLastEmail > 60:
        self.timeOfLastEmail = int(time.time())
        doEmail = True
        self.emailList = self.emailList_5min
        #get desperate after 20 minutes
        if alarmAge > 20*60:
          self.emailList = self.emailList_20min

      #add these data when target is in alarm        
      self.data.append( StatusDatum( "Age of Current Alarm", SecondsToTime(alarmAge), problem=True, email=doEmail ) )
      self.data.append( StatusDatum( "Experts Notified?", timeToNotify ) )

    #get targpos and targprox
    DAQUtils.UseGatEPICS()
    targpos  = DAQUtils.GetFromEPICS( "TARGPOS" )
    targprox = DAQUtils.GetFromEPICS( "TARGPROX" )
    self.data.append( StatusDatum( "Target Pos. (control)" , GetTargetString(targpos) ) )
    self.data.append( StatusDatum( "Target Pos. (prox. sensor)", GetTargetString(targprox) ) )

    self.OutputToHTML()
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()

###################
# BeamDAQ
###################
class BeamDAQ(StatusChecker):
  """Check that the BeamDAQ is alive and updating"""
  def __init__(self):
    StatusChecker.__init__(self)
    self.alarmName = "beamDAQcrash"

  def CheckStatus(self):
    Log( "%s::CheckStatus" % self.__class__.__name__ )
    self.timeOfLastUpdate = int( time.time() )
    self.data = []
    global fileAgeWarnTime

    #check that E906BeamDAQ is running
    command = ["ssh", "-x", "e906daq@e906beam3", r"""ps -a | egrep 'E906BeamDAQ|RunBeamDAQ'""" ]
    rval, output = DAQUtils.GetOutput( command, timeout=5 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )

    if len(output)==0:
      #check beam2 if not found on beam1
      command = ["ssh", "-x", "e906daq@e906beam2", r"""ps -a | egrep 'E906BeamDAQ|RunBeamDAQ'""" ]
      rval, output = DAQUtils.GetOutput( command, timeout=5 )
      if len(output)>0:
        self.data.append( StatusDatum( "Is E906beamDAQ Running?", "Yes (e906beam2)" ) )
      else:
        self.data.append( StatusDatum( "Is E906BeamDAQ Running?", "NO", problem=True ) )
    else:
      self.data.append( StatusDatum( "Is E906beamDAQ Running?", "Yes (e906beam3)" ) )


    #get BeamDAQ status bits from EPICS and parse to discover problems
    DAQUtils.UseGatEPICS()
    statusCode = DAQUtils.GetFromEPICS( "BEAMDAQ_STATUS" )
    self.data.append( StatusDatum( "Status Code", statusCode ) )
    try:
      statusCode = int( statusCode )
      dutyProblem  = statusCode % 2
      resetProblem = ( ( statusCode - dutyProblem ) / 2 ) % 2
      if dutyProblem:
        self.data.append( StatusDatum( "QIE Duty Factor Problem", "run ResetQIEBoard", problem=True, alarm=True, email=True ) )
      if resetProblem:        self.data.append( StatusDatum( "QIE Register Problem", "run ResetQIEBoard", problem=True, alarm=True, email=True ) )
    except:
      pass

    imgFilename = "/data2/data/beamDAQ/pics/cerenkov_last.png"
    if os.path.isfile(imgFilename):
      timeSinceLastMod = int( time.time() ) - os.path.getmtime(imgFilename)
      isProblem = timeSinceLastMod > fileAgeWarnTime
      self.data.append( StatusDatum( "&#268;erenkov file age", SecondsToTime(timeSinceLastMod), problem=isProblem, email=isProblem, alarm=isProblem ) )


    #get file age
    beamDAQ_spillcountAge = self.timeOfLastUpdate - os.path.getmtime(DAQUtils.spillcount_filename_beamDAQ)
    isProblem = beamDAQ_spillcountAge > fileAgeWarnTime
    self.data.append( StatusDatum( "BeamDAQ SpillID age", SecondsToTime(beamDAQ_spillcountAge), problem=isProblem, email=isProblem, alarm=isProblem ) )

    #get spillcounts
    lines = open(DAQUtils.spillcount_filename).readlines()
    local_spillcount = int(lines[0])

    lines = open(DAQUtils.spillcount_filename_beamDAQ).readlines()
    beamDAQ_spillcount = int(lines[0])
    isProblem = abs( local_spillcount - beamDAQ_spillcount ) > 2
    self.data.append( StatusDatum( "BeamDAQ Last SpillID", beamDAQ_spillcount, problem=isProblem, email=isProblem, alarm=isProblem ) )

    self.OutputToHTML()
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()

###################
# MainDAQ
###################
class MainDAQ(StatusChecker):
  """Check that status of the Main DAQ"""
  def __init__(self):
    StatusChecker.__init__(self)

  def CheckStatus(self):
    Log( "%s::CheckStatus" % self.__class__.__name__ )
    self.timeOfLastUpdate = int( time.time() )
    self.data = []
  
    #--
    #check to see if mainDAQ is alive
    command = ["ssh", "-x", "e906daq@e906daq1", r'ps -a |grep coda_eb_rc3' ]
    rval, output = DAQUtils.GetOutput( command, timeout=5 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    ebDead = len(output)==0

    #if there is no eb then there is (usually) a problem
    if ebDead:
      self.data.append( StatusDatum( "Coda EventBuilder Alive?", "NO", warning=True ) )
    else:
      self.data.append( StatusDatum( "Coda EventBuilder Alive?", "Yes" ) )

    runNumber = None #none means could not get it
    #check to see if mainDAQ is alive
    command = ["ssh", "-x", "e906daq@e906daq1", r'ps -a |grep coda_er_rc3' ]
    rval, output = DAQUtils.GetOutput( command, timeout=5 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    erDead = len(output)==0

    #if there is no eb then there is (usually) a problem
    if erDead:
      self.data.append( StatusDatum( "Coda EventReader Alive?", "NO", warning=True ) )
    else:
      self.data.append( StatusDatum( "Coda EventReader Alive?", "Yes" ) )


    #if eb was found ue plask to get current information in rcGui
    if not ebDead:
      components = {}
      components["ROC2"] = "Not found"
      components["ROC4"] = "Not found"
      components["ROC5"] = "Not found"
      components["ROC6"] = "Not found"
      components["ROC7"] = "Not found"
      components["ROC8"] = "Not found"
      components["ROC9"] = "Not found"
      components["ROC10"] = "Not found"
      components["ROC11"] = "Not found"
      components["ROC12"] = "Not found"
      components["ROC13"] = "Not found"
      components["ROC14"] = "Not found"
      components["ROC15"] = "Not found"
      components["EBe906"] = "Not found"
      components["ERe906"] = "Not found"
      components["TSe906"] = "Not found"

      command = ["ssh", "-x", "e906daq@e906daq1", r'plask -rt Sea2 -all' ]
      rval, output = DAQUtils.GetOutput( command, timeout=5 )
      if rval is None:
        Log("Timed out executing command %s" % str(command) )
      for line in output:
        line = line.strip()
        if len(line)==0:
          continue
        if "Session" in line:
          continue
        elif "Run number" in line:
          val = line.split("=")[1]
          self.data.append( StatusDatum( "Run Number", val ) )
          if val:
            runNumber = int(val)
        elif "Run state" in line:
          val = line.split("=")[1].strip()
          self.data.append( StatusDatum( "Run State", val ) )
        elif "Start time" in line:
          val = line.split("=")[1]
          self.data.append( StatusDatum( "Run Started", val ) )
        elif "End time" in line:
          val = line.split("=")[1]
          self.data.append( StatusDatum( "Run Ended", val ) )
        else:
          if len( line.split() ) != 2:
            Log( "Warning: Coda status line is not a component,state line in mainDAQ: '%s'." % line )
            continue
          component, state = line.split()          
          if component in components.keys():
            components[component] = state

      allOK = True
      for component, state in components.iteritems():
        if not CodaComponentOK(state):
          self.data.append( StatusDatum( component, state, warning=True ) )
          allOK = False
  
      if allOK:
        self.data.append( StatusDatum( "All components OK?", "Yes" ) )

    DAQUtils.UseGatEPICS()
    filesize = DAQUtils.GetFromEPICS( "MAIN_DAQ_FILESIZE" )
    if filesize:
      filesize = float(filesize)
      problem = False
      email = False
      if .96 < filesize:
        problem = True
        if len( eagerShifterList ) > 0 and "sent" not in self.emailList:
          email = True
          self.emailList = eagerShifterList
          self.emailList.append("sent")
      else:
# PER 25 Juy 2015        self.emailList = [ "agrassfish@gmail.com", "arun.tadepalli1@gmail.com", "reimer@anl.gov", "chenyc@fnal.gov" ]
        self.emailList = [ "agrassfish@gmail.com", "arun.tadepalli1@gmail.com", "chenyc@fnal.gov" ]
      self.data.append( StatusDatum( "File Size (GB)", "%.2f" % filesize, warning=problem, email=email ) )
    else:
      self.data.append( StatusDatum( "File Size (GB)", "????", warning=True ) )

    self.OutputToHTML()
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()

###################
# ScalerDAQ
###################
class ScalerDAQ(StatusChecker):
  """Check that status of the Scaler DAQ"""
  def __init__(self):
    StatusChecker.__init__(self)
    self.alarmName = "scalerDAQcrash"
    self.lastCodaOK = int( time.time() )

  def CheckStatus(self):
    Log( "%s::CheckStatus" % self.__class__.__name__ )
    self.timeOfLastUpdate = int( time.time() )
    self.data = []
    global fileAgeWarnTime

    #check to see if scalerDAQ is alive
    command = ["ssh", "-x", "-l", "e906daq", DAQUtils.ScalerDAQ_host, r'ps -a |grep coda_eb_rc3' ]
    rval, output = DAQUtils.GetOutput( command, timeout=5 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    ebDead = len(output)==0

    #this will be false if EB or ER are unresponsive
    #only sound alarm and send email if coda is bad for 125s
    codaOK = True
    soundCodaAlarm = 125 < (int(time.time()) - self.lastCodaOK )
    #if there is no eb then there is a problem
    if ebDead:
      self.data.append( StatusDatum( "Coda EventBuilder Alive?", "NO", warning=True, email=True, alarm=soundCodaAlarm ) )
      codaOK = False
    else:
      self.data.append( StatusDatum( "Coda EventBuilder Alive?", "Yes" ) )

    #check for event reader
    command = ["ssh", "-x", "-l", "e906daq", DAQUtils.ScalerDAQ_host, r'ps -a |grep coda_er_rc3' ]
    rval, output = DAQUtils.GetOutput( command, timeout=5 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    erDead = len(output)==0

    #if there is no eb then there is a problem
    if erDead:
      self.data.append( StatusDatum( "Coda EventReader Alive?", "NO", warning=True, email=True, alarm=soundCodaAlarm ) )
      codaOK = False
    else:
      self.data.append( StatusDatum( "Coda EventReader Alive?", "Yes" ) )

    if codaOK:
      self.lastCodaOK = int( time.time() )

    #if eb was found ue plask to get current information in rcGui
    if not ebDead:
      components = {}
      components["ROC6sc"] = "Not found"
      components["EBe906sc"] = "Not found"
      components["ERe906sc"] = "Not found"

      command = ["ssh", "-x", "-l", "e906daq", DAQUtils.ScalerDAQ_host, r'plask -rt Sea2sc -all' ]
      rval, output = DAQUtils.GetOutput( command, timeout=5 )
      if rval is None:
        Log("Timed out executing command %s" % str(command) )
      for line in output:
        line = line.strip()
        if len(line)==0:
          continue
        if "Session" in line:
          continue
        elif "Run number" in line:
          val = line.split("=")[1]
          self.data.append( StatusDatum( "Run Number", val ) )
        elif "Run state" in line:
          val = line.split("=")[1]
          self.data.append( StatusDatum( "Run State", val ) )
        elif "Start time" in line:
          val = line.split("=")[1]
          self.data.append( StatusDatum( "Run Started", val ) )
          ageInS = GetRunAge(val)
          #if age is more than 1.5hr then we should start a new run
          tooOld = ageInS > 1.5*60*60
          self.data.append( StatusDatum( "Run Age", SecondsToTime(ageInS), warning=tooOld, alarm=tooOld, email=tooOld ) )
        elif "End time" in line:
          val = line.split("=")[1]
          self.data.append( StatusDatum( "Run Ended", val ) )
        else:
          if len( line.split() ) != 2:
            Log( "Warning: Coda status line is not a component,state line in scalerDAQ: '%s'." % line )
            continue
          component, state = line.split()
          if component in components.keys():
            components[component] = state

      allOK = True
      for component, state in components.iteritems():
        if not CodaComponentOK(state):
          self.data.append( StatusDatum( component, state, warning=True ) )
          allOK = False
      if allOK:
        self.data.append( StatusDatum( "All components OK?", "Yes" ) )

    #check that FFT is running too
    command = ["ssh", "-x", "-l", "e906daq", DAQUtils.ScalerFFT_host, r'ps -a |grep E906FFT' ]
    rval, output = DAQUtils.GetOutput( command, timeout=5 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    if len(output)==0:
      self.data.append( StatusDatum( "Is E906FFT Running?", "NO", problem=True) )
    else:
      self.data.append( StatusDatum( "Is E906FFT Running?", "Yes (%s)" % DAQUtils.ScalerFFT_host ) )

    #only issue FFT alarm and email if there was beam
    #for some reason it doesn't do well when there is no beam
    global lastSpillHadBeam    

    imgFilename = "/data2/e906daq/scalerDAQ/E906FFT_last.png" #while debugging /dataA
    if os.path.isfile(imgFilename):
      timeSinceLastMod = int( time.time() ) - os.path.getmtime(imgFilename)
      isProblem = timeSinceLastMod > fileAgeWarnTime
      if lastSpillHadBeam:
        self.data.append( StatusDatum( "Latest FFT image age", SecondsToTime(timeSinceLastMod), problem=isProblem, email=isProblem, alarm=isProblem ) )
      else:
        self.data.append( StatusDatum( "Latest FFT image age", SecondsToTime(timeSinceLastMod), problem=isProblem ) )

    #get file age
    scalerDAQ_spillcountAge = self.timeOfLastUpdate - os.path.getmtime(DAQUtils.spillcount_filename_scalerDAQ)
    isProblem = scalerDAQ_spillcountAge > fileAgeWarnTime
    if lastSpillHadBeam:
      self.data.append( StatusDatum( "ScalerDAQ SpillID age", SecondsToTime(scalerDAQ_spillcountAge), problem=isProblem, email=isProblem, alarm=isProblem ) )
    else:
      self.data.append( StatusDatum( "ScalerDAQ SpillID age", SecondsToTime(scalerDAQ_spillcountAge), problem=isProblem ) )

    #get spillcounts
    local_spillcount = DAQUtils.GetSpillcount( DAQUtils.spillcount_filename )

    scalerDAQ_spillcount = DAQUtils.GetSpillcount( DAQUtils.spillcount_filename_scalerDAQ )
    isProblem = abs( local_spillcount - scalerDAQ_spillcount ) > 2
    isProblem = isProblem and (scalerDAQ_spillcount>0)
    if lastSpillHadBeam:
      self.data.append( StatusDatum( "ScalerDAQ Last SpillID", scalerDAQ_spillcount, problem=isProblem, email=isProblem, alarm=isProblem ) )
    else:
      self.data.append( StatusDatum( "ScalerDAQ Last SpillID", scalerDAQ_spillcount, problem=isProblem  ) )
    
    self.OutputToHTML()
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()

###################
# StatusMonitor
###################
class StatusMonitor(StatusChecker):
  """Check that status of the Scaler DAQ"""
  def __init__(self):
    StatusChecker.__init__(self)

  def CheckStatus(self):
    Log( "%s::CheckStatus" % self.__class__.__name__ )
    self.timeOfLastUpdate = int( time.time() )
    #this one is special, we rely on caller to update data for us
    self.OutputToHTML()


#####################################
##########################
# Start main program here
##########################
#####################################

eosflag = False
bosflag = False
readyForEOS = False
lastSpillHadBeam = False
secondsAtScriptStart = int(time.time())
secondsAtLastBOS = int(time.time())
secondsAtLastEOS = int(time.time())
secondsAtLastBeam = int(time.time())
secondsAtLastGoodEPICS = int(time.time())
secondsAtLastEPICSAlarm = 0 #will be used to limit EPICS warning emails to once per minute

#how many seconds since previous update is bad for files that should update each spill
#will be adjusted to account for time since last spill
fileAgeWarnTimeBuffer = 105
fileAgeWarnTime = fileAgeWarnTimeBuffer

#we will create a new debug file each day
last_daystamp = ""
logfile       = None


#a special checker for the status of this script
statMonChecker = StatusMonitor()

#target will be checked every 3s regardless of spill signals
targetChecker = Target()
magnetChecker = Magnet()
spillCounterChecker = Spillcounter()
slowControlChecker  = SlowControl()
beamDAQChecker      = BeamDAQ()
mainDAQChecker      = MainDAQ()
scalerDAQChecker    = ScalerDAQ()
decoderChecker      = Decoder()
diskChecker         = DiskSpace()
CAENChecker         = CAEN()
#####Turn the DAQ checker off, during shutdown  ### 2015/07/25/// Grass
allCheckers = [ magnetChecker, spillCounterChecker, slowControlChecker, beamDAQChecker, mainDAQChecker, scalerDAQChecker, decoderChecker, diskChecker, CAENChecker]
###allCheckers = [ diskChecker ]

os.environ["EPICS_BASE"] = "/data/epics/base-3.14.12.3"
os.environ["PATH"] = os.environ["PATH"] + ":/data/epics/base-3.14.12.3/bin/linux-x86/"

DAQUtils.UseGatEPICS()
#loop forever
while True:

  #use a new debug file each day
  timenow = datetime.datetime.now()
  daystamp = timenow.strftime( "%Y-%m-%d" )
  if daystamp != last_daystamp:
    last_daystamp = daystamp
    if logfile:
      logfile.close()
    #a new directory each month
    monthstamp = timenow.strftime( "%Y-%m" )
    logdir = os.path.join( logdir_root, monthstamp )
    os.system( "mkdir -p %s" % logdir )
    os.system( "chmod a+r %s" % logdir )
    os.system( "chmod a+w %s" % logdir )
    os.system( "chmod a+x %s" % logdir )
    logfilename = os.path.join( logdir, "status_monitor_%s.log" % daystamp )
    print "using logfile = ",logfilename
    #mode "a" appends if file exists and makes a new one if it doesn't
    logfile = open(logfilename, "a")
    os.system( "chmod a+r %s" % logfilename )
    os.system( "chmod a+w %s" % logfilename )
    Log( "Begin appending to logfile %s" % logfilename )


  secondsSinceScriptStart = int(time.time()) - secondsAtScriptStart
  secondsSinceLastBOS = int(time.time()) - secondsAtLastBOS
  secondsSinceLastEOS = int(time.time()) - secondsAtLastEOS
  secondsSinceLastBeam = int(time.time()) - secondsAtLastBeam

  #look for bos/eos on target EPICS
  time.sleep(1)
  DAQUtils.UseTargetEPICS()
  bosflag = DAQUtils.GetFromEPICS( "BOSFLAG" )
  eosflag = DAQUtils.GetFromEPICS( "EOSFLAG" )
  Log( "BOS = %s, EOS = %s, readyForEOS = %s, seconds since last spill = %d, time = %s" % (bosflag, eosflag, str(readyForEOS), secondsSinceLastBOS, time.ctime() ), debug = True )

  if secondsSinceLastBOS % checkInterval == 1:
    #clear old data
    statMonChecker.data = []
    #check the checkers for problems
    for checker in allCheckers:
      if checker.HasProblems():
        statMonChecker.data.append( StatusDatum( checker.__class__.__name__, "Not OK", problem=True ) )
      elif checker.HasWarnings():
        statMonChecker.data.append( StatusDatum( checker.__class__.__name__, "In Warning", warning=True ) )
        

    #print times
    statMonChecker.data.append( StatusDatum( "Time since this script started", SecondsToTime(secondsSinceScriptStart) ) )
    statMonChecker.data.append( StatusDatum( "Time since last BOS", SecondsToTime(secondsSinceLastBOS) ) )
    statMonChecker.data.append( StatusDatum( "Time since last EOS", SecondsToTime(secondsSinceLastEOS) ) )
    statMonChecker.data.append( StatusDatum( "Time since last Beam", SecondsToTime(secondsSinceLastBeam) ) )

    #if epics returns empty string, then there was an EPICS timeout and there could be a problem with the target computer
    targetEpicsVariable = "ALARM_TARGET_EPICS"
    if not eosflag or not bosflag:
      #send warnings every minute
      #EPICS takes 10s to restart every hour.  Ignore don't send notification for the first 60s of the problem
      sendWarning = False
      secondsSinceLastEPICSProblem = int(time.time()) - secondsAtLastEPICSAlarm
      secondsSinceLastGoodEPICS    = int(time.time()) - secondsAtLastGoodEPICS
      if 60 < secondsSinceLastEPICSProblem and 60 < secondsSinceLastGoodEPICS:
        sendWarning = True
        secondsAtLastEPICSAlarm = int(time.time())
        DAQUtils.UseGatEPICS()
        os.system( "caput %s 1" % targetEpicsVariable )
      statMonChecker.data.append( StatusDatum( "Target Computer", "EPICS Problem", problem=True, alarm=sendWarning, email=sendWarning ) )
    else:
      secondsAtLastGoodEPICS = int( time.time() )
      DAQUtils.UseGatEPICS()
      os.system( "caput %s 0" % targetEpicsVariable )

    #check target status every 3s
    targetChecker.CheckStatus()

    #print to page
    statMonChecker.CheckStatus()
    statMonChecker.SendMailIfNeeded()
    statMonChecker.SetAlarmIfNeeded()
    logfile.flush()
    

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
    acnetVars = DAQUtils.GetFromACNET( ["S:G2SEM"] )
    lastSpillHadBeam = False
    if len(acnetVars) == 1 and "scaled" in acnetVars[0].keys():
      nm3sem = acnetVars[0]["scaled"]
      if nm3sem > 1E10:
        secondsAtLastBeam = int(time.time())
        lastSpillHadBeam = True

    for checker in allCheckers:
      checker.CheckStatus()
    
    #make sure logfile is up to date at this spills end
    logfile.flush()

    if oneShot:
      sys.exit(0)

if logfile:
  logfile.close()
#this is the end of main
