#!/usr/bin/env python
import DAQUtils

runNumber = 4268
command = [ "ssh", "-x", "-l", DAQUtils.MainDAQ_user, DAQUtils.MainDAQ_host, "stat --format='%%s %%Z' /localdata/codadata/run_%06d_spin.dat" % runNumber ]
rval, output = DAQUtils.GetOutput( command, timeout=10 )

print rval
print output

