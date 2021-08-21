#!/usr/bin/python
import time, os
from datetime import datetime
import DAQUtils

#setup EPICS
os.environ["EPICS_BASE"] = "/data/epics/base-3.14.12.3"
os.environ["PATH"] = os.environ["PATH"] + ":/data/epics/base-3.14.12.3/bin/linux-x86/"
DAQUtils.UseGatEPICS()

#list the acnet devices we want
devicelist = ["F:NM3S","F:NM4AN"] #magnet current
devicelist.extend( ["F:NS2RET", "F:NM3RRT",] ) #magnet water temp
devicelist.extend( ["F:NS7DFP"] )  #magnet water pressure

#define how often we want to fetch acnet and update epics
updateInterval = 3

while True:
  print datetime.now()
  acnetInfo = DAQUtils.GetFromACNET( devicelist )
  for dev in acnetInfo:
    val = "-9999"
    if dev.has_key("scaled"):
      val = dev["scaled"]
    elif dev.has_key("devicestatus"):
      val = dev["devicestatus"]
    else:
      print "WARNING - Cannot handle acnet variable",dev["name"]
      continue
    epicsName = dev["name"].split(":")[1]
    os.system( "caput %s %s" % (epicsName, val ) )
    #broadcast FMag/KMag current also to target machine as simply fmag/kmag
    if dev["name"] == "F:NM3S":
      DAQUtils.UseTargetEPICS()
      os.system( "caput fmag %s" % val )
      DAQUtils.UseGatEPICS()
    if dev["name"] == "F:NM4AN":
      DAQUtils.UseTargetEPICS()
      os.system( "caput kmag %s" % val )
      DAQUtils.UseGatEPICS()

  time.sleep(updateInterval)
