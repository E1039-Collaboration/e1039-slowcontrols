#include "TEPICcnfg.hh"

#include <iostream>
#include <fstream>
#include <cstdlib>
#include <cmath>
#include <ctime>
#include <iomanip>
#include <csignal>

using std::cout;
using std::endl;

TEPICcnfg::TEPICcnfg(TSLCOlogs* _log_in){
  InitTEPICcnfgMembers();
  log         = _log_in;
  ca_return   = 0;
  ca_callback = ca_disable_preemptive_callback;
}

//////////////////////////////////////////////////////////////////////////////////////// 

TEPICcnfg::TEPICcnfg(){}
TEPICcnfg::~TEPICcnfg(){CleanUp();}

////////////////////////////////////////////////////////////////////////////////////////

void TEPICcnfg::ChannelAccessInit(){
  ca_return = ca_context_create(ca_callback);
  if(ca_return != ECA_NORMAL){
    TString msg = "ca_context_create failed";
    log->SendToLog(msg); ChannelAccessError(msg.Data()); cout<<msg<<endl;}
}

////////////////////////////////////////////////////////////////////////////////////////

void TEPICcnfg::ChannelAccessExit(){ca_context_destroy();}

////////////////////////////////////////////////////////////////////////////////////////

void TEPICcnfg::CleanUp(){
  ChannelAccessExit();
  TString msg = "TEPICcnfg cleaning and exiting";
  log->SendToLog(msg); cout<<msg<<endl;
  InitTEPICcnfgMembers();
}

////////////////////////////////////////////////////////////////////////////////////////

void TEPICcnfg::ChannelAccessError(TString _mess){
  cout<<_mess<<":"<<endl;
  cout<<ca_message(ca_return)<<endl;
  fflush(stdout);  exit(123456);
}

////////////////////////////////////////////////////////////////////////////////////////

void TEPICcnfg::InitTEPICcnfgMembers(){
  ca_return     = 0;   
  ca_callback   = ca_disable_preemptive_callback;
  log           = nullptr; 
}

////////////////////////////////////////////////////////////////////////////////////////
