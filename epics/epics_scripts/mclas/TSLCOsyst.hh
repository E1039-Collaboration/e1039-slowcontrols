#ifndef TSLCOsyst_hh
#define TSLCOsyst_hh

#include <iostream>
#include <fstream>
#include <map>
#include <TString.h>

#include "TSLCOlogs.hh"

class TSLCOsyst{

public :

  typedef std::map<TString, std::vector<TString>>           mtype;
  typedef std::multimap<TString, std::vector<TString>>      mmtype;  

  TSLCOsyst(TSLCOlogs* _log_in, TString _inlist_dn, TString _sysn);
  TSLCOsyst();
  ~TSLCOsyst();

  void                 ReadVariableListFile();
  Bool_t               DoesDataFileExist(TString _indata_dn, Int_t _spill_id);
  void                 ReadVariableDataFile();
  void                 VerifyVariableData();
  
  void                 PrintVarListMap();
  void                 PrintVarEvntMultiMap();

  void                 CleanUp();


  mtype                 mvlist;//map container for all expected PVs info for a subsystem
  mmtype               mmvevnt;//map container for all read PVs from tsv for a subsystem

  mtype::iterator       mvl_it;//key - PV name as shown in master spreadsheet 3d column
  mmtype::iterator     mmve_it;//key - PV name as shown in tsv 1st column

  Int_t                n_var;
  TString              sys_name;
  TString              sysdata_fname;
  Bool_t               is_skip;
  Bool_t               is_readdone;

  Int_t                spill_id;
  Int_t                tsvread_status;

protected:
  
private:

  TSLCOlogs           *log;
  TString              varlist_dname;


  std::vector<TString> dsv_arr;

  Bool_t               ReadDelimeterSeparatedLine(std::istream &str, TString _del);
  void                 InitTSLCOsystMembers();
};

#endif
