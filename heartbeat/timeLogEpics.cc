#define TIMEOUT 10.0

#include <iostream>       // std::cout
#include <iomanip>        // std::put_time
#include <thread>         // std::this_thread::sleep_until
#include <chrono>         // std::chrono::system_clock
#include <ctime>          // std::time_t, std::tm, std::localtime, std::mktime

#include "cadef.h" // epics

int toEpics(int iParVal, chid stchid) {
  int caReturn;
  if (stchid != NULL) {
    if (ca_write_access(stchid) ) {
      caReturn = ca_put(DBR_LONG, stchid, &iParVal);
      printf(" Just finished ca_put, ca_return = %d, iParVal = %d \n", caReturn, iParVal);
      if (caReturn != ECA_NORMAL) {
        printf("ca_put failed: %s", ca_message(caReturn));
        fflush(stdout);
        exit(1);
      }
      caReturn = ca_flush_io();
      if (caReturn != ECA_NORMAL) {
        printf("ca_put failed: %s", ca_message(caReturn));
        fflush(stdout);
        exit(1);
      }
    } else {
      printf (" ca_put failed:  no write access" );
      fflush(stdout);
      exit(1);
    }
  } else {
    printf (" ca_put failed:  chid is null "); 
    fflush(stdout);
    exit(1);
  }
  return caReturn;
}

int initEPICS_CA(chid *TIME5Schid) {
  double timeout = TIMEOUT;
  int caReturn;
  //initialize ca
  ca_preemptive_callback_select caCallBack = ca_disable_preemptive_callback;
  caReturn = ca_context_create (caCallBack);
  if (caReturn != ECA_NORMAL) {
    printf("ca_context_create failed:\n%s\n", ca_message(caReturn)); fflush(stdout);
    exit(1);
  }
  char pvname[30];
  capri priority = CA_PRIORITY_DEFAULT;
  sprintf(pvname, "TIME5S");
  caReturn = ca_create_channel (pvname, NULL, NULL, priority, TIME5Schid);
  if (caReturn != ECA_NORMAL) {
    printf("ca_create_channel failed:\n%s\n", ca_message(caReturn)); fflush(stdout);
    printf("%s\n",pvname); exit(1);
  }

  caReturn = ca_pend_io(timeout);
  if (caReturn != ECA_NORMAL) {
    printf("ca_pend_io failed:\n%s\n", ca_message(caReturn)); fflush(stdout);
    printf(" pvname = %s\n", pvname);
    exit(1);
  }
}

int main() 
{
  chid TIME5Schid;
  initEPICS_CA(&TIME5Schid);

  int delay = 5;
  using std::chrono::system_clock;
  //assign tt the current time from the system clock
  std::time_t tt = system_clock::to_time_t (system_clock::now());

  // change tt into the local time and store in ptm
  struct std::tm *ptm = std::localtime(&tt);

  char buffer [80];

  while (1) {
    int nextTm = (ptm->tm_sec/delay + 1) * delay;
    ptm->tm_sec = nextTm;
    if (ptm->tm_sec >= 60 ) {
      ++ptm->tm_min; ptm->tm_sec=0;
    }
    tt = mktime(ptm);
    std::this_thread::sleep_until (system_clock::from_time_t (tt));
    toEpics(tt, TIME5Schid);
    //char cmd[80];
    //sprintf(cmd, "caput TIME5S %d", tt);
    //printf("%s \n", cmd);
    //std::system(cmd);
    std::strftime(buffer, 80, "%X", ptm);
    std::cout << buffer << " reached! " << tt << std::endl;
  }
  return 0;
}
