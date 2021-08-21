import time
import DAQUtils
from StatMonUtils import Log
from StatusChecker import StatusDatum, StatusChecker

###################
# Target
###################
class Target(StatusChecker):
  """Check that the target computer is OK"""
  def __init__(self):
    StatusChecker.__init__(self)
    #after 5 min: send text to Bryan (sprint), Andrew (verizon)
    #after 20 min: send email to Paul and text to Josh (t-mobile)
    self.emailList_5min = [ "5048583136@messaging.sprintpcs.com", "6303101916@vtext.com" ]
    self.emailList_20min = [ "reimer@anl.gov", "2173599817@tmomail.net" ]
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

    #check if the target is in alarm
    DAQUtils.UseTargetEPICS()
    alarmVar = DAQUtils.GetFromEPICS( "TARGET_ALARM_SOUNDING" )
    alarmStatus = "Unknown"
    alarmProblem = True
    if alarmVar == "0":
      alarmStatus = "No"
      alarmProblem = False
    if alarmVar == "1":
      alarmStatus = "Yes"

    #if we are in alarm, then mark the time
    if alarmProblem:
      self.timeOfLastAlarm = int( time.time() )
      #if this is the first alarm for some period, then mark time of onset
      if not self.lastCheckInAlarm:
        self.timeOfLastAlarmOnset = int( time.time() )

    self.lastCheckInAlarm = alarmProblem  

    self.data.append( StatusDatum( "Target Alarm Sounding?", alarmStatus ) )

    ageOfLastAlarm = int(time.time()-self.timeOfLastAlarm)
    self.data.append( StatusDatum( "Time Since Last Alarm", SecondsToTime(ageOfLastAlarm) ) )
    if alarmProblem:
      alarmAge = int(time.time()) - self.timeOfLastAlarmOnset
      timeSinceLastEmail = int(time.time()) - self.timeOfLastEmail
      doEmail = False
      timeToNotify = alarmAge > 5*60
      #send email if alarm is more than 5 minutes old and we haven't sent email in more than 1 min
      if timeToNotify and timeSinceLastEmail > 60:
        self.timeOfLastEmail = int(time.time())
        doEmail = True
        self.emailList = self.emailList_5min
        #get desperate after 20 minutes
        if alarmAge > 20*60:
          self.emailList = self.emailList_20min

      #add these data when target is in alarm        
      self.data.append( StatusDatum( "Age of Current Alarm", SecondsToTime(alarmAge), problem=True, email=doEmail ) )
      self.data.append( StatusDatum( "Experts Notified?", timeToNotify ) )

    #get targpos and targprox
    DAQUtils.UseGatEPICS()
    targpos  = DAQUtils.GetFromEPICS( "TARGPOS" )
    targprox = DAQUtils.GetFromEPICS( "TARGPROX" )
    self.data.append( StatusDatum( "Target Pos. (control)" , 'dummy' ) )
    self.data.append( StatusDatum( "Target Pos. (prox. sensor)", 'dummy' ) )

    self.OutputToHTML()
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()
