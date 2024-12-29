#ifndef TEPICcnfg_hh 
#define TEPICcnfg_hh

#include <TFile.h>
#include <TTree.h>
#include <TString.h>
#include <map>

#include "cadef.h"
#include "TSLCOlogs.hh"

class TEPICcnfg{

public :
 
  TEPICcnfg(TSLCOlogs* _log_in); 
  TEPICcnfg();
  ~TEPICcnfg();
 
  void                          ChannelAccessInit();
  void                          ChannelAccessExit();

  void                          CleanUp();

protected:
  
private:

  Int_t                         ca_return;   
  ca_preemptive_callback_select ca_callback;

  TSLCOlogs                    *log; 

  void                          ChannelAccessError(TString _mess);
  void                          InitTEPICcnfgMembers();
};
#endif

