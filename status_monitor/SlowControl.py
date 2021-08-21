import os, time, datetime, glob
#import DAQUtils
from StatMonUtils import Log
from StatusChecker import StatusDatum, StatusChecker

###################
# SlowControl
###################
class SlowControl(StatusChecker):
  """Check that the slowcontrol file is being updated"""
  def __init__(self):
    StatusChecker.__init__(self)

  def Restart(self):
    """Restart the slowcontrol process"""
    KillScreenSession( "read_slowcontrol" )  

  def CheckOneDir(self, path_tsv, time_limit):
    n_file = 0
    for file in glob.glob(path_tsv):
      time_f = os.path.getctime(file)
      if time_f > time_limit :
        n_file += 1
        #print file, time_f
    return n_file

  def CheckStatus(self):
    Log( "%s::CheckStatus" % self.__class__.__name__ )
    self.timeOfLastUpdate = int( time.time() )
    self.data = []

    dir_data = "/data2/e1039_data/slowcontrol_data"

    time_now = time.time()
    dati_now = datetime.datetime.fromtimestamp(time_now)
    path_tsv = "%s/slowcontrol_%04d_%02d_%02d/spill_*.tsv" % (dir_data, dati_now.year, dati_now.month, dati_now.day)
    n_file = self.CheckOneDir(path_tsv, time_now - 120)
    if dati_now.hour == 0 and dati_now.minute == 0:
      dati_m60 = datetime.datetime.fromtimestamp(time_now - 60)
      path_tsv = "%s/slowcontrol_%04d_%02d_%02d/spill_*.tsv" % (dir_data, dati_m60.year, dati_m60.month, dati_m60.day)
      n_file += self.CheckOneDir(path_tsv, time_now - 120)
    
    isProblem = n_file ==  0
    isWarning = n_file != 12

    self.data.append( StatusDatum( "N of TSV files in 2 minutes", n_file, problem=isProblem, warning=isWarning ) )

    self.OutputToHTML()    
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()
