import time
import DAQUtils
from StatMonUtils import Log
from StatusChecker import StatusDatum, StatusChecker

###################
# Decoder
###################
class Decoder(StatusChecker):
  """Check what the decoders are doing"""
  def __init__(self):
    StatusChecker.__init__(self)

  def CheckStatus(self):
    Log( "%s::CheckStatus" % self.__class__.__name__ )
    self.timeOfLastUpdate = int( time.time() )
    self.data = []

    #-----------------
    #scalerDAQ decoder
    
    #is the daemon running./scalerDecoding
    command = ["ssh", "-x", "-l", "e906daq", DAQUtils.ScalerDAQ_host, 'ps -fu online |grep scalerdaq-decoding-daemon' ]
    rval, output = DAQUtils.GetOutput( command, timeout=10 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )

    if len(output)==0:
      self.data.append( StatusDatum( "Scaler Decoder Daemon", "Dead", problem=True ) )
    else:
      self.data.append( StatusDatum( "Scaler Decoder Daemon", "Alive" ) )
   
    command = ["ssh", "-x", "-l", "e906daq", DAQUtils.ScalerDAQ_host, r'ps -fu online |grep scalerdaq-decoding-daemon' ]
    rval, output = DAQUtils.GetOutput( command, timeout=10 )
    if rval is None:
      Log("Timed out executing command %s" % str(command) )
    scalerRuns = []
    for decoder in output:
      decoder = decoder.strip()
      m = re.search( r'/scaler_(\d+).dat', decoder )
      if m:
        runno = m.group(1)
        scalerRuns.append( runno )

    if len(scalerRuns) > 0:
      self.data.append( StatusDatum( "Decoding Scaler Runs", ",".join(scalerRuns) ) )

    self.OutputToHTML()
    self.SendMailIfNeeded()
    self.SetAlarmIfNeeded()
