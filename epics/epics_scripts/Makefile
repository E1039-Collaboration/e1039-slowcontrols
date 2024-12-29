FILLEPICSPGM=	fill_epics_var_1
PROGRAM=	$(FILLEPICSPGM)

CC=		gcc -g -std=c++11 
CPLUS=		g++ -g -std=c++11

FLAGS=		
EPICSFLAGS=	-DOSITHREAD_USE_DEFAULT_STACK -D_X86_ -DUNIX -Dlinux
LFLAGS=	

#ROOTLIBS=	-L $(ROOTSYS)/lib -lRint -lCint 
ROOTLIBS=	-L $(ROOTSYS)/lib -lRint 
EPICSLIBS=	-L $(EPICS_BASE)/lib/linux-x86_64 -lca -lCom
LIBS=		-lCore $(ROOTLIBS) $(EPICSLIBS) -ldl -lm 

EPICSINC=	-I$(EPICS_BASE)/include/ -I$(EPICS_BASE)/include/os/Linux/ -I$(EPICS_BASE)/src/libCom/osi/os/Linux/ -I$(EPICS_BASE)/src/libCom/osi/os/posix/ -I$(EPICS_BASE)/include/compiler/gcc/
ROOTINC = 	-I $(ROOTSYS)/include/
INCLUDEDIR =	$(EPICSINC) $(ROOTINC)

FILLEPICSSRC=		fill_epics_var_1.cc

FILLEPICSOBJ=		fill_epics_var_1.o mclas/TEPICcnfg.o  mclas/TEPICsyst.o  mclas/TSLCOcnfg.o  mclas/TSLCOepic.o  mclas/TSLCOlogs.o  mclas/TSLCOsyst.o

OBJECTS=		$(FILLEPICSOBJ)

CFLAGS=			$(FLAGS) 

clean:
			rm -f $(OBJECTS) $(PROGRAM)

all:			$(PROGRAM)

$(FILLEPICSPGM):		$(FILLEPICSOBJ)
			$(CPLUS) $(CFLAGS) \
			$(LFLAGS) $(EPICSFLAGS) -o $(FILLEPICSPGM) $(FILLEPICSOBJ)\
			$(LIBS)

$(FILLEPICSOBJ):		$(FILLEPICSSRC)

%.o:			%.cc $(FILLEPICS_INC_FILES)
			$(CPLUS) $(CFLAGS)  $(EPICSFLAGS)  $(INCLUDEDIR) -o $@ -c $<
