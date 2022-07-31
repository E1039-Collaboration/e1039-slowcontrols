####################################
# This file contains utility functions and classes
#  that are useful for DAQ scripts.
#-
# Note: Some import statements are inside of the functions that need them
#       This is because some features will not work on machines that use ancient versions of python
#       but we want to have the other features available there.  Also it's a bit faster for loading.
#-------
# Brian G Tice - tice@anl.gov
# 8/14/2014
####################################
import smtplib, os, time
import threading
import xmlrpclib, socket, httplib
from subprocess import Popen, PIPE
import signal
import multiprocessing as mp

#how long is the accelerator super cycle in seconds
super_cycle_time = 60

#where is the SlowControl part of the repo?
slowcontrol_root = "/data2/e1039/daq/slowcontrols"

#location of spillcount files
spillcount_dir = "/data2/e1039_data/slowcontrol_data/spillcounter/"
spillcount_filename   = os.path.join(spillcount_dir, "local_spillcount.dat")
spillcount_filename_beamDAQ = os.path.join( spillcount_dir, "beamDAQ_lastspill.dat")
spillcount_filename_scalerDAQ = os.path.join(spillcount_dir, "scalerDAQ_lastspill.dat")
spillcount_filename_insert = os.path.join(spillcount_dir, "spillcount_inserted.dat")

#about acnet  
acnet_url       = "https://www-bd.fnal.gov/xmlrpc/Accelerator"
acnet_write_url = "https://www-bd.fnal.gov/xmlrpc/Remote"
acnet_var_file = os.path.join( os.getenv("SLOWCONTROL_ROOT"), "acnet/acnet_variable_list.txt" )

# Host and user names
MainDAQ_user   = "e1039daq"
MainDAQ_host   = "e1039daq1.sq.pri"
ScalerDAQ_user = "e1039daq"
ScalerDAQ_host = "e1039sc4.sq.pri" #machine running ScalerDAQ Coda
ScalerFFT_host = "e1039sc4.sq.pri" #machine running ScalerDAQ FFT
rampCAEN_Host = "e906-gat6.fnal.gov" #machine attached to CAENhv

def GetOutputOld( command, timeout = 1, check_interval = .025 ):
  """Wait for command to finish up to some timeout, then return the status code and output.  Returns (rval, output)."""
  timeUsed = 0  #counts total time since process was spawned
  rval = None   #return code of process
  output = []   #output lines of process

  #start executing and watch for completion
  p = Popen( command, stdout=PIPE, stderr=PIPE, bufsize=0 )
  while timeUsed < timeout:
    #if the process is done p.poll returns something
    rval = p.poll()
    if rval is not None:
      #if the process is done return the output
      output = p.stdout.readlines()
      break
    else:
      #if the process is not done, wait a bit and try again
      timeUsed += check_interval
      time.sleep(check_interval)

  #if there was no return code, then the process did not finish
  if rval is None:
    #kill the process if possible
    try:
      p.kill()
    except Exception, e:
      pass

  return rval, output

def RunCommand(command, pipe_send):
  proc = Popen(command, stdout=PIPE, stderr=PIPE)
  cont = proc.communicate()[0];
  pipe_send.send(cont)
  exit(proc.returncode)

def GetOutput( command, timeout = 1, check_interval = .025 ):
  timeUsed = 0  #counts total time since process was spawned
  rval = None   #return code of process
  output = [""] #output lines of process

  pipe_recv, pipe_send = mp.Pipe(False)
  proc = mp.Process(target=RunCommand, args=(command, pipe_send))
  proc.start()
  while timeUsed < timeout:
    if not proc.is_alive():
      break
    timeUsed += check_interval
    time.sleep(check_interval)

  if proc.is_alive():
    os.kill(proc.pid, signal.SIGKILL) # proc.kill() in Python >= 3?
  else:
    rval = proc.exitcode
    output = pipe_recv.recv().splitlines()

  return rval, output

def UseTargetEPICS():
  """Set environment to use EPICS on the target PC"""
  os.environ["EPICS_CA_AUTO_ADDR_LIST"] = "NO"
  os.environ["EPICS_CA_ADDR_LIST"] = "192.168.24.20"

def UseGatEPICS():
  """Set environment to use EPICS on gateway network (gat6)"""
  os.environ["EPICS_CA_AUTO_ADDR_LIST"] = "NO"
  #os.environ["EPICS_CA_ADDR_LIST"] = "192.168.24.114"
  #os.environ["EPICS_CA_ADDR_LIST"] = "e1039gat1.fnal.gov"
  #os.environ["EPICS_CA_ADDR_LIST"] = "e1039gat1.sq.pri"
  #os.environ["EPICS_CA_ADDR_LIST"] = "192.168.24.71"
  os.environ["EPICS_CA_ADDR_LIST"] = "e1039scrun.sq.pri"

def GetFromEPICS( variable, timeout = 3 ):
  """Get the value of this variable in EPICS"""
  #print "check env %s" % os.environ["EPICS_CA_ADDR_LIST"]
  #rval, out = GetOutput( ["which", "caget"], timeout)
  #print "check env %s" % out
  rval, out = GetOutput( ["caget", "-ts", variable], timeout)
  #print "check env %s" % rval
  #there should only be one line of output
  if len(out) == 1:
    return out[0].strip()
  return ""

def SendMail( recipients, subject, sender = "e1039@fnal.gov", message = "No further message." ):
  """Email experts that there is a bad problem"""
  from email.mime.text import MIMEText
  msg = MIMEText(message)
  msg['To']      = ", ".join(recipients)
  msg['Subject'] = subject
  msg['From']    = sender
  s = smtplib.SMTP('smtp.fnal.gov', 25)
  s.sendmail( sender, recipients, msg.as_string())
  s.quit()

##############
# ACNET
##############
class ProxiedTransport(xmlrpclib.Transport, object):
  """Allows us to use an http proxy"""
  #note: source code copied from https://docs.python.org/2/library/xmlrpclib.html
  def __init__(self):
    #python 2.6+ needs base class init, but such an init does not exist in old old python (which some machines use)
    try:
      xmlrpclib.Transport.__init__(self)
    except:
      pass
    self.proxy = None
  def set_proxy(self, proxy):
    self.proxy = proxy
  def make_connection(self, host):
    self.realhost = host
    if self.proxy:
      h = httplib.HTTP(self.proxy)
    else:
      h = httplib.HTTP(host)
    return h
  def send_request(self, connection, handler, request_body):
    connection.putrequest("POST", 'http://%s%s' % (self.realhost, handler))
  def send_host(self, connection, host):
    connection.putheader('Host', self.realhost)

class ACNETThread( threading.Thread ):
  """Allows us to get information from ACNET server with a timeout.  Use http proxy as requested or needed."""
  def __init__(self, deviceList):
    super(ACNETThread, self).__init__()
    self.deviceList = deviceList
    self.response = []
  def run(self):
    # No proxy connection will be necessary as e1039gat1 was properly 
    # configured on 2019-12-02.  The follow lines will be deleted soon.
    #use http proxy if environmental variable is set or if we are on private network
    #transport = ProxiedTransport()
    #if "http_proxy" in os.environ.keys():
    #  transport.set_proxy( os.getenv("http_proxy") )
    #else:
    #  fqdn = socket.getfqdn()
    #  if "e906" in fqdn and "gat" not in fqdn:
    #    transport.set_proxy( "e906-gat6.fnal.gov:3128" )

    #connect to server and get response
    #server = xmlrpclib.Server( acnet_url, transport=transport )
    server = xmlrpclib.Server( acnet_url )
    self.response = server.getReading( self.deviceList )

class ACNETWriteThread( threading.Thread ):
  """Allows us to write information to ACNET server with a timeout.  Use http proxy as requested or needed."""
  def __init__(self, device, val):
    super(ACNETWriteThread, self).__init__()
    self.device = device
    self.val    = val
    self.response = []
  def run(self):
    # No proxy connection will be necessary as e1039gat1 was properly 
    # configured on 2019-12-02.  The follow lines will be deleted once this version is tested.
    #use http proxy if environmental variable is set or if we are on private network
    #transport = ProxiedTransport()
    #if "http_proxy" in os.environ.keys():
    #  transport.set_proxy( os.getenv("http_proxy") )
    #else:
    #  fqdn = socket.getfqdn()
    #  if "e906" in fqdn and "gat" not in fqdn:
    #    transport.set_proxy( "e906-gat6.fnal.gov:3128" )

    #connect to server and get response
    #server = xmlrpclib.Server( acnet_write_url, transport=transport )
    server = xmlrpclib.Server( acnet_write_url )
    self.response = server.Remote.setting( self.device, self.val )


def GetFromACNET( deviceList, timeout = 10 ):
  """Read information on these devices from ACNET unless the server takes too long"""
  #take timeout of 0 to mean no timeout
  if 0 == timeout:
    tiemeout = None

  #create and start the thread
  t = ACNETThread( deviceList )
  t.start()

  #join the thread with specified timeout
  #note that if timeout=None, we wait forever
  t.join(timeout)

  #if we stopped for timeout, then print a warning
  if timeout and t.isAlive():
    print "WARNING - DAQUtils::GetFromACNET - Request timed out after %(timeout).1fs, got nothing." % locals()

  return t.response

def WriteToACNET( dev, val, timeout = 10 ):
  """Write value for a device to ACNET unless server takes too long"""
  if 0 == timeout:
    timeout = None

  #cast val to float (may throw exception)
  val_float = float(val)

  #create and start the thread
  t = ACNETWriteThread( dev, val_float )
  t.start()

  #join the thread with specified timeout
  #note that if timeout=None, we wait forever
  t.join(timeout)

  #if we stopped for timeout, then print a warning
  if timeout and t.isAlive():
    print "WARNING - DAQUtils::WriteToACNET - Request timed out after %(timeout).1fs, got nothing." % locals()

  return t.response


def KeithleyIsOK():
  """Returns true if we can connect to Keithley monitor.  False otherwise."""
  #status code of 0 indicates success
  keithley_check = [ "ping", "-c 1", "192.168.24.70" ]
  rval, output = GetOutput( keithley_check, timeout = 3 )
  return 0==rval

def GetSpillcount(filename = spillcount_filename, nRetries = 3 ):
  """Read a file and return the spillcount.  If there is a problem, return 0."""
  spillcount = 0
  if os.path.isfile( filename ):
    lines = open(filename).readlines()
    if len(lines) > 0:
      spillcount = int(lines[0])

  #if we didn't get a spillcount, try again if desired
  if spillcount <= 0 and nRetries > 0:
    time.sleep( 0.05 )
    return GetSpillcount( filename, nRetries - 1 )
  else:
    return spillcount
