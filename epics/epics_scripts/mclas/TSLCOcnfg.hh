#ifndef TSLCOcnfg_hh
#define TSLCOcnfg_hh

#include <iostream>
#include <fstream>
#include <map>
#include <ctime>
#include <TString.h>

#include "TSLCOlogs.hh"

class TSLCOcnfg{

public :

  typedef std::map<TString, std::vector<TString>>           mtype;

  TSLCOcnfg(TSLCOlogs* _log_in, TString _in_fn);
  TSLCOcnfg();
  ~TSLCOcnfg();

  void                 ReadConfigFile();
  void                 ReadSystemListFile();
  Bool_t               DoesDataDirExist();
  Double_t             GetTimestamp();
  TString              GetTimestampString(TString _sel);
  TString              ReadFromEpics(TString _var);
  Int_t                WriteToEpics(TString _var, Double_t _val);

  void                 CleanUp();
  
  TString              syslist_fname;//from cvs file produced by master spreadsheet
  TString              varlist_dname;//dir with system csv files containing variable lists 
  TString              sysdata_dname;//main slowcontrol data directory on raid array
  TString              daydata_dname;//daily slowcontrol data subdirectory
  TString              someout_dname;//optional output directory

  Double_t             max_bos2bos_time;
  Double_t             max_bos2eos_time;
  Double_t             max_readout_time;
  
  mtype                mslist;//container for active subsystems
  mtype::iterator      msl_it;
  Int_t                n_syson;//number of active subsystems
  
protected:

private:
 
  TSLCOlogs           *log;
  std::tm             *time_struc;   
  TString              cnfg_fname;
  std::vector<TString> dsv_arr;//temp array for dsv files readout

  Bool_t               ReadDelimeterSeparatedLine(std::istream &_str, TString _del);
  void                 InitTSLCOcnfgMembers();
};
#endif

