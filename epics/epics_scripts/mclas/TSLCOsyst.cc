#include "TSLCOsyst.hh"

#include <iostream>
#include <fstream>
#include <cstdlib>
#include <cmath>
#include <ctime>
#include <iomanip>
#include <sys/stat.h>

#include <TSystem.h>

using std::cout;
using std::endl;

TSLCOsyst::TSLCOsyst(TSLCOlogs* _log_in, TString _inlist_dn, TString _sysn){
  InitTSLCOsystMembers();
  log           = _log_in;
  varlist_dname = _inlist_dn;
  sys_name      = _sysn;
  ReadVariableListFile();
}

//////////////////////////////////////////////////////////////////////////////////////// 

TSLCOsyst::TSLCOsyst(){}
TSLCOsyst::~TSLCOsyst(){CleanUp();}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOsyst::ReadVariableListFile(){
  TString fn_varl = varlist_dname+"varlist_"+sys_name+".csv";
  std::ifstream fin;  fin.open(fn_varl.Data(), std::ifstream::in);
  if(!fin){
    TString msg = Form("Cant open varlist file %s; exiting...", fn_varl.Data());
    log->SendToLog(msg); cout<<msg<<endl; exit(1111);}

  Int_t ivar=0;
  mvlist.clear();
  while(fin.good()){
    if(ReadDelimeterSeparatedLine(fin,",")){
      if(dsv_arr.size()==12){
	if(!mvlist.count(dsv_arr.at(2))){mvlist[dsv_arr.at(2)]=dsv_arr; ivar++;}
	else{
	  TString msg = Form("Key:\"%s\" already exist; exiting...",dsv_arr.at(2).Data());
	  log->SendToLog(msg); cout<<msg<<endl; exit(1111);}
      }
      else{
	TString msg = Form("Sys:%s. %lu values received; expected 12; exiting...",
			   sys_name.Data(), dsv_arr.size());
	log->SendToLog(msg); cout<<msg<<endl; exit(1111);}
    }
  }
  n_var = ivar;
  fin.close();
}

////////////////////////////////////////////////////////////////////////////////////////

Bool_t TSLCOsyst::DoesDataFileExist(TString _indata_dn, Int_t _spill_id){
  spill_id = _spill_id;
  sysdata_fname = Form("%sspill_%09d_%s.tsv",
			 _indata_dn.Data(),_spill_id,sys_name.Data());
  //struct stat buffer;
  //int         status;
  //status = stat(sysdata_fname.Data(), &buffer);
  //return !status;
  TString cmnd = Form("ls -l %s\*%d\*",_indata_dn.Data(),spill_id);
  gSystem->Exec(cmnd);

  std::ifstream fin;  fin.open(sysdata_fname.Data());
  Bool_t res = (!fin.fail());
  fin.close();
  return res;
  //return !gSystem->AccessPathName(gSystem->ExpandPathName(sysdata_fname.Data()));
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOsyst::ReadVariableDataFile(){
  std::ifstream fin;  fin.open(sysdata_fname.Data());
  if(!fin){
    TString msg = Form("Cant open varlist file %s; exiting...", sysdata_fname.Data());
    log->SendToLog(msg); cout<<msg<<endl; exit(1111);}

  mmvevnt.clear();
  while(fin.good()){
    if(ReadDelimeterSeparatedLine(fin,"\t")){
      if(dsv_arr.size()==4){mmvevnt.insert(mmtype::value_type(dsv_arr.at(0),dsv_arr));}
      else{
	TString msg = Form("%u values received; expected 4; exiting...", dsv_arr.size());
	log->SendToLog(msg); cout<<msg<<endl; exit(1111);}
    }
  }
  is_readdone = 1;
  fin.close();

  TString msg = Form("Sys:%s; Spill:%09d; tsv read done.", sys_name.Data(), spill_id);
  log->SendToLog(msg);
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOsyst::VerifyVariableData(){
  mvl_it = mvlist.begin();
  while(mvl_it != mvlist.end()){
    std::pair<mmtype::iterator, mmtype::iterator> mmv_record;
    mmv_record = mmvevnt.equal_range(mvl_it->first);
    Int_t n_pnt = std::distance(mmv_record.first,mmv_record.second);
    if(n_pnt<1){
      TString msg = Form("Sys:%s; Key:\"%s\"; Key not found in tsv", 
			 sys_name.Data(), mvl_it->first.Data());
      log->SendToLog(msg);
      cout<<msg<<endl;}
    if(n_pnt>1){
      Double_t old_timestamp = 0;
      for(mmve_it = mmv_record.first; mmve_it != mmv_record.second; mmve_it++){
	Double_t new_timestamp = mmve_it->second.at(1).Atof();
	if(old_timestamp == new_timestamp){
	  TString msg = Form("Sys:%s; Key:\"%s\"; Time duplicate:%f", 
			     sys_name.Data(), mvl_it->first.Data(), new_timestamp);
	  log->SendToLog(msg);
	  cout<<msg<<endl;}
	else{old_timestamp = new_timestamp;}
      }
    }
    mvl_it++;
  }

  mmve_it = mmvevnt.begin();
  while(mmve_it != mmvevnt.end()){
    if(mvlist.find(mmve_it->first) == mvlist.end()){
      TString msg = Form("Sys:%s; Key:\"%s\"; Key not registered in epics db", 
			 sys_name.Data(), mmve_it->first.Data());
      log->SendToLog(msg);
      cout<<msg<<endl;}
    mmve_it++;
  }
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOsyst::PrintVarListMap(){
  mvl_it = mvlist.begin();                                             
  while(mvl_it != mvlist.end()){                                         
    Int_t n=mvl_it->second.size();                                                 
    cout<<"Sys:"<<sys_name.Data()
	<<". Key:\""<<mvl_it->first
	<<"\". Content: ";                                            
    for(Int_t i=0;i<n;i++){cout<<mvl_it->second.at(i)<<" ";}                       
    cout<<endl;                                                                              
    mvl_it++;                                                                      
  }
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOsyst::PrintVarEvntMultiMap(){
  mmve_it = mmvevnt.begin();
  while(mmve_it != mmvevnt.end()){
    Int_t n=mmve_it->second.size();
    cout<<"Sys: "<<sys_name.Data()
	<<". Key: \""<<mmve_it->first                                           
	<<"\". Content: ";                                            
    for(Int_t i=0;i<n;i++){cout<<mmve_it->second.at(i)<<" ";}                       
    cout<<endl;                                                                              
    mmve_it++;
  }
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOsyst::CleanUp(){
  TString msg = Form("Sys:%s; TSLCOsyst cleaning and exiting", sys_name.Data());
  log->SendToLog(msg); cout<<msg<<endl;
  InitTSLCOsystMembers();
}

////////////////////////////////////////////////////////////////////////////////////////

Bool_t TSLCOsyst::ReadDelimeterSeparatedLine(std::istream &_str, TString _del){
  TString line;
  Bool_t res = line.ReadLine(_str,0).good();
  if(res){      
    Ssiz_t pos=0;
    dsv_arr.clear();

    while(pos>=0){
      pos = line.Index(_del.Data());
      TString var = line;
      if(pos>=0){var.Remove(pos);}//first chunk before delimeter
      dsv_arr.push_back(var);
      line.Remove(0,pos+1);//remove first chunk with delimeter
    }
  }
  return res;
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOsyst::InitTSLCOsystMembers(){
  mvlist.clear();
  mmvevnt.clear();

  n_var         = 0;
  is_readdone   = 0;

  log           = nullptr;
  sys_name      = "";
  sysdata_fname = "";
  varlist_dname = "";
  
  dsv_arr.clear();

}

////////////////////////////////////////////////////////////////////////////////////////
