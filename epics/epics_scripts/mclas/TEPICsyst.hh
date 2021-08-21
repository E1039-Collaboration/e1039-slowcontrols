#ifndef TEPICsyst_hh 
#define TEPICsyst_hh

#include <TFile.h>
#include <TTree.h>
#include <TString.h>
#include <map>

#include "cadef.h"
#include "TSLCOlogs.hh"

class TEPICsyst{

public :

  typedef std::map<TString, chid>                           mtype_ca;
  typedef std::map<TString, std::vector<TString>>           mtype;
  typedef std::multimap<TString, std::vector<TString>>      mmtype;
  typedef std::pair<mmtype::iterator, mmtype::iterator>     mmpair;
 
  TEPICsyst(TSLCOlogs* _log_in, TString _sysn); 
  TEPICsyst();
  ~TEPICsyst();
 
  void                          ChannelAccessInitVar(mtype &_mv_list);
  void                          ChannelAccessPendIO();
  Double_t                      ChannelAccessReadDoublesOnly(TString _key);
  void                          ChannelAccessWrite(mmtype &_mmv_evnt);
  void                          ChannelAccessFlushIO();
  void                          ChannelAccessClearVar();

  void                          CleanUp();

  TString                       sys_name;

protected:
  
private:

  mtype_ca                      ca_chnl;  
  Int_t                         ca_return;   
  Double_t                      ca_timeout;
  capri                         ca_priority;

  TString                       varlist_dname;
  TSLCOlogs                    *log; 

  Int_t                         GetMMapValues(mmpair _rcrd, dbr_double_t *_val);
  Int_t                         GetMMapValues(mmpair _rcrd, dbr_string_t *_val);

  void                          ChannelAccessError(TString _mess);

  void                          InitTEPICsystMembers();
};
#endif

