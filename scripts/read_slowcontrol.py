#!/usr/bin/env python
#######################
# read slowcontrol information from:
#     - ACNET (beam)
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
import signal
import subprocess
import multiprocessing as mp
import DAQUtils

############
# Constants
############
logdir_root  =   "/home/e1039daq/e1039_data/slowcontrol_log"
codaFilename =   "/home/e1039daq/e1039_data/slowcontrol_data/slowcontrol_codadata.txt"
list_tsv_dir = [ '/home/e1039daq/e1039_data/slowcontrol_data', '/data2/e1039_data/slowcontrol_data' ]

#how long before we need to be ready for next spill in seconds
#give it an 8s buffer
maxCycleTime = DAQUtils.super_cycle_time - 13

#how many seconds after BOS will we look for EOS
maxTimeBetweenBOSandEOS = 12

#who you gonna call?
#emailList        = [ "knakano@nucl.phys.titech.ac.jp" ] # [ "arun.tadepalli1@gmail.com", "chenyc@fnal.gov", "reimer@anl.gov"]

###########################
# Utility Functions
###########################
def Log( message ):
  """Print message to stdout and logfile."""
  global logfile
  print message
  timestr = datetime.datetime.now().ctime()
  logfile.write( "%s - %s\n" % (timestr, message) )


def RunSubsysFunc(name, func, args):
  """Run the function of one subsystem."""
  time0 = time.time()
  ret, cont = func(args)
  time1 = time.time()
  cont += ("ProcessTime\t%d\t%.1f\t0\n" % (int(time1), time1 - time0))
  name_tsv = "spill_%09d_%s.tsv" % (int(spillId), name)
  dir_ymd  = dati.strftime("slowcontrol_%Y_%m_%d")
  for dir_base in list_tsv_dir:
    #os.makedirs(dir_base + '/' + dir_ymd, exist_ok=True); # Need newer PYTHON version...
    if not os.path.exists(dir_base + '/' + dir_ymd):
      os.makedirs(dir_base + '/' + dir_ymd)
    file_out = open(dir_base + '/' + dir_ymd + '/' + name_tsv, 'w')
    file_out.write(cont)
    file_out.close()

    ## Pathlib is not available on e906-gat6
    #path_out = pathlib.Path(dir_base + '/' + dir_ymd + '/' + name_tsv)
    #path_out.parent.mkdir(parents=True, exist_ok=True)
    #path_out.open(mode='w').write_text(cont)
  exit(ret)


###################################
# Functions that fetch slowcontrol data
###################################

def InsertSpillCount(args):
  """Insert the spill-counter event into MainDAQ & ScalerDAQ."""
  proc = subprocess.Popen(['/data2/e1039/daq/slowcontrols/scripts/insert_spillcount.py'], stdout=subprocess.PIPE)
  cont = proc.communicate()[0];
  return proc.returncode, cont

def GetACNET(args):
  """Get ACNET data, enter some into gat EPICS, and prepare the data for insertion into coda"""
  #Log("Grabbing ACNET data.")
  #these devices will be entered into slowcontrol datastream
  acnetDevices = [ \
      "F:NS2FLO","F:NS2SUP","F:NS2RET","F:NM2V", \
      "F:NM2D1", "F:NM2H", "F:NM3S", "F:NM4AN", \
      "I:BEAM21", "I:VFOUT", \
      "E:M3TGHM", "E:M3TGHS", "E:M3TGVM", "E:M3TGVS", \
      "E:M3TGHI", "E:M3TGHF", "E:M3TGVI", "E:M3TGVF", \
      "E:M3TG2HM", "E:M3TG2HS", "E:M3TG2HI", "E:M3TG2HF", \
      "E:M3TG2VM", "E:M3TG2VS", "E:M3TG2VI", "E:M3TG2VF", \
      "E:M2C2HM",  "E:M2C2HS", "E:M2C2VM", "E:M2C2VS", \
      "E:M2C2HI", "E:M2C2HF", "E:M2C2VI", "E:M2C2VF", \
      "L:CBAR", "S:KTEVTC","F:NM2ION", "F:NM3ION", "F:NM3RST", \
      "F:NM3SEM", "F:NS7DFP", \
      "M:OUTTMP", "F:E906BM", "S:G2SEM", "F:NM3RRT", \
      "G:TURN13", "G:BNCH13", "G:NBSYD", "S:MSEP1U", \
      "S:F1SEM", "F:NM2Q1", "F:NM2Q2", "U:TODB25", \
      "G:RD3161", "G:RD3162", "F:LNM344", "I:FTSDF", \
      "F:MT6SC1", "F:MC7SC1", "F:MC1D", "F:MW1W", \
      "F:NM4LCWFLOW", "F:NM4LCWP1", "F:NM4LCWP2", "F:NM4LCWP3", \
      "F:NM4LCWT1", "F:NM4LCWT2", "F:NM4LCWT3", \
      "G:OUTTMP", "G:HUMID", "G:BPRESS" 
      ]

  #these devices will be entered into EPICS
  #acnetDevicesToEPICS = [ \
  #    "I:FTSDF", "F:NM2ION", "F:NM3ION", "F:NM3RST", \
  #    "G:TURN13", "G:BNCH13", "G:NBSYD", "F:NS2RET", \
  #    "F:NM3S", "F:NM4AN", "S:G2SEM", "S:N2N3EF", \
  #    "F:NS7DFP", "G:RD3161", "G:RD3162", "F:NM3RRT", \
  #    "F:NM3SEM", "F:NS2SUP", "M:OUTTMP"\
  #    ]

  time.sleep(2) # To let the ACNET values up-to-date.

  #Log("Getting from acnet...")
  time0 = int(time.time())
  devl = DAQUtils.GetFromACNET(acnetDevices)

  #Log("Got from acnet...")
  cont = ""
  for dev in devl:
    val = "-9999"
    if dev.has_key("scaled"):
      val = dev["scaled"]
    elif dev.has_key("devicestatus"):
      val = dev["devicestatus"]

    #ensure string rep
    val = str(val)
    cont += dev["name"] + "\t" + str(time0) + "\t" + val + "\t0\n"
  
    #DAQUtils.UseGatEPICS()
    #if dev["name"] in acnetDevicesToEPICS:
    #  #don't use the prefix letter for EPICS variable name
    #  epicsName = dev["name"].split(":")[1]
    #  os.system( "caput %s %s" % (epicsName, val ) )
  ret = 0 # always OK for now
  return ret, cont


def GetHodoHv(args):
  """Get the hodoscope HV status"""
  #Log("Getting the HodoHv info.  Takes ~20 seconds...")
  proc = subprocess.Popen(['cd /data2/e1039/daq/slowcontrols/lecroy/hv && tclsh lecroyHVsc.tcl'], shell=True, stdout=subprocess.PIPE)
  cont = proc.communicate()[0];
  return proc.returncode, cont

def GetDpHodoHv(args):
  """Get the Dark-Photon-hodoscope HV status"""
  proc = subprocess.Popen(["ssh -x pi@192.168.24.180 'cd power_scripts && ./read_power.py'"], shell=True, stdout=subprocess.PIPE)
  cont = proc.communicate()[0];
  return proc.returncode, cont


def GetChamHv(args):
  """Get the slow-control data from the Chamber HV monitor"""
  #Log("Getting the ChamHv info.  Takes ~5 seconds...")
  proc = subprocess.Popen(['/data2/chambers/hvmon_cham/fy2018-sl7/hvmoncham', 'slow'], stdout=subprocess.PIPE)
  cont = proc.communicate()[0];
  return proc.returncode, cont


def GetKeithley(args):
  """Get environmental data from Keithely monitor"""
  #Log("Getting Keithley information.  Takes ~11 seconds...")
  proc = subprocess.Popen('/data2/e1039/daq/slowcontrols/hall_env/kscan', stdout=subprocess.PIPE)
  cont = proc.communicate()[0];
  return proc.returncode, cont


def GetVXTicks(args):
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

  return [ (int(time.time()), "vxticks", vxticks, "DAQ") ]
#end GetVXTicks)


def GetReadSlowCont(list_param):
  """Get the parameters from this script.  Actually this function just concatenates all parameters."""
  output = ""
  for param in list_param:
    output += "\t".join(map(str, param)) + "\n"
  return 0, output

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
  # DAQUtils.UseTargetEPICS()
  bosflag = DAQUtils.GetFromEPICS( "BOS" ) # ( "BOSFLAG" )
  eosflag = DAQUtils.GetFromEPICS( "EOS" ) # ( "EOSFLAG" )
  print "BOS = %s, EOS = %s, readyForEOS = %s, seconds since last spill = %d" % (bosflag, eosflag, str(readyForEOS), secondsSinceLastSpill )

  if bosflag is "1":
    readyForEOS = True
    #Log("Found BOS %d seconds after previous BOS.  Now look for EOS before taking action." % secondsSinceLastSpill )
    secondsAtLastBOS = int(time.time())

  #if we get BOS and no EOS for a while the something is wrong with spill signals, reset spill flags
  timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
  if readyForEOS and maxTimeBetweenBOSandEOS < timeSinceLastBOS:
    readyForEOS = False
    Log("Waited %d seconds after BOS but found no EOS.  Something is wrong with EOS.  Waiting for another BOS." % timeSinceLastBOS )
    

  if readyForEOS and eosflag is "1":
    readyForEOS = False
    nSpillsSeen += 1
    #Log( "Found EOS.  Updating slowcontrol iteration %d." % nSpillsSeen )

    spillId = DAQUtils.GetFromEPICS( "SPILLCOUNTER" )
    dati    = datetime.datetime.now()
    Log("  spill ID = %s." % spillId )

    #get lines of [ timestamp, key, val, type ] from all sources
    #the order matters because several things are racing
    #the target position information takes 3 seconds after EOS before it is reliable
    #vxticks should be read quickly so it is closer to the actual time of the spill

    list_name = [ 'SpillCount'    , 'Acnet' , 'HodoHv' , 'DPhodo' , 'ChamHv' , 'HallEnv'   ]
    list_func = [ InsertSpillCount, GetACNET, GetHodoHv, GetDpHodoHv, GetChamHv, GetKeithley ]
  
    list_proc = []
    for name, func in zip(list_name, list_func):
      proc = mp.Process(name=name, target=RunSubsysFunc, args=(name, func, 0))
      proc.start()
      list_proc.append(proc)

    # Wait until all subsystems finish or the time limit (35 sec).
    utime_wait_max = int(time.time()) + 35
    time.sleep(10)
    while True:
      utime_now = int(time.time())
      #mp.connection.wait((p.sentinel for p in list_proc), timeout=utime_now-utime_wait_max) # Python >= 3.3
      all_finished = True
      for name, proc in zip(list_name, list_proc):
        if proc.is_alive():
          Log("  Alive: %d %d %s" % (utime_now, proc.pid, name))
          all_finished = False
      if all_finished or utime_now > utime_wait_max:
        break
      time.sleep(2)

    utime_now = int(time.time())
    list_param = []
    for name, proc in zip(list_name, list_proc):
      proc_kill = 1 if proc.is_alive() else 0
      if proc_kill:
        Log("  Kill: pid %d, pgid %d" % (proc.pid, os.getpgid(proc.pid)))
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        #os.kill(proc.pid, signal.SIGKILL) # proc.kill() in Python >= 3?
        proc_exit = 0
      else:
        proc_exit = proc.exitcode
      list_param.append( (name+"_Killed", utime_now, proc_kill, 0) )
      list_param.append( (name+"_RetVal", utime_now, proc_exit, 0) )
      #Log("  %s %d %d" % (name, proc_exit, proc_kill))

    timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
    list_param.append( ("TimeSinceLastBOS", utime_now, timeSinceLastBOS, 0) )
    proc_rsc = mp.Process(name='ReadSlowCont', target=RunSubsysFunc, args=('ReadSlowCont', GetReadSlowCont, list_param))
    proc_rsc.start()
    time.sleep(1) # proc_rsc needs at least 1 sec to finish.
    
    ## wait until 5s before cycle is over
    timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
    minInsertTime = maxCycleTime - 10
    while timeSinceLastBOS < minInsertTime:
      timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
      print "Wait to insert slowcontrol event (%d/%d)." % (timeSinceLastBOS, minInsertTime)
      time.sleep(1)

    if proc_rsc.is_alive():
      Log("Kill the process of ReadSlowCont (%d)." % proc_rsc.pid)
      os.kill(proc_rsc.pid, signal.SIGKILL)

    timeSinceLastBOS = int(time.time()) - secondsAtLastBOS
    Log( "All done %ds after BOS" % timeSinceLastBOS )
    logfile.flush()
    #end of what to do at EOS

  #end of forever loop

#end of program
