import time
import DAQUtils
from StatMonUtils import Log
from StatusChecker import StatusDatum, StatusChecker

magnets_are_off = True
fmag_low_current = 50
kmag_low_current = 50

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
