#ifndef TSLCOlogs_hh
#define TSLCOlogs_hh

#include <cstdlib>
#include <iostream>
#include <fstream>
#include <ctime>
#include <TString.h>

class TSLCOlogs{

public :

  TSLCOlogs(TString _in_dn);
  TSLCOlogs();
  ~TSLCOlogs();

  Bool_t               DoesLogDirExist();
  Bool_t               OpenNewLogFileWhenNeeded();
  Bool_t               CloseLogFile();
  void                 SendToLog(TString _msg);

  Double_t             GetTimestamp();
  TString              GetTimestampString(TString _sel);

  void                 CleanUp();

  TString              logs_fname;

protected:
  
private:

  std::ofstream        fout;
  TString              logs_topdn; 
  TString              logs_dname; 
  TString              last_daystamp; 
  Int_t                n_fail;
  std::tm             *time_struc;   
  

  void                 InitTSLCOlogsMembers();
};
#endif

