import os
import time
import DAQUtils
from StatMonUtils import Log, SecondsToTime, CodaComponentOK, GetRunAge, fileAgeWarnTime, lastSpillHadBeam
from StatusChecker import StatusDatum, StatusChecker

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
    command = ["ssh", "-x", "-l", DAQUtils.ScalerDAQ_user, DAQUtils.ScalerDAQ_host, r'ps -a |grep coda_eb_rc3' ]
    rval, output = DAQUtils.GetOutput( command, timeout=10 )
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
    command = ["ssh", "-x", "-l", DAQUtils.ScalerDAQ_user, DAQUtils.ScalerDAQ_host, r'ps -a |grep coda_er_rc3' ]
    rval, output = DAQUtils.GetOutput( command, timeout=10 )
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
      components["ROC6sc"  ] = "Not found"
      components["EBe906sc"] = "Not found"
      components["ERe906sc"] = "Not found"

      command = ["ssh", "-x", "-l", DAQUtils.ScalerDAQ_user, DAQUtils.ScalerDAQ_host, r'plask -rt Sea2sc -all' ]
      rval, output = DAQUtils.GetOutput( command, timeout=10 )
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
    command = ["ssh", "-x", "-l", DAQUtils.ScalerDAQ_user, DAQUtils.ScalerFFT_host, r'ps -a |grep E906FFT' ]
    rval, output = DAQUtils.GetOutput( command, timeout=10 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    if len(output)==0:
      self.data.append( StatusDatum( "Is E906FFT Running?", "NO", problem=True) )
    else:
      self.data.append( StatusDatum( "Is E906FFT Running?", "Yes" ) )

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
