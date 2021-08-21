import os, time
import DAQUtils
from StatMonUtils import fileAgeWarnTime, Log, SecondsToTime
from StatusChecker import StatusDatum, StatusChecker

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
