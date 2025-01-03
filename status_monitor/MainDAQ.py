import time
import DAQUtils
from StatMonUtils import Log, CodaComponentOK
from StatusChecker import StatusType, StatusDatum, StatusChecker

###################
# MainDAQ
###################
class MainDAQ(StatusChecker):
  """Check that status of the Main DAQ"""
  def __init__(self):
    StatusChecker.__init__(self)
    self.emailList = [ "liuk.pku@gmail.com", "bhy7tf@virginia.edu" ]
    self.do_email_this = True

  def CheckStatus(self):
    Log( "%s::CheckStatus" % self.__class__.__name__ )
    self.timeOfLastUpdate = int( time.time() )
    self.data = []
  
    #--
    #check to see if mainDAQ is alive
    command = ["ssh", "-x", "-l", DAQUtils.MainDAQ_user, DAQUtils.MainDAQ_host, r'ps -a |grep coda_eb_rc3' ]
    rval, output = DAQUtils.GetOutput( command, timeout=10 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    ebDead = len(output)==0

    #if there is no eb then there is (usually) a problem
    if ebDead:
      self.data.append( StatusDatum( "Coda EventBuilder Alive?", "NO", warning=True ) )
    else:
      self.data.append( StatusDatum( "Coda EventBuilder Alive?", "Yes" ) )

    runNumber = None #none means could not get it
    #check to see if mainDAQ is alive
    command = ["ssh", "-x", "-l", DAQUtils.MainDAQ_user, DAQUtils.MainDAQ_host, r'ps -a |grep coda_er_rc3' ]
    rval, output = DAQUtils.GetOutput( command, timeout=10 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    erDead = len(output)==0

    #if there is no eb then there is (usually) a problem
    if erDead:
      self.data.append( StatusDatum( "Coda EventReader Alive?", "NO", warning=True ) )
    else:
      self.data.append( StatusDatum( "Coda EventReader Alive?", "Yes" ) )


    #if eb was found ue plask to get current information in rcGui
    if not ebDead:
      components = {}
      components["ROC2"] = "Not found"
      components["ROC4"] = "Not found"
      components["ROC5"] = "Not found"
      #components["ROC6"] = "Not found"
      components["ROC7"] = "Not found"
      components["ROC8"] = "Not found"
      components["ROC9"] = "Not found"
      #components["ROC10"] = "Not found"
      components["ROC11"] = "Not found"
      components["ROC12"] = "Not found"
      components["ROC13"] = "Not found"
      #components["ROC14"] = "Not found"
      components["ROC15"] = "Not found"
      components["EBe906"] = "Not found"
      components["ERe906"] = "Not found"
      components["TSe906"] = "Not found"

      run_state = None

      command = ["ssh", "-x", "-l", DAQUtils.MainDAQ_user, DAQUtils.MainDAQ_host, r'plask -rt Spin -all' ]
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
          if val:
            runNumber = int(val)
        elif "Run state" in line:
          val = line.split("=")[1].strip()
          self.data.append( StatusDatum( "Run State", val ) )
          run_state = val
        elif "Start time" in line:
          val = line.split("=")[1]
          self.data.append( StatusDatum( "Run Started", val ) )
        elif "End time" in line:
          val = line.split("=")[1]
          self.data.append( StatusDatum( "Run Ended", val ) )
        else:
          if len( line.split() ) != 2:
            Log( "Warning: Coda status line is not a component,state line in mainDAQ: '%s'." % line )
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

    if runNumber is None:
      self.data.append( StatusDatum( "File Size (GB)", "????", warning=True ) )
    else:
      command = [ "ssh", "-x", "-l", DAQUtils.MainDAQ_user, DAQUtils.MainDAQ_host, "stat --format='%%s %%Z' /localdata/codadata/run_%06d_spin.dat" % runNumber ]
      rval, output = DAQUtils.GetOutput( command, timeout=10 )
      if rval is None:
        Log("Timed out executing command %s" % str(command) )
      values = output[0].split()
      filesize = float(values[0]) / 1024 / 1024 / 1024
      fileage  = time.time() - int(values[1])

      status = StatusType.GOOD
      email  = False
      if filesize > 4.0:
        status = StatusType.WARNING
        email  = True
      self.data.append( StatusDatum( "File Size", "%.1f GB" % filesize, status=status, email=email ) )

      status = StatusType.GOOD
      email  = False
      if run_state == "Running" or run_state == "active":
        if fileage > 50:
          status = StatusType.ERROR
        elif fileage > 10: 
          status = StatusType.WARNING
        #email  = True
        #self.emailList = [ "liuk.pku@gmail.com", "bhy7tf@virginia.edu" ]
        #if len( eagerShifterList ) > 0 and "sent" not in self.emailList:
        #  email = True
        #  self.emailList = eagerShifterList
        #  self.emailList.append("sent")
      self.data.append( StatusDatum( "File Age", "%.1f s" % fileage, status=status, email=email ) )

    self.OutputToHTML()
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()
