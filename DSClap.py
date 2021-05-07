import numpy as np
#import seaborn as sns
from scipy import signal
import math
#import sys
import soundfile as sf
import librosa

from genericsynth import synthInterface as SI

class DSClap(SI.MySoundModel) :
	'''
	      @rng - pass in your own, or the default will be the same everytime  
	'''
	def __init__(self,  noiseLevel=.8, amp=1, rng=None) :
		SI.MySoundModel.__init__(self)

		self.numClaps=35 # number of files in the sounds folder.

		if rng==None :
			print(f"Clap creating new RNG")
			self.rng = np.random.default_rng(18005551212)
		else :
			self.rng = rng

		#create a dictionary of the parameters this synth will use
		self.__addParam__("amp", 0, 1, amp)

		self.claps=[]
		for i in range(self.numClaps) :
			data, samplerate = sf.read(f'sounds/CLAP{i+1}a.wav')
			self.claps.append(np.array(librosa.core.resample(data, samplerate, self.sr)))

	'''
		Override of base model method
	'''
	def generate(self, noiseLenSecs, sigLenSecs,  amp=None) :

		if amp==None : amp=self.getParam("amp")

		ticksamps = int(round(noiseLenSecs*self.sr)) # in samples
		outsig=np.zeros((ticksamps))

		#clappernum=self.numClaps*self.rng.random((1))
		clappernum=int(self.numClaps*self.rng.random())
		copylen=np.minimum(ticksamps, len(self.claps[clappernum]))
		outsig[0:  copylen]=self.claps[clappernum][:copylen]*self.getParam("amp")


		return outsig

