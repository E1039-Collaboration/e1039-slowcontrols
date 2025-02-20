#include "TEPICsyst.hh"

#include <iostream>
#include <fstream>
#include <cstdlib>
#include <cmath>
#include <ctime>
#include <iomanip>
#include <csignal>

using std::cout;
using std::endl;

TEPICsyst::TEPICsyst(TSLCOlogs* _log_in, TString _sysn){
  InitTEPICsystMembers();
  log         = _log_in;
  sys_name    = _sysn;
  ca_chnl.clear();
  ca_return   = 0;
  ca_timeout  = 15;
  ca_priority = CA_PRIORITY_DEFAULT;
  cout<<"INIT "<<sys_name<<endl;
  log->SendToLog("INIT");
}

//////////////////////////////////////////////////////////////////////////////////////// 

TEPICsyst::TEPICsyst(){}
TEPICsyst::~TEPICsyst(){CleanUp();}

////////////////////////////////////////////////////////////////////////////////////////

void TEPICsyst::ChannelAccessInitVar(mtype &_mv_list){
  mtype::iterator mv_list_it = _mv_list.begin();
  ca_chnl.clear();
  while(mv_list_it != _mv_list.end()){
    ca_return = ca_create_channel(mv_list_it->first.Data(),
				  NULL, NULL, 
				  ca_priority, 
				  &ca_chnl[mv_list_it->first]);
    //cout<<"CA "<<mv_list_it->first<<" "<<ca_return<<endl;
    log->SendToLog(Form("CA %s, %s",sys_name.Data(),mv_list_it->first.Data())); 
    if(ca_return != ECA_NORMAL){
      TString msg = Form("Sys:%s; %s ca_create_channel failed",
			 sys_name.Data(), mv_list_it->first.Data());
      log->SendToLog(msg); cout<<msg<<endl; ChannelAccessError(msg.Data());}
    mv_list_it++;
  }
}

////////////////////////////////////////////////////////////////////////////////////////

void TEPICsyst::ChannelAccessPendIO(){
  ca_return = ca_pend_io(ca_timeout);
  if(ca_return != ECA_NORMAL){
    TString msg = Form("Sys:%s; ca_pend_io failed",sys_name.Data());
    log->SendToLog(msg); cout<<msg<<endl; ChannelAccessError(msg.Data());}
}

////////////////////////////////////////////////////////////////////////////////////////

Double_t TEPICsyst::ChannelAccessReadDoublesOnly(TString _key){
  Double_t res =0.;
  mtype_ca::iterator ca_chnl_it = ca_chnl.find(_key);
  if(ca_chnl_it != ca_chnl.end()){
    chtype i_chnl_type = ca_field_type(ca_chnl_it->second);
    ca_return = ca_get(i_chnl_type, ca_chnl_it->second, &res);
    if(ca_return != ECA_NORMAL){
      TString msg = Form("Sys:%s; %s ca_get failed",
			 sys_name.Data(), ca_chnl_it->first.Data());
      log->SendToLog(msg); cout<<msg<<endl;}
    ChannelAccessPendIO();
  }
  else{
    TString msg = Form("Sys:%s; no Key:\"%s\"; ca read failed",
		       sys_name.Data(), _key.Data());
    log->SendToLog(msg); cout<<msg<<endl;}

  return res;
}

////////////////////////////////////////////////////////////////////////////////////////

void TEPICsyst::ChannelAccessWrite(mmtype &_mmv_evnt){
  Int_t err_type1 = 0, err_type2 = 0, err_type3 = 0, err_type4 = 0;
  mtype_ca::iterator ca_chnl_it = ca_chnl.begin();
  while(ca_chnl_it != ca_chnl.end()){

    if(!ca_write_access(ca_chnl_it->second)){
      TString msg = Form("Sys: %s; %s ca_write_access failed", 
			 sys_name.Data(), ca_chnl_it->first.Data());
      log->SendToLog(msg); cout<<msg<<endl; ChannelAccessError(msg.Data());
      if(err_type1<9){err_type1++;}
    }
    
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
	TString msg = Form("Sys:%s; unsupported channel type:%ld at ca_put", 
			   sys_name.Data(), i_chnl_type);
	log->SendToLog(msg); cout<<msg<<endl;
	if(err_type2<9){err_type2++;}
      }
      
      if(ca_return != ECA_NORMAL){
	TString msg = Form("Sys:%s; %s ca_put failed", 
			   sys_name.Data(), ca_chnl_it->first.Data());
	log->SendToLog(msg); cout<<msg<<endl; ChannelAccessError(msg.Data());}

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
	TString msg = Form("Sys:%s; unsupported channel type:%ld at ca_array_put", 
			   sys_name.Data(), i_chnl_type);
	log->SendToLog(msg); cout<<msg<<endl;
	if(err_type2<9){err_type2++;}
      }

      if(ca_return != ECA_NORMAL){
	TString msg = Form("Sys:%s; %s ca_array_put failed", 
			   sys_name.Data(), ca_chnl_it->first.Data());
	log->SendToLog(msg); cout<<msg<<endl; ChannelAccessError(msg.Data());
	if(err_type3<9){err_type3++;}
      }

    }
    else{
      	TString msg = Form("Sys:%s; Key:\"%s\"; wrong number of records:%d ca write", 
			   sys_name.Data(), ca_chnl_it->first.Data(), n_rcrds);
	log->SendToLog(msg); cout<<msg<<endl;
	if(err_type4<9){err_type4++;}
    }
    ca_chnl_it++;
  }
  caput_time    = GetTimestampString("time"); 
  caput_status  = err_type1*1 + err_type2*10 + err_type3*100 + err_type4*1000;
}

////////////////////////////////////////////////////////////////////////////////////////

void TEPICsyst::ChannelAccessWriteStatus(TString _ind, TString _time, Int_t _sid, Int_t _st){
  TString time_key = Form("caput_time_%s", _ind.Data());
  TString sid_key = Form("caput_spillid_%s", _ind.Data());
  TString st_key = Form("caput_status_%s", _ind.Data());

  mtype_ca::iterator ca_chnl_it;

  ca_chnl_it = ca_chnl.find(time_key);
  if(ca_chnl_it != ca_chnl.end()){
    chtype i_chnl_type = ca_field_type(ca_chnl_it->second);

    dbr_string_t *var = new dbr_string_t();
    //dbr_string_t var = {'\0'};
    //for(Int_t i=0;i<sizeof(dbr_string_t);i++){var[i]='\0';}
    for(Int_t i=0;i<std::min(sizeof(dbr_string_t),strlen(_time));i++){var[i]=_time[i];}

    ca_return = ca_put(i_chnl_type, ca_chnl_it->second, &var);
    //delete var;
  }

  ca_chnl_it = ca_chnl.find(sid_key);
  if(ca_chnl_it != ca_chnl.end()){
    chtype i_chnl_type = ca_field_type(ca_chnl_it->second);

    dbr_double_t *var = new dbr_double_t;
    *var = (dbr_double_t)_sid;

    ca_return = ca_put(i_chnl_type, ca_chnl_it->second, var);
    delete var;
  }

}

////////////////////////////////////////////////////////////////////////////////////////

void TEPICsyst::ChannelAccessFlushIO(){
  ca_return = ca_flush_io();
  if(ca_return != ECA_NORMAL){
    TString msg = Form("Sys:%s; ca_flush_io failed", sys_name.Data());
    log->SendToLog(msg); cout<<msg<<endl; ChannelAccessError(msg.Data());}
}

////////////////////////////////////////////////////////////////////////////////////////

void TEPICsyst::ChannelAccessClearVar(){
  mtype_ca::iterator ca_chnl_it = ca_chnl.begin();
  while(ca_chnl_it != ca_chnl.end()){
    ca_return = ca_clear_channel(ca_chnl_it->second);
    if(ca_return != ECA_NORMAL){
      TString msg = Form("Sys:%s; %s ca_clear_channel failed", 
			 sys_name.Data(), ca_chnl_it->first.Data());
      log->SendToLog(msg); cout<<msg<<endl; ChannelAccessError(msg.Data());}
    ca_chnl_it++;
  }
}

////////////////////////////////////////////////////////////////////////////////////////

void TEPICsyst::CleanUp(){
  ChannelAccessClearVar();
  TString msg = Form("Sys:%s; TEPICsyst cleaning and exiting", sys_name.Data());
  log->SendToLog(msg); cout<<msg<<endl;
  InitTEPICsystMembers();
}

////////////////////////////////////////////////////////////////////////////////////////

Int_t TEPICsyst::GetMMapValues(mmpair _rcrd, dbr_double_t *_val){
  
  Int_t cc = 0;
  mmtype::iterator mmv_rcrd_it;
  for(mmv_rcrd_it = _rcrd.first; mmv_rcrd_it != _rcrd.second; mmv_rcrd_it++){
    _val[cc] = (dbr_double_t)(mmv_rcrd_it->second.at(2).Atof());
    cc++;
  }
  return cc;
}

////////////////////////////////////////////////////////////////////////////////////////

Int_t TEPICsyst::GetMMapValues(mmpair _rcrd, dbr_string_t *_val){
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

void TEPICsyst::ChannelAccessError(TString _mess){
  cout<<_mess<<":"<<endl;
  cout<<ca_message(ca_return)<<endl;
  fflush(stdout);  exit(123456);
}

////////////////////////////////////////////////////////////////////////////////////////

Double_t TEPICsyst::GetTimestamp(){
  std::time_t time_stamp;
  Double_t res = Double_t(time(&time_stamp));
  time_struc = localtime(&time_stamp);
  return res;
}

////////////////////////////////////////////////////////////////////////////////////////

TString TEPICsyst::GetTimestampString(TString _sel){
  GetTimestamp();
  char time_buf[100]={0};
  if(_sel.EqualTo("yymm")){strftime(time_buf, 100, "%Y_%m", time_struc);}
  if(_sel.EqualTo("date")){strftime(time_buf, 100, "%Y_%m_%d", time_struc);}
  if(_sel.EqualTo("time")){strftime(time_buf, 100, "%H:%M:%S", time_struc);}
  TString time_str = time_buf;
  return time_str;
}

////////////////////////////////////////////////////////////////////////////////////////

void TEPICsyst::InitTEPICsystMembers(){
  sys_name      = "";
  caput_time    = ""; 
  caput_status  = 0;

  ca_chnl.clear();  
  ca_return     = 0;   
  ca_timeout    = 0.;
  ca_priority   = 0;

  log           = nullptr; 
  time_struc    = nullptr;   
}

////////////////////////////////////////////////////////////////////////////////////////
