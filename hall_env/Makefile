CXX = g++
CXXFLAGS = -Wall -Wextra -pedantic -O2
#CXXFLAGS += -g
#CXXFLAGS += -Werror

kscan: keithley2701_ctl.cc 
	$(CXX) $(CXXFLAGS) -o $@ $<

clean:
	rm -f kscan
