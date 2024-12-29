CC=		gcc -g -std=c++11 
CPLUS=		g++ -g -std=c++11

FLAGS=		
LFLAGS=	

EPICSINC=	-I$(EPICS_BASE)/include/ -I$(EPICS_BASE)/include/os/Linux/ -I$(EPICS_BASE)/src/libCom/osi/os/Linux/ -I$(EPICS_BASE)/src/libCom/osi/os/posix/ -I$(EPICS_BASE)/include/compiler/gcc/
ROOTINC = 	-I $(ROOTSYS)/include/
INCLUDEDIR =	$(EPICSINC) $(ROOTINC)

clean:
			rm -f $(OBJECTS) $(PROGRAM)

all:	 	TEPICcnfg.o  TEPICsyst.o  TSLCOcnfg.o  TSLCOepic.o  TSLCOlogs.o  TSLCOsyst.o

%.o:			%.cc 
			$(CPLUS) $(CFLAGS) $(INCLUDEDIR) -o $@ -c $<
