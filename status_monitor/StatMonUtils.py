import os, datetime, time, subprocess, sys, re

#we will create a new debug file each day
logfile       = None
last_daystamp = ""

# Where should logfiles for this script go
logdir_root = "/home/e1039daq/e1039_data/status_monitor_log" # "/data2/e1039_data/status_monitor/log/"

# Do you want to print debug lines to file?
do_debug = True

#how many seconds since previous update is bad for files that should update each spill
#will be adjusted to account for time since last spill
fileAgeWarnTimeBuffer = 105
fileAgeWarnTime = fileAgeWarnTimeBuffer

lastSpillHadBeam = False

#####################################
##########################
# Utility Functions
##########################
#####################################
def Log( message, debug = False ):
  """Print message to stdout and logfile."""
  global logfile
  global last_daystamp

  timenow = datetime.datetime.now()
  daystamp = timenow.strftime( "%Y-%m-%d" )
  if daystamp != last_daystamp: # Use a new debug file each day
    last_daystamp = daystamp
    if logfile:
      logfile.close()

    #a new directory each month
    monthstamp = timenow.strftime( "%Y-%m" )
    logdir = os.path.join( logdir_root, monthstamp )
    os.system( "mkdir -p %s" % logdir )
    os.system( "chmod a+rwx %s" % logdir )

    logfilename = os.path.join( logdir, "status_monitor_%s.log" % daystamp )
    #mode "a" appends if file exists and makes a new one if it doesn't
    logfile = open(logfilename, "a")
    os.system( "chmod a+rw %s" % logfilename )
    Log( "Begin appending to logfile %s" % logfilename )

  #timestr = datetime.datetime.now().ctime()
  #line = "%s - %s" % (timestr, message)
  line = "%s - %s" % (timenow.ctime(), message)
  print line
  if logfile:
    if (not debug) or (debug and do_debug):
      logfile.write( line + "\n" )

def LogFlush():
  global logfile
  logfile.flush()

def LogClose():
  global logfile
  if logfile:
    logfile.close()

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

