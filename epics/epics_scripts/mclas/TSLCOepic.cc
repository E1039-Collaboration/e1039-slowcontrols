#include "TSLCOepic.hh"

#include <iostream>
#include <fstream>
#include <cstdlib>
#include <cmath>
#include <ctime>
#include <iomanip>
#include <csignal>

using std::cout;
using std::endl;

TSLCOepic::TSLCOepic(TSLCOlogs* _log_in){
  InitTSLCOepicMembers();
  log         = _log_in;
  ca_chnl.clear();
  ca_return   = 0;
  ca_timeout  = 15;
  ca_priority = CA_PRIORITY_DEFAULT;
  ca_callback = ca_disable_preemptive_callback;
}

//////////////////////////////////////////////////////////////////////////////////////// 

TSLCOepic::TSLCOepic(){}
TSLCOepic::~TSLCOepic(){CleanUp();}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOepic::ChannelAccessInit(){
  ca_return = ca_context_create(ca_callback);
  if(ca_return != ECA_NORMAL){
    TString msg = "ca_context_create failed";
    log->SendToLog(msg); ChannelAccessError(msg.Data()); cout<<msg<<endl;}
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOepic::ChannelAccessInitVar(mtype &_mv_list){
  mtype::iterator mv_list_it = _mv_list.begin();
  ca_chnl.clear();
  while(mv_list_it != _mv_list.end()){
    ca_return = ca_create_channel(mv_list_it->first.Data(),
				  NULL, NULL, 
				  ca_priority, 
				  &ca_chnl[mv_list_it->first]);
    if(ca_return != ECA_NORMAL){
      TString msg = Form("%s ca_create_channel failed", mv_list_it->first.Data());
      log->SendToLog(msg); ChannelAccessError(msg.Data()); cout<<msg<<endl;}
    mv_list_it++;
  }
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOepic::ChannelAccessPendIO(){
  ca_return = ca_pend_io(ca_timeout);
  if(ca_return != ECA_NORMAL){
    TString msg = "ca_pend_io failed";
    log->SendToLog(msg); ChannelAccessError(msg.Data()); cout<<msg<<endl;}
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOepic::ChannelAccessWrite(mmtype &_mmv_evnt){
  mtype_ca::iterator ca_chnl_it = ca_chnl.begin();
  while(ca_chnl_it != ca_chnl.end()){

    if(!ca_write_access(ca_chnl_it->second)){
      TString msg = Form("%s ca_write_access failed", ca_chnl_it->first.Data());
      log->SendToLog(msg); ChannelAccessError(msg.Data()); cout<<msg<<endl;}
    
    chtype i_chnl_type = ca_field_type(ca_chnl_it->second);

    std::pair<mmtype::iterator, mmtype::iterator> mmv_rcrd;
    mmv_rcrd = _mmv_evnt.equal_range(ca_chnl_it->first);
    Int_t n_rcrds = std::distance(mmv_rcrd.first, mmv_rcrd.second);

    if(n_rcrds==1){//single value per spill

      if(i_chnl_type==6){//double
	dbr_double_t *var = new dbr_double_t[n_rcrds];
	if(GetMMapValues(mmv_rcrd, var) == 1){
	  ca_return = ca_put(i_chnl_type, ca_chnl_it->second, var);}
	delete []var;
      }
      else if(i_chnl_type==0){//string
	dbr_string_t *var = new dbr_string_t[n_rcrds];
	if(GetMMapValues(mmv_rcrd, var) == 1){
	  ca_return = ca_put(i_chnl_type, ca_chnl_it->second, var);}
	delete []var;
      }
      else{//unsupported
	TString msg = Form("unsupported channel type:%ld at ca_put", i_chnl_type);
	log->SendToLog(msg); cout<<msg<<endl;}
      
      if(ca_return != ECA_NORMAL){
	TString msg = Form("%s ca_put failed", ca_chnl_it->first.Data());
	log->SendToLog(msg); ChannelAccessError(msg.Data());	cout<<msg<<endl;}

    }
    else if(n_rcrds>1){//multiple values per spill

      if(i_chnl_type==6){//waveform of doubles
	dbr_double_t *var = new dbr_double_t[n_rcrds];
	if(GetMMapValues(mmv_rcrd, var) == n_rcrds){
	  ca_return = ca_array_put(i_chnl_type, n_rcrds, ca_chnl_it->second, var);}
	delete []var;
      }
      else if(i_chnl_type==0){//waveform of string
	dbr_string_t *var = new dbr_string_t[n_rcrds];
	if(GetMMapValues(mmv_rcrd, var) == n_rcrds){
	  ca_return = ca_array_put(i_chnl_type, n_rcrds, ca_chnl_it->second, var);}
	delete []var;
      }
      else{//unsupported
	TString msg = Form("unsupported channel type:%ld at ca_array_put", i_chnl_type);
	log->SendToLog(msg); cout<<msg<<endl;}

      if(ca_return != ECA_NORMAL){
	TString msg = Form("%s ca_array_put failed", ca_chnl_it->first.Data());
	log->SendToLog(msg); ChannelAccessError(msg.Data());	cout<<msg<<endl;}

    }
    else{
      	TString msg = Form("Key:\"%s\"; wrong number of records:%d ca write", 
			   ca_chnl_it->first.Data(), n_rcrds);
	log->SendToLog(msg); cout<<msg<<endl;}
    
    ca_chnl_it++;
  }
  
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOepic::ChannelAccessFlushIO(){
  ca_return = ca_flush_io();
  if(ca_return != ECA_NORMAL){
    TString msg = "ca_flush_io failed";
    log->SendToLog(msg); ChannelAccessError(msg.Data()); cout<<msg<<endl;}
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOepic::ChannelAccessClearVar(){
  mtype_ca::iterator ca_chnl_it = ca_chnl.begin();
  while(ca_chnl_it != ca_chnl.end()){
    ca_return = ca_clear_channel(ca_chnl_it->second);
    if(ca_return != ECA_NORMAL){
      TString msg = Form("%s ca_clear_channel failed", ca_chnl_it->first.Data());
      log->SendToLog(msg); ChannelAccessError(msg.Data()); cout<<msg<<endl;}
    ca_chnl_it++;
  }
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOepic::ChannelAccessExit(){
  ca_context_destroy();
  /*ca_return = ca_context_destroy();
  if(ca_return != ECA_NORMAL){
    TString msg = "ca_context_destroy failed";
    log->SendToLog(msg); ChannelAccessError(msg.Data()); cout<<msg<<endl;}*/
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOepic::CleanUp(){
  ChannelAccessExit();
  InitTSLCOepicMembers();
}

////////////////////////////////////////////////////////////////////////////////////////

Int_t TSLCOepic::GetMMapValues(mmpair _rcrd, dbr_double_t *_val){
  
  Int_t cc = 0;
  mmtype::iterator mmv_rcrd_it;
  for(mmv_rcrd_it = _rcrd.first; mmv_rcrd_it != _rcrd.second; mmv_rcrd_it++){
    _val[cc] = (dbr_double_t)(mmv_rcrd_it->second.at(2).Atof());
    cc++;
  }
  return cc;
}

////////////////////////////////////////////////////////////////////////////////////////

Int_t TSLCOepic::GetMMapValues(mmpair _rcrd, dbr_string_t *_val){
  Int_t cc = 0;
  mmtype::iterator mmv_rcrd_it;
  for(mmv_rcrd_it = _rcrd.first; mmv_rcrd_it != _rcrd.second; mmv_rcrd_it++){
    for(Int_t i=0;i<sizeof(dbr_string_t);i++){_val[cc][i]='\0';}
    TString tsv_val = mmv_rcrd_it->second.at(2);    
    for(Int_t i=0;i<std::min(sizeof(dbr_string_t),strlen(tsv_val));i++){
      _val[cc][i]=tsv_val[i];
    }
    cc++;
  }
  return cc;
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOepic::ChannelAccessError(TString _mess){
  cout<<_mess<<":"<<endl;
  cout<<ca_message(ca_return)<<endl;
  fflush(stdout);  exit(123456);
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOepic::InitTSLCOepicMembers(){
  ca_chnl.clear();  
  ca_return     = 0;   
  ca_timeout    = 0.;
  ca_priority   = 0;
  ca_callback   = ca_disable_preemptive_callback;

  varlist_dname = "";
  log           = nullptr; 
}

////////////////////////////////////////////////////////////////////////////////////////
