import numpy as np
import math

from scipy import signal   #for making a filter
#from random import random

from genericsynth import synthInterface as SI
from DSClap import DSClap  # This is "event" synthesizer this pattern synth will use

# Repeat an array float(n) times and concatenate them 
def repeatSeg(seg,n) : 
        return  np.concatenate((np.tile(seg,int(n)), seg[:int(round((n%1)*len(seg)))]))

# Exend an event (time) list by concatenating the sequence with seqDur added to the events in each successive repeat.
def extendEventSequence(oseq, seqDur, durationSecs) :
        cyclelength=len(oseq)

        newEvList=[]
        newEvNum=0
        revNum=0
        revSeqEvNum=0
        t=oseq[revSeqEvNum]
        while t < durationSecs :
                
                newEvList.append(t)

                # now get the next one
                newEvNum=newEvNum+1
                revNum=newEvNum//cyclelength
                revSeqEvNum=newEvNum%cyclelength
                t=oseq[revSeqEvNum]+revNum*seqDur
        return newEvList

################################################################################################################
'''
        if cylinders is > 1, then a sequence is made of length cylinders/rate which is repeated for the durationSecs requested in generate()
        if cylinders is <=1, the a squence of length durationSecs is created with no repeating subsequences.
'''
class DSClapperSynth(SI.MySoundModel) :
        '''
              @rng - pass in your own, or the default will be the same everytime 
        '''
        def __init__(self,  rate_exp=0, irreg_exp=1, evdur=.003,  cylinders=0, evamp=.5, rng=None) :

                SI.MySoundModel.__init__(self)
                if rng==None :
                        print(f"ClapperSynth creating new RNG")
                        self.rng = np.random.default_rng(18005551212)
                else :
                        self.rng = rng

                #get the sub synth
                self.evSynth=DSClap(amp=evamp, rng=self.rng)

                self.__addParam__("rate_exp", -10, 10, rate_exp, synth_doc="events per second (eps) = 2^rate_exp")
                self.__addParam__("irreg_exp", 0, 50, irreg_exp, synth_doc="irregularity=.1*irreg_exp*np.power(10,irreg_exp), gaussian sd=irregularity/eps")
                self.__addParam__("evdur", .001, 10, evdur, synth_doc="duration of individual events")
                self.__addParam__("cylinders", 0, 64, cylinders, synth_doc="event timing repeats every 'cylynders' events")

                #My "hard coded" defaults for the subsynth
                self.evSynth.setParam('amp', .4) #should be smaller for overlapping events...


                self.numResonators=1
                for rn in range(self.numResonators) :
                        # Parallel Resonators 
                        self.__addParam__("f"+str(rn), 2, 2000, 1000., synth_doc="resonator f"+str(rn))
                        self.__addParam__("q"+str(rn), .1, 40, .5, synth_doc="resonator q"+str(rn))
                        self.__addParam__("a"+str(rn), 0, 1, 1., synth_doc="resonator a"+str(rn))



        #-----------------------------------------------------------------------

        '''
                Just a shorthand for setting all resonance parameters in one call with 3 array args for f, q, a
        '''
        def setResonances(self, f, q, a) :
                assert len(f)==len(q)==len(q), f"setResonance: All arrays must be of length {self.numResonators}"
                if len(f) != self.numResonators :
                        print(f"WARNING: Initializing with setRsonances with array lengths longer than numbResonators (={self.numResonators})")
                for i in range(self.numResonators) :
                        self.setParam("f"+str(i), f[i])
                        self.setParam("q"+str(i), q[i])
                        self.setParam("a"+str(i), a[i])
                       

        '''
                Random resonance features for the engine
        '''
        def setRandomResonance(self) :
                for i in range(self.numResonators) :
                        self.setParam("f"+str(i), 120*(i+.5*self.rng.random()))
                        self.setParam("q"+str(i), 10*self.rng.random())
                        self.setParam("a"+str(i), 1-i/(self.numResonators+4))
                        print(f"setRandomResonance: For reson {i}, f = {self.getParam('f'+str(i))}. q={self.getParam('q'+str(i))} and a= {self.getParam('a'+str(i))}") 
                        print(f"---")

        '''
                Override of base model method
        '''
        def generate(self,  durationSecs) :

                cylinders=self.getParam("cylinders")
                
                if cylinders > 1 :
                        #how much time for n piston pops?
                        revdur=cylinders/np.power(2,self.getParam("rate_exp"))
                        print(f"revdur={revdur} and durationSecs={durationSecs}")
                        revdur=np.minimum(revdur,durationSecs) #don't compute events that go beyond signal generation length
                        print(f"      the min of the two is ")

                        revSeq=SI.noisySpacingTimeList(self.getParam("rate_exp"), self.getParam("irreg_exp"), revdur, rng=self.rng)
                        elist=extendEventSequence(revSeq, revdur, durationSecs)
                else:
                        elist=SI.noisySpacingTimeList(self.getParam("rate_exp"), self.getParam("irreg_exp"), durationSecs, rng=self.rng)

                return self.elist2signal(elist, durationSecs)


        ''' Take a list of event times, and return our (possibly overlapped) events at those times'''
        def elist2signal(self, elist, sigLenSecs) :
                numSamples=self.sr*sigLenSecs
                sig=np.zeros(sigLenSecs*self.sr)

                #print(f"Evdur is {self.getParam('evdur')} and ioi is {1./np.power(2,self.getParam('rate_exp'))}")
                dur=np.minimum(self.getParam('evdur'), 1./np.power(2,self.getParam('rate_exp')))

                for nf in elist :
                        startsamp=int(round(nf*self.sr))%numSamples
                        gensig = self.evSynth.generate(dur, dur+.01)
                        sig = SI.addin(gensig, sig, startsamp)

                outsig=np.zeros((len(sig)))


                for i in range(self.numResonators) :
                        # Design peak filter
                        b, a = signal.iirpeak(self.getParam("f"+str(i)), self.getParam("q"+str(i)), self.sr)
                        #use it
                        foo=signal.lfilter(b, a, sig)
                        outsig= outsig+self.getParam("a"+str(i))*signal.lfilter(b, a, foo)


                # envelope with 10ms attack, decay at the beginning and the end of the whole signal. Avoid rude cuts
                length = int(round(sigLenSecs*self.sr)) # in samples
                ltrans = round(.01*self.sr)
                midms=length-2*ltrans-1
                ampenv=SI.bkpoint([0,1,1,0,0],[ltrans,midms,ltrans,1])

                return np.array(ampenv)*outsig