#!/bin/bash
####################################
# Continuously check that certain programs are running
# -
# Runs an infinite loop with periodic checks.
# Check that each process is running.
# If process is not running, 
#   start a screen session to run it
# -
# Scroll down to MAIN for the important stuff
# ----------------------------------
# For extra protection, run a cron to make sure this program is alive
# ----------------------------------
# Brian Tice - tice@anl.gov
# April 10, 2014
# PEReimer 21 October 2019 Modified to take hostname from command and only start those things needed
#                          on that host
# PEReimer 09 January 2020 added -L to screen command to  produce a log file.
####################################

DIR_SCRIPT=$(dirname $(readlink -f $0))

#######################
###########################
# Helper functions
###########################
#######################

###################################
#Grep for a process, return the number of instances running
# Args:
#    $1 = process to grep for [required]
#    $2 = user who runs the process [default=root]
# Return:
#    nonnegative integer = number of instances of that user running that process
#    -1 = argument problem
IsRunning() {
  local prog="$1"
  local user=${2:-root}
  #how many processes contain the phrase in prog
  #  exclude instances in grep, editor and screen
  nproc=`ps aux | grep "^$user" | grep -v grep | grep -v emacs | grep -v vim | grep -v nano | grep -v SCREEN | grep -c $prog`
  return $nproc
}

###################################
#Start a detached screen session
# Args:
#   $1 = program name as a single full path
#   $2 = user who is running the process
StartScreen() {
  local program=$1
  local    user=$2
  local session=$session_prefix.$(basename $program)
  local    comm="screen -L -dmS $session $program"
  echo "$user : $comm"
  su --login --command="$comm" $user 
}

###################################
#Check to see if a process is running
# if it isn't, then start a screen session to run it
# Args:
#   $1 = program name as a single full path
#   $2 = user who is running the process
# Return:
#   0 = all OK
#   1 = arguments problem
#   2 = program not running
StartIfStopped(){
  local program=$1
  local    user=$2
  local bname=$(basename $program)
  IsRunning $program $user
  nproc=$?
  echo Number of $program processes for $user: $nproc

  rval=0
  if [ "0" -eq "$nproc" ]; then
    echo Starting screen to run $bname.
    StartScreen $program $user
  elif [ "1" -eq "$nproc" ]; then
    echo Process is already running for $bname.
  elif [ "1" -lt "$nproc" ]; then
    echo WARNING: Is $nproc too many instances for $bname.
    rval=2
  else
    echo ERROR: nproc=$nproc. Could not check processes of $bname.
    rval=1
  fi
  return $rval
}

###################################
# Handle on subsystem script.
HandleSubsys() {
  local      check=$1 # Could be empty.
  local  prog_full=$2 # Must be a single path (w/o space).
  local       user=${3:-'root'}
  local prog_bname=$(basename $prog_full)
  echo "-------------"
  if [ "$check" = true ]; then
    echo "Checking $prog_bname..."
    StartIfStopped $prog_full $user
    local rval=$?
    if [ $rval -ne 0 ]; then
      allOK=false
      email_message+="Error with program $prog_bname.  Return value of StartIfStopped was $rval.\n"
    fi
  else
    echo "Do not check $prog_bname."
  fi
}

#######################
#######################
# MAIN
#######################
#######################
####
#set environment here
###
#this script is started by a cronjob so our environment is not setup
#run our login script to get everything ready
source /etc/profile
source $DIR_SCRIPT/setup_slowcontrols.sh

###
#control variables
###
thisHost=`hostname -s`
session_prefix=$thisHost"-MasterLoop" #prefix for screen session names

check_period=10 #number of seconds between running the checks

## Switch to check each.  All 'false' by default.
check_slowcontrol=false
check_spillcounter=false
check_epics=false
check_backup=false
check_qie_reset=false
check_magnet_epics=false
check_status_monitor=false
check_fakeEOSBOS=false
if [ "$thisHost" = e1039gat1 ]; then 
  check_epics=true
  check_spillcounter=true
elif [ "$thisHost" = e1039scrun ]; then 
  check_slowcontrol=true
  check_status_monitor=true
fi

email_recipients="reimer@anl.gov"
email_frequency=15*6 #number of checks between sending email for problems (e.g nMinutes*(60/$check_period) )

allOK=true #is everything OK?
nchecks=0  #number of iterations
nchecks_notOK=0 #number of checks that have been bad

#loop forever
while true ; do
  let nchecks=nchecks+1
  echo ====================================
  echo Running check number $nchecks at `date`

  #Reset the error checking variables
  lastOK=$allOK
  allOK=true
  email_message=""

  HandleSubsys "$check_slowcontrol"    "$SLOWCONTROL_ROOT/scripts/read_slowcontrol.py"  "e1039daq"
  HandleSubsys "$check_spillcounter"   "$SLOWCONTROL_ROOT/scripts/spillcounter.py"
  HandleSubsys "$check_epics"          "$SLOWCONTROL_ROOT/epics/startEpics.cmd"
  HandleSubsys "$check_fakeEOSBOS"     "$SLOWCONTROL_ROOT/scripts/fakeEOSBOS.sh"
  HandleSubsys "$check_backup"         "$SLOWCONTROL_ROOT/perl/backup_check.pl"
  HandleSubsys "$check_qie_reset"      "$SLOWCONTROL_ROOT/perl/get_QIE_settings.pl"
  HandleSubsys "$check_magnet_epics"   "$SLOWCONTROL_ROOT/scripts/update_magnet_epics.py"
  HandleSubsys "$check_status_monitor" "$SLOWCONTROL_ROOT/status_monitor/status_monitor.py"  "e1039daq"
  # The code block for "startEpics.cmd" had an extra command;
  # "touch $SLOWCONTROL_ROOT/scripts/$thisHost-check_epics".
  # For simplicity, it should be done in "startEpics.cmd" 
  # or in a wrapper script like "scripts/startEpics.sh".


  #if there was a problem notify DAQ experts
  if [ "$allOK" = false ]; then
    let nchecks_notOK=nchecks_notOK+1
    emailNow=$(( $nchecks_notOK  % $email_frequency ))
    if [ "$emailNow" -eq "1" ]; then
      email_message+="This is check number $nchecks_notOK that has had a problem.\n"
      echo -e "$email_message" | mail -s "SlowControl Master Loop Problem" "$email_recipients"
    fi
  else
    nchecks_notOK=0
  fi

  sleep $check_period
done
