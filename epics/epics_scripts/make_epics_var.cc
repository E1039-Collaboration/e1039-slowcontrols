#include <iostream>
#include <fstream>
#include <stdlib.h>
#include <unistd.h>
#include <iomanip>

#include "TRint.h"
#include "TFile.h"
#include "TStyle.h"
#include "TSystem.h"
#include <TString.h>

//#include "THupgrade.hh"

#include "mclas/TSLCOcnfg.hh"
#include "mclas/TSLCOsyst.hh"

using std::cout;
using std::endl;

void PrintUsage(){
  cout<<endl<<"--------------------------------Usage--------------------------------"<<endl;
  cout<<"to create Epics include db files run command:"<<endl;
  cout<<"make_epics_var path/to/config/file"<<endl;
  cout<<"---------------------------------------------------------------------"<<endl<<endl;
}

int main(int argc, char **argv)
{
  if(argc!=3){ PrintUsage(); exit(444); }

  TString dn_logs=argv[1];
  TString fn_cnfg=argv[2];

  TSLCOlogs *logs = new TSLCOlogs(dn_logs);
  TSLCOcnfg *cnfg = new TSLCOcnfg(logs, fn_cnfg);

  //cnfg->SetLog(logs);  
  //cnfg->ReadConfigFile();
  cnfg->ReadSystemListFile();

  Int_t cc=0;

  for(cnfg->msl_it =cnfg->mslist.begin();cnfg->msl_it!=cnfg->mslist.end();cnfg->msl_it++){

    TSLCOsyst *syst = new TSLCOsyst(logs, cnfg->varlist_dname, cnfg->msl_it->first);
    TString epics_db_fname = Form("%srecords_list_%s.db",
				  cnfg->someout_dname.Data(),
				  cnfg->msl_it->first.Data());

    
    std::ofstream fout;  fout.open(epics_db_fname.Data());
    if(!fout){cout<<"Cannot open file "<<epics_db_fname<<" exiting..."<<endl; exit(1111);}
    //syst->ReadVariableListFile();


    syst->mvl_it = syst->mvlist.begin();
    while(syst->mvl_it != syst->mvlist.end()){
      //records: ai(double), stringin(string), waveform(double or string)
            
      TString desc = Form("  field(DESC,\"%s\")", syst->mvl_it->second.at(1).Data());
      TString dtyp = Form("  field(DTYP,\"%s\")", "Soft Channel");
      TString inp  = Form("  field(INP,\"%s\")" , "");
      TString pini = Form("  field(PINI,\"%s\")", "1");
      TString scan = Form("  field(SCAN,\"%s\")", "Passive");
      TString egu  = Form("  field(EGU,\"%s\")" , syst->mvl_it->second.at(5).Data());
      TString lolo = Form("  field(LOLO,\"%s\")", syst->mvl_it->second.at(6).Data());
      TString low  = Form("  field(LOW,\"%s\")" , syst->mvl_it->second.at(7).Data());
      TString high = Form("  field(HIGH,\"%s\")", syst->mvl_it->second.at(8).Data());
      TString hihi = Form("  field(HIHI,\"%s\")", syst->mvl_it->second.at(9).Data());
      TString prec = Form("  field(PREC,\"%s\")", syst->mvl_it->second.at(10).Data());

      TString hhsv = Form("  field(HHSV,\"%s\")", "2");
      TString hsv  = Form("  field(HSV,\"%s\")" , "1");      
      TString llsv = Form("  field(LLSV,\"%s\")", "2");
      TString lsv  = Form("  field(LSV,\"%s\")" , "1");
      TString nelm = Form("  field(NELM,\"%s\")", "60");
      TString ftvl = Form("  field(FTVL,\"%s\")" , "DOUBLE");
      TString brkt = Form("%s" , "}");      

      TString rcrd = Form("record(ai,\"%s\"){",   syst->mvl_it->second.at(2).Data());//always
      if(syst->mvl_it->second.at(3).Contains("string")){//unless
	rcrd = Form("record(stringin,\"%s\"){",   syst->mvl_it->second.at(2).Data());
	ftvl = Form("  field(FTVL,\"%s\")" , "STRING");//for waveforms only
      }
      if(syst->mvl_it->second.at(4).Atoi()>1){//otherwise always
	rcrd = Form("record(waveform,\"%s\"){",   syst->mvl_it->second.at(2).Data());
      }

     
      fout<<rcrd.Data()<<endl;//all
      fout<<desc.Data()<<endl;//all
      fout<<dtyp.Data()<<endl;//all
      fout<<pini.Data()<<endl;//all

      if(rcrd.Contains("ai,")){
	fout<<egu.Data()<<endl; //ai
	fout<<inp.Data()<<endl; //input records
	fout<<lolo.Data()<<endl;//ai
	fout<<low.Data()<<endl; //ai
	fout<<high.Data()<<endl;//ai
	fout<<hihi.Data()<<endl;//ai
	fout<<hhsv.Data()<<endl;//ai
	fout<<hsv.Data()<<endl; //ai
	fout<<llsv.Data()<<endl;//ai
	fout<<lsv.Data()<<endl; //ai
	fout<<prec.Data()<<endl; //ai
      }
      if(rcrd.Contains("waveform,")){
	fout<<nelm.Data()<<endl;//waveform and other arr
	fout<<ftvl.Data()<<endl;//waveform and other arr
      }

      fout<<brkt.Data()<<endl;
      
      cout<<cc<<" writing variable: "<<syst->mvl_it->second.at(2)<<endl;
      cc++;
      syst->mvl_it++;
    }
    fout.close();
  }
    
  //theApp->Run();  

}

