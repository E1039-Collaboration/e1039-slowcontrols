#!/usr/bin/env python
#########################
# Backs up raw files to raid or pnfs
#------------------------
# Brian Tice - tice@anl.gov
# Mar 13, 2015
#########################
import os, sys, optparse, time
import logging, operator
from subprocess import call
from re import search
from hashlib import md5
from uuid import uuid4

#################
#define constants
#################
#units
B_TO_GB = 1. / (1024*1024*1024)
DAY_TO_S = 24*60*60

#constants to control verbosity
kDebug   = "Debug"
kInfo    = "Info"
kWarning = "Warning"
kError   = "Error"

def GetChecksum(filename):
  """Get the md5 checksum on a file"""
  if not os.path.isfile(filename):
    return "0"
  if not os.access( filename, os.R_OK ):
    return "1"

  #files on pnfs cannot be read directory from gat machines, so copy them to tmp home area
  if "/pnfs/e906/data" in filename:
    tmpdir = os.path.join( os.getenv("HOME"), "tmp_checksum" )
    if not os.path.isdir( tmpdir ):
      os.mkdir( tmpdir )
    tmpname = os.path.join( tmpdir, "%s_%s" % (uuid4(), os.path.basename(filename) ) )
    cmd = "dccp %s %s" % ( filename, tmpname )
    os.system(cmd)
    #call checksum on the newly local file
    checksum = GetChecksum(tmpname)
    #remove tmp file if it exists
    if os.path.isfile(tmpname):
      os.remove(tmpname)
    return checksum
  else:
    return md5( open(filename, 'rb').read() ).hexdigest()

#define DataFile class
class DataFile:
  """Knows the filename in raw, raid, pnfs locations.  Knows if file is successfully backed up to pnfs.  Performs backup and removal.  Stores errors."""
  def __init__(self, filename, filepat=r'.*_(\d+).dat', raw_dir=None, raid_dir=None, pnfs_dir=None, logger = None, test = False):
    """Construct the CodaFile object to know all its possible locations"""

    #not sure what to do when handed a filename with no file
    if not os.path.isfile(filename):
      raise Exception( "Cannot create DataFile if file doesn't exist: %s" % filename )

    self.filepat  = filepat  #use pattern for a regular expression to find files, assume one group to get the runnumber
    self.raw_dir  = raw_dir  #root location of raw files
    self.raid_dir = raid_dir #root location of raid copies
    self.pnfs_dir = pnfs_dir #root location of pnfs backups
    self.logger   = logger   #instance of a logger for output
    self.test     = test     #is this a test?  if so, make no actual changes

    #populate filenames
    #replace the value of --outdir in runKTracker.py with PNFS_DIR
    self.orig_file = filename
    self.basename = os.path.basename(filename)
    self.dirname  = os.path.dirname(filename)

    self.raw_file = None
    if self.raw_dir:
      self.raw_file = filename.replace( self.dirname, self.raw_dir )

    self.raid_file = None
    if self.raid_dir:
      self.raid_file = filename.replace( self.dirname, self.raid_dir )

    self.pnfs_file = None
    if self.pnfs_dir:
      self.pnfs_file = filename.replace( self.dirname, self.pnfs_dir )

    #save run number for sorting
    self.run = self.GetRunNumber( )

    #get ready to compile error messages
    self.errors = []

    #store file attributes
    self.orig_size  = os.path.getsize( self.orig_file ) * B_TO_GB
    self.orig_mtime = os.stat( self.orig_file ).st_mtime
    self.raw_size = 0
    self.raw_mtime = 0
    self.raid_size = 0
    self.raid_mtime = 0
    self.pnfs_size  = 0
    self.pnfs_mtime = 0

    #checksums will be used to make sure files are identical before removal
    self.orig_md5 = None
    self.raw_md5 = None
    self.raid_md5 = None
    self.pnfs_md5 = None

    self.is_on_raw = False
    if self.raw_file:
      self.is_on_raw = self.CheckRaw()

    self.is_on_raid = False
    if self.raid_file:
      self.is_on_raid = self.CheckRaid()

    self.is_on_pnfs = False
    if self.pnfs_file:
      self.is_on_pnfs = self.CheckPNFS()

  def __str__(self):
    rval = " ===> " + self.__class__.__name__ + ": " + self.basename + "\n"
    info = []
    info.append( "\tOriginal file: " + self.orig_file )
    if self.raw_file:
      if self.is_on_raw:
        info.append( "raw file: " + self.raw_file )
      else:
        info.append( "Raw file no longer exists" )
    else:
      info.append( "No known raw location for this file." )
    if self.raid_file:
      if self.is_on_raid:
        info.append( "raid file: " + self.raid_file )
      else:
        info.append( "File is not backed up to raid" )
    else:
      info.append( "No known raid location for this file." )
    if self.pnfs_file:
      if self.is_on_pnfs:
        info.append( "PNFS file: " + self.pnfs_file )
      else:
        info.append( "File is not backed up to PNFS" )
    else:
      info.append( "No known PNFS location for this file." )
    info.append( "File size: %.2fG" % self.orig_size )
    if len(self.errors)==0:
      info.append("No Errors")
    else:
      info.append( "Errors: " + " | ".join(self.errors) )
    rval += "; ".join( info )
    return rval

  def Log( self, level, line ):
    """Print the line to stdout or logger utility"""
    if self.logger:
      if level == kDebug:
        self.logger.debug( line )
      elif level == kInfo:
        self.logger.info( line )
      elif level == kWarning:
        self.logger.warning( line )
      elif level == kError:
        self.logger.error( line )
    else:
      print "%s - %s" % ( level, line )

  def GetRunNumber(self):
    """Get the run number from filename using known pattern for filename with one group for the run number"""
    m = search( self.filepat, self.basename )
    if not m or len(m.groups()) != 1:
      return -1
    else:
      return int(m.group(1))

  def CheckRaw(self):
    """check that the raw copy is the same as the original"""
    if os.path.exists( self.raw_file ):
      self.Log( kDebug, "Raw file exists at %s" % self.raw_file )
      #file is on PNFS, but is it really the same file?
      self.raw_size  = os.path.getsize( self.raw_file ) * B_TO_GB
      self.raw_mtime= os.stat( self.raw_file ).st_mtime
      if self.raw_size != self.orig_size:
        self.errors.append("Size mismatch between original and raw copy.")
      return True
    else:
      self.Log( kDebug, "No raw file exists at %s" % self.raw_file )
      return False

  def CheckRaid(self):
    """check that the raid copy is the same as the original"""
    if os.path.exists( self.raid_file ):
      self.Log( kDebug, "Disk backup file exists at %s" % self.raid_file )
      #file is on raid, but is it really the same file?
      self.raid_size  = os.path.getsize( self.raid_file ) * B_TO_GB
      self.raid_mtime= os.stat( self.raid_file ).st_mtime
      if self.raid_size != self.orig_size:
        self.errors.append("Size mismatch between original and raid copy.")
      return True
    else:
      self.Log( kDebug, ("No disk backup file exists at %s" % self.raid_file ) )
      return False

  def CheckPNFS(self):
    """check that the pnfs copy is the same as the original"""
    if os.path.exists( self.pnfs_file ):
      self.Log( kDebug, "Tape backup file exists at %s" % self.pnfs_file )
      #file is on PNFS, but is it really the same file?
      self.pnfs_size  = os.path.getsize( self.pnfs_file ) * B_TO_GB
      self.pnfs_mtime= os.stat( self.pnfs_file ).st_mtime
      if self.pnfs_size != self.orig_size:
        self.errors.append("Size mismatch between original and pnfs copy.")
      return True
    else:
      self.Log( kDebug, "No tape backup file exists at %s" % self.pnfs_file )
      return False

  def CopyToRaid(self, force=False):
    """Copy the original to pnfs and check the result"""
    self.Log( kInfo, "Copy %s to raid." % self.basename )
    if not force and os.path.isfile( self.raid_file ):
      self.errors.append( "You must use 'force' to copy a file to raid if it already exists there" )
      return False
    try:
      if not self.test:
        os.system( "mkdir -p %s" % os.path.dirname( self.raid_file ) )
        cmd = [ "cp", self.orig_file, self.raid_file ]
        rval = call( cmd )
        rval = 0
        if rval != 0:
          self.errors.append( "cp in CopyToRaid bad return value was %d" % rval )
    except Exception, e:
      self.errors.append( "Exception in CopyToRaid: %s" % e )
      return False
    return self.CheckRaid()

  def CopyToPNFS(self, force=False):
    """Copy the original to pnfs and check the result"""
    self.Log( kInfo, "Copy %s to pnfs." % self.basename )
    if not force and os.path.isfile( self.pnfs_file ):
      self.errors.append( "You must use 'force' to copy a file to pnfs if it already exists there" )
      return False
    try:
      if not self.test:
        os.system( "mkdir -p %s" % os.path.dirname( self.pnfs_file ) )
        cmd = [ "dccp", self.orig_file, self.pnfs_file ]
        rval = call( cmd )
        rval = 0
        if rval != 0:
          self.errors.append( "dccp in CopyToPNFS bad return value was %d" % rval )
    except Exception, e:
      self.errors.append( "Exception in CopyToPNFS: %s" % e )
      return False
    return self.CheckPNFS()


  def CanRemoveRaid(self):
    """Is it safe to remove the RAID file?"""
    if not self.raid_file:
      self.Log( kDebug, "No raid file will exist for %s, so no raid file can be removed" % self.basename )
      return False
    if not self.pnfs_file:
      self.Log( kDebug, "No pnfs backup file will exist for %s, so raid file cannot be removed" % self.basename )
      return False
    if not self.is_on_pnfs:
      self.Log( kDebug, "PNFS file not found, cannot remove %s from raid." % self.basename )
      return False
    if len(self.errors) > 0:
      self.Log( kDebug, "PNFS backup for exists for %s but there are errors: %s" % ( self.basename, str(self.errors) ) )
      return False
    self.Log( kDebug, "PNFS backup file found with no problems for raid file %s" % self.basename )
    if not self.RaidChecksumOK():
      self.Log( kDebug, "Not removing raid file %s due to md5 checksum mismatch" % self.basename )
      return False
    return True
      
  def CanRemoveRaw(self):
    """Is it safe to remove the raw file?"""
    if not self.raw_file:
      self.Log( kDebug, "No raw file will exist for %s, so no raw file can be removed" % self.basename )
      return False
    if not self.pnfs_file:
      self.Log( kDebug, "No pnfs backup file will exist for %s, so raw file cannot be removed" % self.basename )
      return False

    if not self.is_on_pnfs:
      self.Log( kDebug, "PNFS file not found, cannot remove %s raw file." % self.basename )
      return False
    if len(self.errors) > 0:
      self.Log( kDebug, "PNFS backup for exists for %s but there are errors: %s" % ( self.basename, str(self.errors) ) )
      return False

    if not self.RawChecksumOK():
      self.Log( kDebug, "Not removing raw file %s due to md5 checksum mismatch" % self.basename )
      return False

    self.Log( kDebug, "PNFS backup file found with no problems for raw file %s" % self.basename )
    return True
      

  def CalculateChecksums(self):
    """Calculate checksum (if needed) for all known files and look for errors"""
    if self.orig_md5 is None:
      self.orig_md5 = GetChecksum( self.orig_file )
   
    if self.raw_md5 is None and self.is_on_raw:
      self.raw_md5 = GetChecksum( self.raw_file )
      if self.raw_md5 != self.orig_md5:
        self.errors.append( "Checksum mismatch between raw and original files" )
   
    if self.raid_md5 is None and self.is_on_raid:
      self.raid_md5 = GetChecksum( self.raid_file )
      if self.raid_md5 != self.orig_md5:
        self.errors.append( "Checksum mismatch between raid and original files" )

    if self.pnfs_md5 is None and self.is_on_pnfs:
      self.pnfs_md5 = GetChecksum( self.pnfs_file )
      if self.pnfs_md5 != self.orig_md5:
        self.errors.append( "Checksum mismatch between pnfs and original files" )

    self.Log( kDebug, "Checksums orig/raw/raid/pnfs = %s/%s/%s/%s" % (self.orig_md5, self.raw_md5, self.raid_md5, self.pnfs_md5) )


  def RawChecksumOK(self):
    """Do the checksums of backups match the raw file?"""
    self.CalculateChecksums()
    if self.orig_md5 != self.raw_md5:
      return False
    if self.orig_md5 != self.pnfs_md5:
      return False
    return True

  def RaidChecksumOK(self):
    """Do the checksums of backups match the raid file?"""
    self.CalculateChecksums()
    if self.orig_md5 != self.raid_md5:
      return False
    if self.orig_md5 != self.pnfs_md5:
      return False
    return True

###################
#inheriting classes
###################
class MainDAQDataFile( DataFile ):
  """Instance of DataFile with MainDAQ coda file locations"""
  def __init__(self, filename, logger = None, test = False):
    DataFile.__init__(self, \
        filename=filename,\
        raw_dir = "/codadata",\
        filepat=r'run_(\d{8}).dat',\
        raid_dir = "/seaquest/data/mainDAQ",\
        pnfs_dir = "/pnfs/e906/data/mainDAQ",\
        logger=logger, test=test)

class ScalerDAQDataFile( DataFile ):
  """Instance of DataFile with ScalerDAQ coda file locations"""
  def __init__(self, filename, logger = None, test = False):
    DataFile.__init__(self, \
        filename=filename,\
        filepat=r'scaler_(\d+).dat',\
        raw_dir = "/scaler_data_sc3/codadata",\
        raid_dir = "/seaquest/data/scalerDAQ",\
        pnfs_dir = "/pnfs/e906/data/scalerDAQ",\
        logger=logger, test=test)




