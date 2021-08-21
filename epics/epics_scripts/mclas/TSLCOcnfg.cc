#include "TSLCOcnfg.hh"

#include <iostream>
#include <fstream>
#include <cstdlib>
#include <iomanip>
#include <sys/stat.h>

#include <TSystem.h>

using std::cout;
using std::endl;

TSLCOcnfg::TSLCOcnfg(TSLCOlogs* _log_in, TString _in_fn){
  InitTSLCOcnfgMembers();
  log        = _log_in;
  cnfg_fname =_in_fn;
  ReadConfigFile();
}

//////////////////////////////////////////////////////////////////////////////////////// 

TSLCOcnfg::TSLCOcnfg(){}
TSLCOcnfg::~TSLCOcnfg(){CleanUp();}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOcnfg::ReadConfigFile(){
  //expects 2-field file separated by :
  std::ifstream fin;  fin.open(cnfg_fname.Data());
  if(!fin){
    TString msg = Form("Cant open configuration file %s; exiting...", cnfg_fname.Data());
    log->SendToLog(msg); cout<<msg<<endl; exit(1111);}
  
  while(fin.good()){
    if(ReadDelimeterSeparatedLine(fin,":")){
      if(dsv_arr.size()==2){
	TString field = dsv_arr.at(0);
	TString value = dsv_arr.at(1).Strip(TString::kLeading,' ');

	if(field.Contains("sys list file")){syslist_fname=value;}
	if(field.Contains("var list dir")) {varlist_dname=value;}
	if(field.Contains("var data dir")) {sysdata_dname=value;}
	if(field.Contains("out dir"))      {someout_dname=value;}
	if(field.Contains("bos2bos time")) {max_bos2bos_time=value.Atof();}
	if(field.Contains("bos2eos time")) {max_bos2eos_time=value.Atof();}
	if(field.Contains("readout time")) {max_readout_time=value.Atof();}
      }
      else{
	TString msg = Form("%u values received; expected 2; exiting...", dsv_arr.size());
        log->SendToLog(msg); cout<<msg<<endl; exit(1111);}
    }
  }
  fin.close();
  if(!varlist_dname.EndsWith("/")){varlist_dname+="/";}
  if(!sysdata_dname.EndsWith("/")){sysdata_dname+="/";}
  if(!someout_dname.EndsWith("/")){someout_dname+="/";}
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOcnfg::ReadSystemListFile(){
  //expects 3-column csv file
  std::ifstream fin;  fin.open(syslist_fname.Data());
  if(!fin){
    TString msg = Form("Cant open syslist file %s; exiting...", syslist_fname.Data());
    log->SendToLog(msg); cout<<msg<<endl; exit(1111);}
  
  Int_t isys=0;
  mslist.clear();
  while(fin.good()){
    if(ReadDelimeterSeparatedLine(fin,",")){
      if(dsv_arr.size()==3){

	if(dsv_arr.at(2).Atoi()){//is on?
	  if(!mslist.count(dsv_arr.at(1))){//duplicate?
	    mslist[dsv_arr.at(1)]=dsv_arr; isys++;}
	  else{
	    TString msg = Form("Key:\"%s\" already exist; exiting...",dsv_arr.at(1).Data());
	    log->SendToLog(msg); cout<<msg<<endl; exit(1111);}
	}

      }
      else{
	TString msg = Form("%u values received; expected 3; exiting...", dsv_arr.size());
        log->SendToLog(msg); cout<<msg<<endl; exit(1111);}
    }
  }
  n_syson = isys;
  fin.close();
}

////////////////////////////////////////////////////////////////////////////////////////

Bool_t TSLCOcnfg::DoesDataDirExist(){
  TString current_daystamp = GetTimestampString("date");
  daydata_dname = sysdata_dname+"slowcontrol_"+current_daystamp+"/";
  //if(gSystem->OpenDirectory(daydata_dname)){return 1;}
  //else{return 0;}
  struct stat buffer;
  int         status;
  status = (stat(daydata_dname.Data(), &buffer)==0) && S_ISDIR(buffer.st_mode);
  return status;
}

////////////////////////////////////////////////////////////////////////////////////////

Double_t TSLCOcnfg::GetTimestamp(){
  std::time_t time_stamp;
  Double_t res = Double_t(time(&time_stamp));
  time_struc = localtime(&time_stamp);
  return res;
}

////////////////////////////////////////////////////////////////////////////////////////

TString TSLCOcnfg::GetTimestampString(TString _sel){
  GetTimestamp();
  char time_buf[100]={0};
  if(_sel.EqualTo("yymm")){strftime(time_buf, 100, "%Y_%m", time_struc);}
  if(_sel.EqualTo("date")){strftime(time_buf, 100, "%Y_%m_%d", time_struc);}
  if(_sel.EqualTo("time")){strftime(time_buf, 100, "%H:%M:%S", time_struc);}
  TString time_str = time_buf;
  return time_str;
}

////////////////////////////////////////////////////////////////////////////////////////

TString TSLCOcnfg::ReadFromEpics(TString _var){
  TString cmnd = Form("caget -t %s",_var.Data());
  TString rpns = gSystem->GetFromPipe(cmnd);
  return rpns;
}

////////////////////////////////////////////////////////////////////////////////////////

Int_t TSLCOcnfg::WriteToEpics(TString _var, Double_t _val){
  TString cmnd = Form("caput %s %f",_var.Data(),_val);
  return gSystem->Exec(cmnd);
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOcnfg::CleanUp(){
  TString msg = "TSLCOcnfg cleaning and exiting";
  log->SendToLog(msg); cout<<msg<<endl;
  InitTSLCOcnfgMembers();
}

////////////////////////////////////////////////////////////////////////////////////////

Bool_t TSLCOcnfg::ReadDelimeterSeparatedLine(std::istream &_str, TString _del){
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

void TSLCOcnfg::InitTSLCOcnfgMembers(){
  syslist_fname    = "";
  varlist_dname    = "";
  sysdata_dname    = "";
  daydata_dname    = "";
  someout_dname    = "";

  max_bos2bos_time = 0.;
  max_bos2eos_time = 0.;
  max_readout_time = 0.;

  mslist.clear();  
  n_syson          = 0;

  log              = nullptr;   
  time_struc       = nullptr;   
  cnfg_fname       = "";

  dsv_arr.clear();
}

////////////////////////////////////////////////////////////////////////////////////////
