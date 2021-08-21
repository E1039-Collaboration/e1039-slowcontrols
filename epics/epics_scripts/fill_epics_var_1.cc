#include <iostream>
#include <fstream>
#include <stdlib.h>
#include <unistd.h>
#include <iomanip>
#include <unistd.h>
#include <csignal>
#include <time.h>

#include "TRint.h"
#include "TFile.h"
#include "TStyle.h"
#include "TSystem.h"
#include <TString.h>

#include "mclas/TEPICcnfg.hh"
#include "mclas/TEPICsyst.hh"
#include "mclas/TSLCOcnfg.hh"
#include "mclas/TSLCOsyst.hh"
#include "mclas/TSLCOlogs.hh"

using std::cout;
using std::endl;

sig_atomic_t exitRequested = 0;
void NiceKillExit(int signum){exitRequested=1; cout<<"interrupt exit:"<<signum<<endl;}

void PrintUsage(){
  cout<<endl<<"--------------------------------Usage--------------------------------"<<endl;
  cout<<"fill_epics_var arg1 arg2"<<endl;
  cout<<"arg1: path to the logger output top directory"<<endl;
  cout<<"arg2: path to the fill_epics_var configuration file"<<endl;
  cout<<"---------------------------------------------------------------------"<<endl<<endl;
  cout<<"arguments were nor provided, using defaults instead..."<<endl;
}

int main(int argc, char **argv)
{
  std::signal(SIGINT,  NiceKillExit);//ctrl+c
  std::signal(SIGTERM, NiceKillExit);//kill proc_id; 

  TString dn_logs=argv[1];
  TString fn_cnfg=argv[2];

  if(argc!=3){ 
    PrintUsage(); 
    dn_logs="/data2/e1039_data/slowcontrol_logs";
    fn_cnfg="/data2/e1039/daq/slowcontrols/epics/epics_scripts/mdata/fill_epics_config.txt";
  }
  
  TSLCOlogs *logs = new TSLCOlogs(dn_logs);
  TSLCOcnfg *cnfg = new TSLCOcnfg(logs, fn_cnfg);
  TEPICcnfg *epic = new TEPICcnfg(logs);

  cnfg->ReadSystemListFile();
  epic->ChannelAccessInit();

  std::map<TString,TSLCOsyst *> syst_tsv;
  std::map<TString,TEPICsyst *> syst_ca;

  for(cnfg->msl_it =cnfg->mslist.begin();cnfg->msl_it!=cnfg->mslist.end();cnfg->msl_it++){
    TString indx = cnfg->msl_it->first;
    syst_tsv[indx] = new TSLCOsyst(logs, cnfg->varlist_dname, cnfg->msl_it->first);
    syst_ca[indx]  = new TEPICsyst(logs, cnfg->msl_it->first);
    syst_ca[indx]->ChannelAccessInitVar(syst_tsv[indx]->mvlist);
    syst_ca[indx]->ChannelAccessPendIO();
  }

  Bool_t mydebug = 1;

  Int_t bos_flag               = 0;
  Int_t eos_ready              = 0;
  Int_t eos_flag               = 0;
  Int_t spill_id               = 0;

  Double_t time_at_codeinit    = cnfg->GetTimestamp();
  Double_t time_at_lastbos     = cnfg->GetTimestamp();
  Double_t time_at_lasteos     = cnfg->GetTimestamp();
  Double_t time_at_readout     = cnfg->GetTimestamp();

  Double_t time_since_codeinit = 0.;
  Double_t time_since_lastbos  = 0.;
  Double_t time_since_lasteos  = 0.;
  Double_t time_since_readout  = 0.;

  while(!exitRequested){
    time_since_codeinit = cnfg->GetTimestamp() - time_at_codeinit;
    time_since_lastbos  = cnfg->GetTimestamp() - time_at_lastbos;
    time_since_lasteos  = cnfg->GetTimestamp() - time_at_lasteos;
    
    usleep(1000000);
    
    //bos_flag = cnfg->ReadFromEpics("BOS").Atoi();
    //eos_flag = cnfg->ReadFromEpics("EOS").Atoi();
    bos_flag = syst_ca["SpillData"]->ChannelAccessReadDoublesOnly("BOS");
    eos_flag = syst_ca["SpillData"]->ChannelAccessReadDoublesOnly("EOS");


    if(!logs->OpenNewLogFileWhenNeeded()){
      TString msg = Form("Logfile failure:%s",logs->logs_fname.Data());
      cout<<msg<<endl;}

    TString msg = Form("bos:%d; eos:%d; eos_rdy:%d; last bos:%3.0fs ago",
		       bos_flag, eos_flag, eos_ready, time_since_lastbos);
    logs->SendToLog(msg); cout<<msg<<endl; 

    if(time_since_lastbos > cnfg->max_bos2bos_time){
      eos_ready=0;
      TString msg = Form("No bos, bad spill?; last bos:%3.0fs ago; expected bos2bos:%3.0fs",
			 time_since_lastbos, cnfg->max_bos2bos_time);
      logs->SendToLog(msg); cout<<msg<<endl; 
    }

    if(eos_ready == 1 && time_since_lastbos > cnfg->max_bos2eos_time){
      eos_ready=0;
      TString msg = Form("No eos, bad spill?; last bos:%3.0fs ago; expected bos2eos:%3.0fs",
			 time_since_lastbos, cnfg->max_bos2eos_time);
      logs->SendToLog(msg); cout<<msg<<endl; 
    }

    if(bos_flag == 1){//bos arrived, clear readout flag
      time_at_lastbos = cnfg->GetTimestamp();
      bos_flag  = 0;
      eos_ready = 1;
      for(cnfg->msl_it =cnfg->mslist.begin();
	  cnfg->msl_it!=cnfg->mslist.end();
	  cnfg->msl_it++){
	TString indx = cnfg->msl_it->first;
	syst_tsv[indx]->is_readdone = 0;
      }
      syst_tsv["SpillData"]->is_readdone = 1;
    }

    //if(mydebug){
    if( (eos_ready == 1 && eos_flag == 1)){//eos todo start
      time_at_lasteos = cnfg->GetTimestamp();
      eos_flag  = 0;
      eos_ready = 0;
      //spill_id = cnfg->ReadFromEpics("SPILLCOUNTER").Atoi();
      spill_id = syst_ca["SpillData"]->ChannelAccessReadDoublesOnly("SPILLCOUNTER");

      TString msg = Form("readout start at Spill ID:%09d",spill_id);
      logs->SendToLog(msg); cout<<msg<<endl; 

      if(!cnfg->DoesDataDirExist()){
	TString msg = Form("No data directory available:%s",cnfg->daydata_dname.Data());
	logs->SendToLog(msg); cout<<msg<<endl; 
	continue;
      }
      
      Bool_t all_complete = 0;
      time_at_readout = cnfg->GetTimestamp();
      time_since_readout = 0;
      while( (!exitRequested) & (!all_complete)  & 
	     (time_since_readout < cnfg->max_readout_time) ){

	time_since_lasteos = cnfg->GetTimestamp() - time_at_lasteos;
	time_since_readout = cnfg->GetTimestamp() - time_at_readout;
	TString msg = Form("completed:%s; last eos:%3.0fs ago; readout started :%3.0fs ago",
			   all_complete ? "true":"false", 
			   time_since_lasteos, time_since_readout);
	logs->SendToLog(msg); cout<<msg<<endl; 

	usleep(1000000);
	all_complete = 1;
	for(cnfg->msl_it =cnfg->mslist.begin();//cycle over subsystems
	    cnfg->msl_it!=cnfg->mslist.end();
	    cnfg->msl_it++){
	  
	  TString indx = cnfg->msl_it->first;
	  if(syst_tsv[indx]->is_readdone){continue;}
	  if(syst_tsv[indx]->DoesDataFileExist(cnfg->daydata_dname, spill_id)){
	    clock_t t_start, t_end;
	    //t_start = clock();
	    usleep(1000000);
	    syst_tsv[indx]->ReadVariableDataFile();
	    syst_tsv[indx]->VerifyVariableData();
	    //syst_tsv[indx]->PrintVarEvntMultiMap();
	    syst_tsv[indx]->is_readdone = 1;
	    
	    
	    syst_ca[indx]->ChannelAccessWrite(syst_tsv[indx]->mmvevnt);
	    syst_ca[indx]->ChannelAccessFlushIO();
	    

	    //t_end = clock();

	    //Double_t t_s = Double_t(t_start);
	    //Double_t t_e = Double_t(t_end);
	    //Double_t t_period = (t_e - t_s)/(Double_t)(CLOCKS_PER_SEC);
	    //cout<<"time elalsed "
	    //<<std::fixed<< std::setprecision(9)
	    //<<t_s<<" "
	    //<<t_e<<" "
	    //<<t_period<<endl;
	    
	  }
	  else{
	    all_complete = 0;
	    TString msg = Form("No data file:%s yet",
			       gSystem->BaseName(syst_tsv[indx]->sysdata_fname.Data()));
	    logs->SendToLog(msg); cout<<msg<<endl; 
	    continue;
	  }
	}//readout loop end
      }//readout waiting loop end
      
      for(cnfg->msl_it =cnfg->mslist.begin();cnfg->msl_it!=cnfg->mslist.end();cnfg->msl_it++){
	TString indx = cnfg->msl_it->first;
	if(!syst_tsv[indx]->is_readdone){
	  TString msg = Form("Warning failed %s readout at Spill ID:%09d",
			     syst_tsv[indx]->sys_name.Data(), spill_id);
	  logs->SendToLog(msg); cout<<msg<<endl; 
	}
      }
    }//eos todo end

  }//forever loop end

  std::map<TString,TEPICsyst *>::iterator syst_ca_it;
  for(syst_ca_it=syst_ca.begin(); syst_ca_it!=syst_ca.end(); syst_ca_it++){
    delete syst_ca_it->second;}
  syst_ca.clear();

  std::map<TString,TSLCOsyst *>::iterator syst_tsv_it;
  for(syst_tsv_it=syst_tsv.begin(); syst_tsv_it!=syst_tsv.end(); syst_tsv_it++){
    delete syst_tsv_it->second;}
  syst_tsv.clear();

  delete epic; epic = nullptr;
  delete cnfg; cnfg = nullptr;
  delete logs; logs = nullptr;
}

