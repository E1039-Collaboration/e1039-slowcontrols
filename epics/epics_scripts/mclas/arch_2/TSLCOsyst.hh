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


  mtype                 mvlist;
  mmtype               mmvevnt;

  mtype::iterator       mvl_it;
  mmtype::iterator     mmve_it;

  Int_t                n_var;
  TString              sys_name;
  TString              sysdata_fname;
  Bool_t               is_readdone;

protected:
  
private:

  TSLCOlogs           *log;
  TString              varlist_dname;
  Int_t                spill_id;

  std::vector<TString> dsv_arr;

  Bool_t               ReadDelimeterSeparatedLine(std::istream &str, TString _del);
  void                 InitTSLCOsystMembers();
};

#endif
