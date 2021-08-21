// Records the temperatures of seven thermistors, pressure, and humidity
// from a 7710 multiplexer card

// Output is printed in the following order:
// Cables are labeled as blow where they enter Keithley Modules
// See doc-db for more information
//
// Thermistors:
//     T1 = hydrogen pipe in target control area
//     T2 = discriminator NIM crate for st. 1, 2 hodoscopes
//     T3 = bottom of tall post 0.91m above floor (T3 and T4 are at same location, but are different types of thermistors
//     T4 = bottom of tall post 0.91m above floor
//     T5 = middle of tall post 2.59m above floor
//     T6 = trigger supervisor VME crate
//     T7 = top of tall post    6.25m above floor,
//     T8 = NM3 ??? ??? ???
//     T9 = NM3 ??? ??? ???
//     T10 = NM3 ??? ??? ???
//
//  HXX Sensors each have a humidity sensor and Temperature sensor
//   (position to be determined by Drift Chamber experts
//     HT1=humidity sensor #1 temperature
//     HT2=humidity sensor #2 temperature
//     HT3=humidity sensor #3 temperature
//     HT4=humidity sensor #4 temperature

//     HH1=humidity sensor #1 relative  humidity
//     HH2=humidity sensor #2 relative  humidity
//     HH3=humidity sensor #3 relative  humidity
//     HH4=humidity sensor #4 relative  humidity

//     P1=Shares cable with Humidity/Temperature  Modules
//     P2=Shares cable with Humidity/Temperature  Modules
//     P3=On its own twisted cable



//  Temperature/Humidity sensors are read out where Ch. 8-11 are the temperatures of H1, H2, H3 and H4
//  Then channels 11-14 are read out as voltages and converted to relative humidity.
//  Pressure
//  The channels 15-17 are pressure from the MPXAZ6115A pressure sensor (circuits used are handmade and are crude)
//
//  Once the humidity and temperature are known on a particular sensor the dew point is calculated and output

// If you change or add new sensors, you must modify these parts of code:
// Set fNChannels
// Change channel numbers in temperature/voltage reading configuration
// Set the scan command to scan the correct channels
// Set which voltage measurements get converted to pressure or humidity
// written by Brandon Bowen, Mandy Crowder, Shon Watson, Donald Isenhower, Elizabeth Carlisle, Zhaojia Xi
// Also, you should make sure that the read_slowcontrol script gives the output correct labels


#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netdb.h>

#include <errno.h>
#include <time.h>
#include <unistd.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>


using namespace std;
class KMultimeter
{
public:
  KMultimeter(const char* ip_host);
  ~KMultimeter();

  int ReadAll();
  int StopAcq();
  int SaveAll();

  bool IsConnected() { return fSocket > 0; }
  bool IsOkay() { return !fBadness; }
private:
  int SendCommand(const char* cmd);
  int GetResponse(char* buf, const size_t len);

  // Convert raw measurements to standard units
  double ConvertPressure(double voltage);
  double ConvertHumidity(double voltage);
  double Convert10kThermToDegC(double resistance);
  double CalculateDewpoint(double temperature_C, double rel_humidity_pct);

private:
  int fSocket;
  string fLastMeasurements[256];
  int fNChannels;
  bool fBadness;
  time_t lastMeasTime; // TODO: consider a separate timestamp for each channel...
};

KMultimeter::KMultimeter(const char* ip_host)
  : fSocket(-1)
  , fNChannels(0)
  , fBadness(false)
  , lastMeasTime(0)
{
  int ret = 0;
  fNChannels = 21; //number of channels
  for (int i = 0; i<256; i++)
    fLastMeasurements[i] = "";
  fSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
  if (fSocket <= 0) {
    cerr << "Error: socket() failed.\n";
    cerr << strerror(errno) << endl;
    fBadness = true;
    return;
  }
  int optval=1;
  ret = setsockopt(fSocket, IPPROTO_TCP, TCP_NODELAY, &optval, sizeof(optval)); // enable TCP_NODELAY option
  // FIXME: check return value..., should be okay to just warn if option cannot be set

  addrinfo *dmm_addr_info;
  addrinfo hints;
  hints.ai_flags = 0;  // TODO: if an IP address is already known, could specify AI_NUMERICHOST here to avoid potentially slow DNS lookups...
  hints.ai_family = AF_INET;
  hints.ai_socktype = SOCK_STREAM;
  hints.ai_protocol = IPPROTO_TCP;
  hints.ai_addrlen = 0; hints.ai_addr = 0; hints.ai_canonname = 0; hints.ai_next = 0;
  
  ret = getaddrinfo(ip_host, "1394", &hints, &dmm_addr_info);
  if (ret != 0) {
    cerr << "Error: getaddrinfo for the host or ip address: ``" << ip_host << "'' was unsuccessful." << endl;
    cerr << strerror(errno) << endl;
    fBadness = true;
    return;
  }

  char addr_str[256];
  memset(addr_str, 0, sizeof(addr_str));
  char serv_str[256];
  ret = getnameinfo(dmm_addr_info->ai_addr, dmm_addr_info->ai_addrlen, addr_str, sizeof(addr_str), serv_str, sizeof(serv_str), NI_NUMERICHOST | NI_NUMERICSERV);
  if (ret != 0) {
    cerr << "Error: getnameinfo was unsuccessful.\n";
    cerr << strerror(errno) << endl;
    fBadness = true;
    return;
  }
  
  ret = connect(fSocket, dmm_addr_info->ai_addr, dmm_addr_info->ai_addrlen); 
  if (ret != 0) {
    fSocket=-1;
    fBadness=true;
    cerr << "Error: socket connect() failed (" << addr_str << " on port " << serv_str << ")." << endl;
    cerr << strerror(errno) << endl;
    return;
  }
  freeaddrinfo(dmm_addr_info);

//  char cmd[255];
//  memset(cmd, 0, sizeof(cmd));
//  strncpy(cmd,"*IDN?\r\n", sizeof(cmd)-1);
  char cmd[256];
  memset(cmd, 0, sizeof(cmd));
  // char buf[256];
  //memset(buf, 0, sizeof(buf));
  // TODO: should check device identification string...
  //SendCommand("*IDN?\r\n");
  //GetResponse(buf, sizeof(buf));
  //printf("%s", buf);

  bool send_reset = true;
  if (send_reset) {
    // TODO: should there be a delay/sleep after the RST command before sending other commands?
    SendCommand("*RST;FORM:ELEM READ\r\n");
    // TODO: change format to include UNITs and CHANnel .  Then use them to help validate incoming data.
  } else {
    SendCommand("ROUTe:SCAN:LSELect NONE\r\n");
    SendCommand("INIT:CONT OFF\r\n");
    SendCommand("FORM:ELEM READ\r\n");
    SendCommand("TRAC:CLE\r\n");
  }


// Configuration for temperature reading:
// 10 temperatures from different locations, then 4 temperatures from Humidity/Temp modules
// [FIXME: COMMENT OUT OF DATE?] 1-4 are temperature sensors on humidity boards
// [FIXME: COMMENT OUT OF DATE?] 5-8 are the humidity;9,10 are pressure on the large cable;
// [FIXME: COMMENT OUT OF DATE?] 11 is separate pressure sensor on circuit board


  // TODO: first 7 temperatures (T1-T7) were Fahrenheit, now Celsius, make sure to elog and update drawing functions with timestamp of change...
 
  // Channels 101-110 are T1-T10
  // Channels 201-204 are HT1-HT4
  std::string clist="";
  clist="101:110,201:204"; // Thermistor channels

  snprintf(cmd, sizeof(cmd)-1, "SENS:FUNC 'RES', (@%s)\r\n", clist.c_str());
  SendCommand(cmd);
  snprintf(cmd, sizeof(cmd)-1, "SENS:RES:RANG 50000, (@%s)\r\n", clist.c_str());
  SendCommand(cmd);
  snprintf(cmd, sizeof(cmd)-1, "SENS:RES:NPLC 2, (@%s)\r\n", clist.c_str());
  SendCommand(cmd);
  snprintf(cmd, sizeof(cmd)-1, "SENS:RES:DIG 5, (@%s)\r\n", clist.c_str());
  SendCommand(cmd);

  //Configuration for voltage reading (used for pressure, humidity) First 4 are from matching H/T sensors temp measurements
  //  Channels 205-208 are HH1-HH4
  //  Channels 209-211 are P1-P3
  clist="205:211"; // Voltage channels (Humidity and Pressure transducers)
  snprintf(cmd, sizeof(cmd)-1, "SENS:FUNC 'VOLT:DC', (@%s)\r\n", clist.c_str());
  SendCommand(cmd);
  snprintf(cmd, sizeof(cmd)-1, "SENS:VOLT:DC:RANGe 10, (@%s)\r\n", clist.c_str());
  SendCommand(cmd);
  snprintf(cmd, sizeof(cmd)-1, "SENS:VOLT:DC:NPLC 2, (@%s)\r\n", clist.c_str());
  SendCommand(cmd);
  snprintf(cmd, sizeof(cmd)-1, "SENS:VOLT:DIG 5, (@%s)\r\n", clist.c_str());
  SendCommand(cmd);
    

  //SendCommand("DISP:ENAB OFF\r\n");
  SendCommand("ROUTe:SCAN (@101:110,201:211);\r\n"); //Channels to be scanned
  // SendCommand("ROUTe:SCAN (@201:211);\r\n"); //Channels to be scanned

  // Channels must be sequential
  // Otherwise it might read wrong voltage
  SendCommand("ROUTe:SCAN:LSELect INT;\r\n"); // internal triggers
  
}

KMultimeter::~KMultimeter()
{
}


int KMultimeter::SendCommand(const char* cmd)
{
  int flags=0;
  int ret=0;

  // TODO: Consider appending the required "\r\n" to commands if not already present.
   
  ret = send(fSocket, cmd, strlen(cmd), flags);
  if (ret < 0) {
    cerr << "Error when sending command!\n";
    cerr << strerror(errno) << endl;
  }
  // if (ret < 0) {
  //   return ret;
  // } else if
  //   try to send remaining data...
  return ret;
}


int KMultimeter::GetResponse(char* buf, const size_t len)
{
  int ret = 0;
  ret = recv(fSocket, buf, len, /*flags=*/0);
  if (ret < 0) {
    cerr << "Error when receiving data!\n";
    cerr << strerror(errno) << endl;
  }
  return ret;
}

int KMultimeter::ReadAll()
{
  //int module=1;
  //cerr << "start measuring " << endl;
  char buf[256];
  memset(buf,0,sizeof(buf));
  lastMeasTime = time(0);
  for (int i = 0; i<fNChannels; i++) {
    SendCommand("READ?\r\n");
    GetResponse(buf,sizeof(buf));
    fLastMeasurements[i] = buf;
    //cerr << "i=" << i << "\t``" << buf << "''"<< endl;
  }
  return 0;
}


int KMultimeter::StopAcq()
{

  SendCommand("ROUT:SCAN:LSEL NONE\r\n"); 
  SendCommand("TRAC:CLE\r\n");
  //SendCommand("DISP:ENAB ON\r\n");
  return 0;
}



int KMultimeter::SaveAll()
{
  double measurements[256];
  // TODO: handle +9.9E37 values returned by Keithley 2701 (indicates overflow reading or NAN)
  for (int i=0; i<fNChannels; i++) {
    measurements[i] = atof(fLastMeasurements[i].c_str());
  }

  // Convert raw resistance and voltage measurements into temperature, humidity, and pressure.
  const int spareFieldValue = 0;
  const int nThermistors = 10;
  const int nHumiditySensors = 4; // each sensor has temperature and RH%
  const int nPressureSensors = 3;
  for (int i = 0; i<fNChannels; i++) {
    // Write data in TSV (tab separated value) format to stdout
    // For example, it should look something like:
    //   "T1	1570650255	21.30293	0"
    //   "T2	1570650255	20.12345	0"
    // with a line for each measurement

    // TODO: rework the following for clarity
    if (i < nThermistors) {
      //cout << "T" << i+1 << "\t" << lastMeasTime << "\t" << measurements[i] << "\t" << spareFieldValue << endl; 
      cout << "T" << i+1 << "\t" << lastMeasTime << "\t" << Convert10kThermToDegC(measurements[i]) << "\t" << spareFieldValue << endl;
    } else if(i >= nThermistors && i < (nThermistors + nHumiditySensors)) {
      cout << "HT" << (i+1) - nThermistors << "\t" << lastMeasTime << "\t" << Convert10kThermToDegC(measurements[i]) << "\t" << spareFieldValue << endl;
    } else if(i >= (nThermistors + nHumiditySensors) && i < (nThermistors + 2*nHumiditySensors)) {
      cout << "HH" << (i+1) - (nThermistors + nHumiditySensors) << "\t" << lastMeasTime << "\t" << ConvertHumidity(measurements[i]) << "\t" << spareFieldValue << endl;
    } else if(i >= (nThermistors + 2*nHumiditySensors) && i < (nThermistors + 2*nHumiditySensors + nPressureSensors)) {
      cout << "P"<< (i+1) - (nThermistors + 2*nHumiditySensors) << "\t" << lastMeasTime << "\t" << ConvertPressure(measurements[i]) << "\t" << spareFieldValue << endl;
    } else {
      cerr << "Error: " << endl;
    }
  }
  
  int nDerivedChannels = nHumiditySensors;
  for (int i=0; i<nDerivedChannels; i++) {
    double value=NAN;
    double temperature = Convert10kThermToDegC(measurements[i+nThermistors]);
    double humidity = ConvertHumidity(measurements[i+nThermistors+nHumiditySensors]);
    //cerr << "temperature = " << temperature << " humidity = " << humidity << endl;
    if (!isnan(temperature) && !isnan(humidity)) {
      value = CalculateDewpoint(temperature, humidity);
    }
    cout << "HD" << (i+1) << "\t" << lastMeasTime << "\t" << value << "\t" << spareFieldValue << endl;
  }

  return 0;
}


//For the MPXXAZ6115A pressure sensors
double KMultimeter::ConvertPressure(double voltage)
{
  double v_supply = 5.0;
  double kPa = (voltage/v_supply+0.095)/.009;
  double psi = kPa/6.89475729; //unit conversion
  return psi;
}


// For the HTM1735LF humidity sensors
double KMultimeter::ConvertHumidity(double voltage/*, double temperature*/)
{
  //double v_supply = 6.0;
  // original code, but looks wrong:    return (voltage-0.01515*v_supply)/(v_supply*0.00636);
  return (38.92*voltage) - 41.98;

  // TODO: Determine whether or not the following temperature correction applies to the installed humidity sensors...
  // Temperature correction, if wanted:
  // True RH = (Sensor RH)/(1.0546-0.00216*T), T in degrees C
}


// Calculate temperature in degrees Celsius from a thermistor resistance in ohms.
double KMultimeter::Convert10kThermToDegC(double resistance)
{
  // This function use the same thermistor parameterization constants as the Keithley 2701 firmware for a 10kohm at 25C (series 440006).  The installed thermistors may be better described by different constants.
  const double a=0.0010295;
  const double b=0.0002391;
  const double c=1.568e-7;
  double t_C = 1.0/(a + b*std::log(resistance) + c*std::pow(std::log(resistance),3)) - 273.15;
  // TODO: handle out of range inputs and determine what to return for invalid input
  return t_C;
}


// Calculates dewpoint (degC) from temperature (degC) and relative humidity (percent)
double KMultimeter::CalculateDewpoint(double temperature_C, double rel_humidity_pct)
{
  double b=18.678, c=257.14, d=234.5;
  double gamma_m = std::log((rel_humidity_pct/100.0)*std::exp( (b-temperature_C/d)*(temperature_C/(c+temperature_C)) ));
  double t_dp_c = c*gamma_m / (b - gamma_m);
  return t_dp_c;
}


//---------------------------------------------------------------------------
int main()
{
  //KMultimeter dmm("192.168.24.70");//real address on DAQ network
  KMultimeter dmm("keithley.sq.pri"); //hostname for the actual address on DAQ network
  //KMultimeter dmm("127.0.0.1"); //localhost for testing

  // TODO: move channel configuration to a centralized location (currently in KMultimeter constructor and SaveAll())
  //    would need: channel number, meas type, range, digits, post processing function (could dependent on other measurements), variable name (e.g., HT1)
  
  if (dmm.IsOkay()) {
    dmm.ReadAll();
    dmm.StopAcq();
    dmm.SaveAll();
  } else {
    cerr << "Error: Exiting..."<<endl;
    return 1;
  }

  return 0;
}
