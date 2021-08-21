#!/bin/bash
####################################
# Check if the seaquest master loop is running.
# if not, run it in a screen session
# -
# Scroll down to MAIN for the important stuff
# ----------------------------------
# This should run as root user on e906-gat6
# Run this by cron every minute
# ----------------------------------
# PEReimer 28 Oct 2015 changed gat6 to gat6  
# Andrew Chen - chenyc@fanl.gov
# Oct. 20, 2015
####################################


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
  if [ -z "$1" ]; then
    echo "ERROR: Must pass program name as argument to IsRunning().  Return -1."
    return -1
  fi

  #get args
  prog="$1"
  user=${2:-root}

  #how many processes contain the phrase in prog
  #  exclude instances in grep, editor and screen
  nproc=`ps -U $user -u $user ux | grep -v grep | grep -v emacs | grep -v vim | grep -v nano | grep -v SCREEN | grep -c $prog`
  return $nproc
}

###################################
#Start a detached screen session
# Args:
#    $1 = screen session name
#    all others = program and arguments
# Returns:
#    0 = all OK
#    1 = error with arguments
StartScreen() {
  if [ -z "$1" ]; then
    echo "ERROR: Must pass session name as argument to StartScreen.  Return 1."
    return 1
  fi
  session="$1"
  shift #throw away first argument so $@ is now program to run with params
  screen -dmS $session "$@"
  return 0
}

###################################
#Check to see if a process is running
# if it isn't, then start a screen session to run it
# Args:
#   $1 = process name to grep for
#   $2 = user who is running the process
#   $3 = name for screen session
#   all subsequent = program to run with arguments
# Return:
#   0 = all OK
#   1 = arguments problem
StartIfStopped(){
  if [ "$#" -lt "4" ]; then
    echo StartIfStopped required at least 4 arguments.  See in-code documentation.
    return 1
  fi
  searchfor="$1"
  user="$2"
  session="$3"
  shift 3    #now $@ is the program to run with args

  IsRunning $searchfor $user
  nproc=$?
  echo Number of $searchfor processes for $user: $nproc

  rval=0
  if [ "0" -eq "$nproc" ]; then
    echo Starting session $session to run command \'$@\'.
    StartScreen $session "$@"
  elif [ "1" -eq "$nproc" ]; then
    echo Process is already running for command \'$@\'.
  elif [ "1" -lt "$nproc" ]; then
    echo WARNING: Is $nproc too many instances for command \'$@\'.
  else
    echo ERROR: nproc=$nproc. Could not check $searchfor to find processes for command \'$@\'.
    rval=1
  fi
  return $rval
}
#######################
#######################
# MAIN
#######################
#######################

#this script is started by a cronjob so our environment is not setup
#run our login script to get everything ready
source /etc/profile
source /data2/e1039/daq/slowcontrols/scripts/setup_slowcontrols.sh

###
#control variables
###
thisHost=`hostname -s`
session_prefix=$thisHost"-loop" #prefix for screen session names
slowcontrol_scripts=$SLOWCONTROL_ROOT

  
#do the check
program="slowControlMasterLoop.sh"
user="root"     #for now assume all processes run under the same user
session="${session_prefix}.${program}"
echo StartIfStopped $program $user $session $slowcontrol_scripts/scripts/$program
StartIfStopped $program $user $session $slowcontrol_scripts/scripts/$program
