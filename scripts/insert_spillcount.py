#!/usr/bin/env python3
#######################
# This script reads the spill count (or ID) from EPICS and
# insert it into mainDAQ and scalerDAQ coda stream as event 0x81.
# It was made from "spillcounter.py" on 2021-04-12,
# but it no longer counts up nor saves the spill count for other programs.
#
# This script does not find EOS by itself but executed at EOS by "read_slowcontrol.py".
# It follows the new coverage of one spill ID decided on 2021-Apr-09, namely spill ID is incremented at BOS and covers the spill of that BOS and the following off-spill period.
########################
import os, sys, datetime, time
import DAQUtils

######################
######################
# Main program
######################
######################

##################
# global variables
##################
logdir_root = "/home/e1039daq/e1039_data/insert_spillcount_log"
timenow     = datetime.datetime.now()
timestamp   = timenow.strftime( "%H:%M:%S" )
daystamp    = timenow.strftime( "%Y-%m-%d" )
monthstamp  = timenow.strftime( "%Y-%m" )
logdir      = os.path.join( logdir_root, monthstamp )
os.system( "mkdir -p %s" % logdir )
logfilename = os.path.join( logdir, "insert_spillcount_%s.log" % daystamp )
logfile     = open(logfilename, "a")
#print "Using logfile = ",logfilename

##
## Get EPICS variables
##
DAQUtils.UseGatEPICS()
bosflag    = DAQUtils.GetFromEPICS( "BOS" )
eosflag    = DAQUtils.GetFromEPICS( "EOS" )
spillcount = DAQUtils.GetFromEPICS( "SPILLCOUNTER" )
logfile.write("%s %s: BOS %s, EOS %s, SPILLCOUNT %s\n" % (daystamp, timestamp, bosflag, eosflag, spillcount))

##
## Create a spill-count file
##
spillcountFile = open(DAQUtils.spillcount_filename_insert,"w")
spillcountFile.write( str(spillcount) )
spillcountFile.close()

##
## Insertion to Main DAQ and Scaler DAQ
##
def InsertEvent(user, host, plask_rt, label):
  """Insert the spill-count event to a remote DAQ process.  Return 0 if OK, 1 if not active, 2 if 'ps' failed, 3 if 'plask' failed, 4 if 'fileToEvent' failed."""
  status_insert = 0
  command = ["ssh", "-x", "-l", user, host, r'ps -a |grep coda_eb_rc3' ]
  rval, output = DAQUtils.GetOutput(command, timeout=10)
  if rval is None:
    status_insert = 2
    logfile.write("Timed out executing command %s.\n" % str(command) )
  elif len(output) == 0:
    status_insert = 2
    logfile.write( "Cannot connect to %s.\n" % label )
  else:
    command = ["ssh", "-x", "-l", user, host, r'plask -rt '+plask_rt+' -spState' ]
    rval, output = DAQUtils.GetOutput(command, timeout=10)
    if rval is None:
      status_insert = 3
      logfile.write("Timed out executing command %s.\n" % str(command) )
    elif len(output) != 1:
      status_insert = 3
      logfile.write( "Cannot parse %s state.  Plask output was %s.\n" % (label, str(output)) )
    else:
      state = output[0].strip().lower()
      if state == "active":
        logfile.write( "Insert spillcount into %s.\n" % label )
        insertCodaCommand = r'/data2/e906daq/slowcontrols/scripts/c/fileToEvent %s 129 3' % DAQUtils.spillcount_filename_insert
        command = ["ssh", "-x", "-l", user, host, insertCodaCommand]
        #print "Command:", command
        rval, output = DAQUtils.GetOutput(command, timeout=10)
        if rval is None:
          status_insert = 4
          logfile.write("Timed out executing command %s.\n" % str(command) )
      else:
        status_insert = 1
        logfile.write( "%s exists but its state is '%s'.  Not inserting spillcount.\n" % (label, state) )
  return status_insert

def InsertEventToScalerDAQ(user, host, plask_rt, label):
  """Insert the spill-count event to a remote Scaler-DAQ process.  Return 0 if OK, 1 if not active, 2 if 'ps' failed, 3 if 'plask' failed, 4 if 'fileToEvent' failed."""
  comm_docker = 'docker compose -f ~/e1039-docker-daq/docker-compose.yml exec scalerdaq '
  status_insert = 0
  command = ["ssh", "-x", "-l", user, host, comm_docker + r'ps ax | grep coda_eb_rc3' ]
  rval, output = DAQUtils.GetOutput(command, timeout=10)
  if rval is None:
    status_insert = 2
    logfile.write("Timed out executing command %s.\n" % str(command) )
  elif len(output) == 0:
    status_insert = 2
    logfile.write( "Cannot connect to %s.\n" % label )
  else:
    command = ["ssh", "-x", "-l", user, host, comm_docker + r'/bin/tcsh -c "source dosetupcoda261 ; plask -rt '+plask_rt+' -spState"' ]
    rval, output = DAQUtils.GetOutput(command, timeout=10)
    if rval is None:
      status_insert = 3
      logfile.write("Timed out executing command %s.\n" % str(command) )
    elif len(output) != 1:
      status_insert = 3
      logfile.write( "Cannot parse %s state.  Plask output was %s.\n" % (label, str(output)) )
    else:
      state = output[0].strip().lower()
      if state == "active":
        logfile.write( "Insert spillcount into %s.\n" % label )
        insertCodaCommand = comm_docker + r'/bin/tcsh -c "/data2/e906daq/slowcontrols/scripts/c/fileToEvent %s 129 3"' % DAQUtils.spillcount_filename_insert
        command = ["ssh", "-x", "-l", user, host, insertCodaCommand]
        #print "Command:", command
        rval, output = DAQUtils.GetOutput(command, timeout=10)
        if rval is None:
          status_insert = 4
          logfile.write("Timed out executing command %s.\n" % str(command) )
      else:
        status_insert = 1
        logfile.write( "%s exists but its state is '%s'.  Not inserting spillcount.\n" % (label, state) )
  return status_insert

status_main   = InsertEvent(DAQUtils.MainDAQ_user  , DAQUtils.MainDAQ_host  , "Spin"  , "Main DAQ"  )
status_scaler = InsertEventToScalerDAQ(DAQUtils.ScalerDAQ_user, DAQUtils.ScalerDAQ_host, "Spin2sc", "Scaler DAQ")
#utime_str = str(int(timenow.timestamp())) # Only Python 3
utime_str = str(int((timenow - datetime.datetime(1970,1,1)).total_seconds()))
print("MainDAQ\t"  , utime_str, "\t", str(status_main  ), "\t0")
print("ScalerDAQ\t", utime_str, "\t", str(status_scaler), "\t0")
logfile.write("MainDAQ\t"  + utime_str + "\t" + str(status_main  ) + "\n")
logfile.write("ScalerDAQ\t"+ utime_str + "\t" + str(status_scaler) + "\n")

##
## End
##
if os.path.exists(DAQUtils.spillcount_filename_insert):
  os.remove(DAQUtils.spillcount_filename_insert)
#logfile.write( "Good End.\n" )
logfile.flush()
logfile.close()
