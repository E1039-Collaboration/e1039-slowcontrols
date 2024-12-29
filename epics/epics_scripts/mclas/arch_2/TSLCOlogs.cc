#include "TSLCOlogs.hh"
#include <iomanip>
#include <TSystem.h>

using std::cout;
using std::endl;


TSLCOlogs::TSLCOlogs(TString _in_dn){
  InitTSLCOlogsMembers();
  logs_topdn = _in_dn;
  if(!logs_topdn.EndsWith("/")){logs_topdn+="/";}
  if(!DoesLogDirExist()){cout<<"cant find or make logdir:"<<logs_dname<<endl;}
  if(!OpenNewLogFileWhenNeeded()){cout<<"cant open logfile:"<<logs_dname<<endl;}
}

//////////////////////////////////////////////////////////////////////////////////////// 

TSLCOlogs::TSLCOlogs(){}
TSLCOlogs::~TSLCOlogs(){CleanUp();}

////////////////////////////////////////////////////////////////////////////////////////

Bool_t TSLCOlogs::DoesLogDirExist(){
  TString current_monthstamp = GetTimestampString("yymm");
  logs_dname = logs_topdn+current_monthstamp+"/";
  if(gSystem->OpenDirectory(logs_dname)){return 1;}
  else{return !gSystem->MakeDirectory(logs_dname);}
}

////////////////////////////////////////////////////////////////////////////////////////

Bool_t TSLCOlogs::OpenNewLogFileWhenNeeded(){
  TString current_daystamp = GetTimestampString("date");
  logs_fname = logs_dname + current_daystamp + "_fill_epics.log";
  if(current_daystamp.EqualTo(last_daystamp.Data())){
    if(!fout.good()){
      CloseLogFile(); n_fail++;
      fout.open(logs_fname.Data(), std::ofstream::app);
      SendToLog(Form("reopening after logger was killed/or failed: %d",n_fail));
    }
  }
  else{
    last_daystamp = current_daystamp;
    CloseLogFile();
    fout.open(logs_fname.Data(), std::ofstream::app);
    SendToLog("starting a new log file or appending if logfile existed");
  }
  return fout.good();
}

////////////////////////////////////////////////////////////////////////////////////////

Bool_t TSLCOlogs::CloseLogFile(){
  if(fout.is_open()){fout.clear();fout.close();}
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOlogs::SendToLog(TString _msg){
  if(fout.good()){
    fout<<GetTimestampString("time")<<"---";
    fout<<_msg<<endl;
  }
}

////////////////////////////////////////////////////////////////////////////////////////

Double_t TSLCOlogs::GetTimestamp(){
  std::time_t time_stamp;   
  Double_t res = Double_t(time(&time_stamp));
  time_struc = localtime(&time_stamp);
  return res;
}

////////////////////////////////////////////////////////////////////////////////////////

TString TSLCOlogs::GetTimestampString(TString _sel){
  GetTimestamp();
  char time_buf[100]={0};
  if(_sel.EqualTo("yymm")){strftime(time_buf, 100, "%Y_%m", time_struc);}
  if(_sel.EqualTo("date")){strftime(time_buf, 100, "%Y_%m_%d", time_struc);}
  if(_sel.EqualTo("time")){strftime(time_buf, 100, "%H:%M:%S", time_struc);}
  TString time_str = time_buf;
  return time_str;
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOlogs::CleanUp(){
  TString msg = "TSLCOlogs cleaning and exiting";
  SendToLog(msg); cout<<msg<<endl;
  CloseLogFile();
  InitTSLCOlogsMembers();
}

////////////////////////////////////////////////////////////////////////////////////////

void TSLCOlogs::InitTSLCOlogsMembers(){
  logs_fname     = "";
  logs_topdn     = ""; 
  logs_dname     = ""; 
  last_daystamp  = ""; 
  n_fail         = 0;
  time_struc     = nullptr;
}

////////////////////////////////////////////////////////////////////////////////////////
