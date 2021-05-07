import numpy as np
import math

from scipy import signal   #for making a filter
#from random import random

from genericsynth import synthInterface as SI
from DSClapperSynth import DSClapperSynth  # This is "event" synthesizer this pattern synth will use



################################################################################################################
class DSApplauseSynth(SI.MySoundModel) :
        '''
              @rng - pass in your own, or the default will be the same everytime
        '''

        def __init__(self,  numClappers=20, rate_exp=2, irreg_exp=.6, evdur=.003,  cylinders=0, evamp=.5, rng=None) :
                SI.MySoundModel.__init__(self)
                if rng==None :
                        self.rng = np.random.default_rng(18005551212) #Arbitrary seed - just so repeatable
                else :
                        self.rng = rng

                #array of children
                self.clappers=[]

                def setNumClappers(n) : 
                        n=int(n)
                        numClappers=int(self.getParam("numClappers"))
                        print(f"changing numClappers from {numClappers} to {n}")
                        if n > numClappers :
                                for cn in range(numClappers, n) :
                                        self.clappers.append(DSClapperSynth(rate_exp=rate_exp, irreg_exp=irreg_exp, evdur=evdur,  cylinders=cylinders, evamp=evamp, rng=self.rng))

                                        self.clappers[cn].setParam("rate_exp",  self.getParam("rate_exp")) # will make 2^1 events per second
                                        self.clappers[cn].setParam("irreg_exp", self.getParam("irreg_exp"))
                                        self.clappers[cn].setParam("cylinders", self.getParam("cylinders"))
                                        #self.clappers[cn].setParam('evamp', .4) #should be smaller for overlapping events...

                                        self.clappers[cn].setResonances([1000],[1],[1])

                #---------
                ''' This is for all the clapper parameters exposed by applause.
                    It just turns around and sets the parameter with the same name on all the individual clappers
                '''
                def setChildrenParam(param, v):
                        numClappers=self.getParam("numClappers")
                        for cn in range(0, int(numClappers)) :
                                self.clappers[cn].setParam(param,v)
                #---------

                self.__addParam__("rate_exp", -10, 10, rate_exp, 
                        cb=lambda v: setChildrenParam("rate_exp", v),
                        synth_doc="events per second (eps) = 2^rate_exp")

                self.__addParam__("irreg_exp", 0, 50, irreg_exp, 
                        cb=lambda v: setChildrenParam("irreg_exp", v),
                        synth_doc="irregularity=.1*irreg_exp*np.power(10,irreg_exp), gaussian sd=irregularity/eps")
                
                self.__addParam__("evdur", .001, 10, evdur, 
                        cb=lambda v: setChildrenParam("evdur", v),
                        synth_doc="duration of individual events")

                self.__addParam__("cylinders", 0, 64, cylinders, 
                        cb=lambda v: setChildrenParam("cylinders", v),
                        synth_doc="event timing repeats every 'cylynders' events")

                # A bit superfluous, but the applaus has a post-clappers filter, broad band by default
                # Some room reverb would probably work better
                #self.numResonators=1
                #for rn in range(self.numResonators) :
                #        # Parallel Resonators 
                #        self.__addParam__("f"+str(rn), 2, 2000, 60., synth_doc="resonator f"+str(rn))
                #        self.__addParam__("q"+str(rn), .1, 40, 3., synth_doc="resonator q"+str(rn))
                #        self.__addParam__("a"+str(rn), 0, 1, 1., synth_doc="resonator a"+str(rn))

                self.__addParam__("numClappers", 1, 50, 0, 
                        lambda v : setNumClappers(v), 
                        synth_doc="number of clappers")

                # Now create go those children
                self.setParam('numClappers', numClappers)

                
        '''
                Override of base model method.
                Just generate a bunch of individual clappers, and sum them up.
        '''
        def generate(self,  durationSecs) :
                sig=self.clappers[0].generate(durationSecs)
                print(f"numClappers is {int(self.getParam('numClappers'))}")
                for cn in range(1,int(self.getParam("numClappers"))) :
                      sig = sig + self.clappers[cn].generate(durationSecs)   
                return sig


