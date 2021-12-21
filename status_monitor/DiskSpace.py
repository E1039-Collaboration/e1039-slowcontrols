import time
import DAQUtils
from StatMonUtils import Log
from StatusChecker import StatusDatum, StatusChecker

###################
# Disk
###################

def DoDFCommand( disk, machine = None, user = None ):
  """Execute df command and organize output.
  You should execute the following command on e1039scrun for each host 
  in order to enable the publickey authentication;
  ssh-copy-id -i ~/.ssh/id_rsa.pub e1039daq@e1039daq1
  """
  KB_TO_TB = 1. / (1024*1024*1024)
  rval = None  # function will return this

  cmd = [ "df", "-P", disk ]
  if machine:
    cmd = ["ssh", "-x", "-o", "PreferredAuthentications=publickey", "-l", user, machine, r'df -P %s' % disk ]

  rcode, output = DAQUtils.GetOutput( cmd, timeout=10 )
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
      percent   = 100 - disk["percent"] 
      isProblem = available < 1.
      self.data.append( StatusDatum( "Available on %s" % diskname, "%.1f T, %d%%" % (available,percent), warning=isProblem ) )

    #-----------
    #check daq1
    diskname = "/localdata"
    hostname = "e1039daq1"
    disk = DoDFCommand( diskname, hostname, "e1039daq" )
    if not disk:
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "Disk not found", warning=True ) )
    else:
      available = disk["available"] * 1024
      percent   = 100 - disk["percent"]
      isWarning = available < 150.
      isProblem = available < 100.
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "%.1f G, %d%%" % (available,percent), warning=isWarning, problem=isProblem ) )

    diskname = "/"
    hostname = "e1039daq1"
    disk = DoDFCommand( diskname, hostname, "e1039daq" )
    if not disk:
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "Disk not found", warning=True ) )
    else:
      available = disk["available"] * 1024
      percent   = 100 - disk["percent"]
      isProblem = available < 20.
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "%.1f G, %d%%" % (available,percent), warning=isProblem ) )

    #-----------
    #check beam3
    diskname = "/"
    hostname = "e1039beam3"
    disk = DoDFCommand( diskname, hostname, "e1039daq" )
    if not disk:
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "Disk not found", warning=True ) )
    else:
      available = disk["available"] * 1024
      percent   = 100 - disk["percent"]
      isProblem = available < 5.
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "%.1f G, %d%%" % (available,percent), warning=isProblem ) )

    diskname = "/home"
    hostname = "e1039beam3"
    disk = DoDFCommand( diskname, hostname, "e1039daq" )
    if not disk:
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "Disk not found", warning=True ) )
    else:
      available = disk["available"] * 1024
      percent   = 100 - disk["percent"]
      isProblem = available < 50.
      self.data.append( StatusDatum( "Available on %s:%s" % (hostname,diskname), "%.1f G, %d%%" % (available,percent), warning=isProblem ) )

    #-----------
    #check sc4
    diskname = "/home"
    hostname = "e1039sc4"
    disk = DoDFCommand( diskname, hostname, "e1039daq" )
    if not disk:
      self.data.append( StatusDatum( hostname + ":" + diskname, "Disk not found", warning=True ) )
    else:
      available = disk["available"] * 1024
      percent   = 100 - disk["percent"]
      isProblem = available < 50.
      self.data.append( StatusDatum( " Available on " + hostname + ":" + diskname, "%.1f G, %d%%" % (available,percent), warning=isProblem ) )

    #-----------
    # Output
    self.OutputToHTML()
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()



