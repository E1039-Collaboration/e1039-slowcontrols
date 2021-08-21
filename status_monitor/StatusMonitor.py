import time
import DAQUtils
from StatMonUtils import Log
from StatusChecker import StatusDatum, StatusChecker

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

