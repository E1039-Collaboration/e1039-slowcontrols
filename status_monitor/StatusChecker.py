import os, datetime, time, subprocess, sys, re
from StatMonUtils import Log
import DAQUtils

#where to write output html stuff - for normal operation
statusDir = "/data2/e1039_data/status_monitor/html" # "/dev/shm/SpinQuestDAQStatus"

alarmDir = "/data2/e1039_data/status_monitor/alarm"

#do you want target alarms and email?
do_alarms = True
do_email = True ## True or False.  Set to 'False' in case of no beam for example.

######################
# StatusType
######################
class StatusType:
  GOOD = "good"
  WARNING = "warning"
  PROBLEM = "problem"

######################
# StatusDatum
######################
class StatusDatum:
  """A specific item checked during status check"""
  def __init__(self, name, value, status = StatusType.GOOD, alarm = False, email = False, problem = None, warning = None ):
    self.name   = name
    self.value  = value
    self.status = status #status of this datum (e.g. is it a problem?)
    self.alarm  = alarm  #boolean to indicate if there should be an uh-oh target computer alarm
    self.email  = email   #boolean to indicate if there an email should be sent to expert

    #if warning or problem are given explicitly, use them
    if warning:
      self.status = StatusType.WARNING
    if problem:
      self.status = StatusType.PROBLEM

  def __str__(self):
    """String representation"""
    rval = "%s = %s, status=%s, InAlarm=%s, InEmail=%s" % (self.name, self.value, self.status, self.alarm, self.email)
    return rval

#########################
# StatusChecker
#########################
class StatusChecker:
  """Base class for checking the status of DAQ-related systems."""
  def __init__(self):

    self.data = []           # a list of StatusDatum
    self.pageHeader = self.__class__.__name__ + " Status" #what to write above the data for this subsytem on the webpage
    self.outputFile = os.path.join( statusDir, self.__class__.__name__ + "_Status.html" ) #where to output html status
    self.timeOfLastUpdate = int( time.time() )
    self.alarmName = None #none means there is no alarm
    self.emailList = [ "bhy7tf@virginia.edu" ]
    self.email_interval = 12*3600 # in seconds
    self.do_email_this = False

    self.inAlarm   = False #remember if we are in alarm state

  def CheckStatus(self):
    """Pure virtual function to check the status.  Must be defined in inheriting classes."""
    raise Exception( "Check Status is not defined for class " + self.__class__.__name__ )

  def HasProblems(self):
    """Returns true if at least one datum says there is a problem"""
    for datum in self.data:
      if datum.status == StatusType.PROBLEM:
        return True
    return False

  def HasWarnings(self):
    """Returns true if at least one datum says there is a warning"""
    for datum in self.data:
      if datum.status == StatusType.WARNING:
        return True
    return False

  def GetLastAlarmTime(self):
    filename = alarmDir + '/' + self.__class__.__name__ + '.timestamp'
    if os.path.exists(filename):
        return os.path.getmtime(filename)
    else:
        return 0

  def SetLastAlarmTime(self):
    if not os.path.exists(alarmDir):
        os.system( "mkdir -p %s" % alarmDir )
    filename = alarmDir + '/' + self.__class__.__name__ + '.timestamp'
    if os.path.exists(filename):
        os.utime(filename, None)
    else:
        open(filename, 'a').close()

  def SetAlarmIfNeeded(self):
    """Returns true if at least one datum says there should be an alarm and set the alarm.  Turn off alarm if everything is fine."""
    if not self.alarmName:
      return False
    if not do_alarms:
      return False

    #look for data that are in alarm mode
    for datum in self.data:
      if datum.alarm:
        #DAQUtils.UseTargetEPICS()
        os.system( "caput %s 1" % self.alarmName )
        Log( "Issuing alarm %s. For datum: %s" % (self.alarmName, str(datum) ) )
        self.inAlarm = True
        return True
    
    #there should not be an alarm, turn it off if it is on
    if self.inAlarm:
      #DAQUtils.UseTargetEPICS()
      os.system( "caput %s 0" % self.alarmName )
      Log( "Turning off alarm %s." % self.alarmName)
     
    self.inAlarm = False
    return False

  def SendMailIfNeeded(self):
    """Email the experts if necessary"""
    #loop for data saying we should email
    if not do_email and not do_email_this:
      return False

    emailLines = []    
    emailNeeded = False
    for datum in self.data:
      emailLines.append( str(datum) )
      if datum.email:
        emailNeeded = True

    #if data has email, then send the email
    if emailNeeded and time.time() - self.GetLastAlarmTime() > self.email_interval:
      subject = "%s Problem" % self.__class__.__name__
      message = "\n\n".join(emailLines)
      DAQUtils.SendMail( self.emailList, subject, message=message )
      Log( "Sending email to %s for problem in %s" % (str(self.emailList), self.__class__.__name__ ) )
      self.SetLastAlarmTime()

  def OutputToHTML(self):
    """Write the status information to HTML."""
    Log( "%s::OutputToHTML" % self.__class__.__name__ )
    lines = []

    if self.HasProblems():
      lines.append( "<span class='header problem'>%s</span>" % self.pageHeader )
    elif self.HasWarnings():
      lines.append( "<span class='header warning'>%s</span>" % self.pageHeader )
    else:
      lines.append( "<span class='header'>%s</span>" % self.pageHeader )

    lines.append("<br />")
    lines.append( "Last Updated: " + datetime.datetime.fromtimestamp( self.timeOfLastUpdate ).strftime('%Y-%m-%d %H:%M:%S') )

    lines.append( "<table>" )
    for datum in self.data:
      if datum.status == StatusType.PROBLEM:
        lines.append( "<tr class='problem'>" )
      elif datum.status == StatusType.WARNING:
        lines.append( "<tr class='warning'>" )
      else:
        lines.append( "<tr>" )
      lines.append( "<td> %s </td>" % datum.name )
      lines.append( "<td> %s </td>" % datum.value )
      lines.append( "</tr>" )
    lines.append("</table>")

    #add newline
    lines = [ line + "\n" for line in lines ]

    fout = open(self.outputFile, "w")
    fout.writelines( lines )
    fout.close()
