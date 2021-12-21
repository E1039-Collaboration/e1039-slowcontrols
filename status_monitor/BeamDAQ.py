import os
import time
import DAQUtils
from StatMonUtils import Log, SecondsToTime, fileAgeWarnTime
from StatusChecker import StatusDatum, StatusChecker

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
    command = ["ssh", "-x", "e1039daq@e1039beam3", r"""ps a | egrep 'E906BeamDAQ|RunBeamDAQ'""" ]
    rval, output = DAQUtils.GetOutput( command, timeout=10 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    if len(output)==0:
      self.data.append( StatusDatum( "Is E906BeamDAQ Running?", "NO", problem=True ) )
    else:
      self.data.append( StatusDatum( "Is E906beamDAQ Running?", "Yes" ) )

    #if len(output)==0:
    #  #check beam2 if not found on beam1
    #  command = ["ssh", "-x", "e1039daq@e1039beam2", r"""ps -a | egrep 'E906BeamDAQ|RunBeamDAQ'""" ]
    #  rval, output = DAQUtils.GetOutput( command, timeout=10 )
    #  if len(output)>0:
    #    self.data.append( StatusDatum( "Is E906beamDAQ Running?", "Yes (e906beam2)" ) )
    #  else:
    #    self.data.append( StatusDatum( "Is E906BeamDAQ Running?", "NO", problem=True ) )
    #else:
    #  self.data.append( StatusDatum( "Is E906beamDAQ Running?", "Yes (e1039beam3)" ) )


    #get BeamDAQ status bits from EPICS and parse to discover problems
    #DAQUtils.UseGatEPICS()
    statusCode = DAQUtils.GetFromEPICS( "BEAMDAQ_STATUS" )
    self.data.append( StatusDatum( "Status Code", statusCode ) )
    try:
      statusCode = int( statusCode )
      dutyProblem  = statusCode % 2
      resetProblem = ( ( statusCode - dutyProblem ) / 2 ) % 2
      if dutyProblem:
        self.data.append( StatusDatum( "QIE Duty Factor Problem", "run ResetQIEBoard", problem=True, alarm=True, email=True ) )
      if resetProblem:
        self.data.append( StatusDatum( "QIE Register Problem", "run ResetQIEBoard", problem=True, alarm=True, email=True ) )
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
    #lines = open(DAQUtils.spillcount_filename).readlines()
    #local_spillcount = int(lines[0])
    #lines = open(DAQUtils.spillcount_filename_beamDAQ).readlines()
    #beamDAQ_spillcount = int(lines[0])
    #isProblem = abs( local_spillcount - beamDAQ_spillcount ) > 2
    #self.data.append( StatusDatum( "BeamDAQ Last SpillID", beamDAQ_spillcount, problem=isProblem, email=isProblem, alarm=isProblem ) )

    self.OutputToHTML()
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()
