TIMELOGEPICSPGM=	timeLogEpics
PROGRAM=	$(TIMELOGEPICSPGM)

CC=		gcc -g -std=c++11 
CPLUS=		g++ -g -std=c++11

FLAGS=		-DUNIX -DLINUX
EPICSFLAGS=	-DLinux-D_GNU_SOURCE -DOSITHREAD_USE_DEFAULT_STACK -D_X86_ -DUNIX -Dlinux
LFLAGS=

LIBS=		-L $(DIRLIB) -lncurses -lpthread -ldl -lm
EPICSLIBS=	-L $(EPICS_BASE)/lib/linux-x86_64 -lca -lCom

EPICSINC=	-I$(EPICS_BASE)/include/ -I$(EPICS_BASE)/include/os/Linux/ -I$(EPICS_BASE)/src/libCom/osi/os/Linux/ -I$(EPICS_BASE)/src/libCom/osi/os/posix/ -I$(EPICS_BASE)/include/compiler/gcc/

TIMELOGEPICSSRC=		timeLogEpics.cc

TIMELOGEPICSOBJ=		timeLogEpics.o

OBJECTS=		$(TIMELOGEPICSOBJ)

CFLAGS=			$(FLAGS) 

clean:
			rm -f $(OBJECTS) $(PROGRAM)

all:			$(PROGRAM)

$(TIMELOGEPICSPGM):		$(TIMELOGEPICSOBJ)
			$(CPLUS) $(CFLAGS) \
			$(LFLAGS) $(EPICSFLAGS) -o $(TIMELOGEPICSPGM) $(TIMELOGEPICSOBJ)\
			$(LIBS) $(EPICSLIBS)

$(TIMELOGEPICSOBJ):		$(TIMELOGEPICSSRC)

%.o:			%.cc $(TIMELOGEPICS_INC_FILES)
			$(CPLUS) $(CFLAGS)  $(EPICSFLAGS)  $(INCLUDEDIR) $(EPICSINC) -o $@ -c $<
