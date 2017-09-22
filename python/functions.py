import numpy as np


def gaussFilt(X, wdim = (1,)):
	'''
		Gaussian Filtering in 1 or 2d.		
		Made to fit matlab
	'''
	from scipy.signal import gaussian

	if len(wdim) == 1:
		from scipy.ndimage.filters import convolve1d
		l1 = len(X)
		N1 = wdim[0]*10
		S1 = (N1-1)/float(2*5)
		gw = gaussian(N1, S1)
		gw = gw/gw.sum()
		#convolution
		if len(X.shape) == 2:
			filtered_X = convolve1d(X, gw, axis = 1)
		elif len(X.shape) == 1:
			filtered_X = convolve1d(X, gw)
		return filtered_X	
	elif len(wdim) == 2:
		from scipy.signal import convolve2d
		def conv2(x, y, mode='same'):
			return np.rot90(convolve2d(np.rot90(x, 2), np.rot90(y, 2), mode=mode), 2)			

		l1, l2 = X.shape
		N1, N2 = wdim		
		# create bordered matrix
		Xf = np.flipud(X)
		bordered_X = np.vstack([
				np.hstack([
					np.fliplr(Xf),Xf,np.fliplr(Xf)
				]),
				np.hstack([
					np.fliplr(X),X,np.fliplr(X)
				]),
				np.hstack([
					np.fliplr(Xf),Xf,np.fliplr(Xf)
				]),
			])
		# gaussian windows
		N1 = N1*10
		N2 = N2*10
		S1 = (N1-1)/float(2*5)
		S2 = (N2-1)/float(2*5)
		gw = np.vstack(gaussian(N1,S1))*gaussian(N2,S2)
		gw = gw/gw.sum()
		# convolution
		filtered_X = conv2(bordered_X, gw, mode ='same')
		return filtered_X[l1:l1+l1,l2:l2+l2]
	else :
		print("Error, dimensions larger than 2")
		return

def derivative(x, f):
	''' 
		Compute the derivative of a time serie
		Used for jPCA
	'''
	from scipy.stats import linregress
	fish = np.zeros(len(f))
	slopes_ = []
	tmpf = np.hstack((f[0],f,f[-1])) # not circular
	binsize = x[1]-x[0]	
	tmpx = np.hstack((np.array([x[0]-binsize]),x,np.array([x[-1]+binsize])))	
	# plot(tmpx, tmpf, 'o')
	# plot(x, f, '+')
	for i in range(len(f)):
		slope, intercept, r_value, p_value, std_err = linregress(tmpx[i:i+3], tmpf[i:i+3])
		slopes_.append(slope)	
		# plot(tmpx[i:i+3], tmpx[i:i+3]*slope+intercept, '-')
	return np.array(slopes_)/binsize

def buildHMap(n, ):
	'''
		build the H mapping for a given n
		used for the jPCA
	'''
	from scipy.sparse import lil_matrix
	M = np.zeros((n,n), dtype = np.int)
	M[np.triu_indices(n,1)] = np.arange(1,int(n*(n-1)/2)+1)
	M = M - M.transpose()
	m = np.vstack(M.reshape(n*n))
	k = np.vstack(M[np.triu_indices(n,1)]).astype('int')
	H = lil_matrix( (len(m), len(k)), dtype = np.float16)
	H = np.zeros( (len(m), len(k) ))
	# first column 
	for i in k.flatten():
		# positive
		H[np.where(m == i)[0][0],i-1] = 1.0
		# negative
		H[np.where(m == -i)[0][0],i-1] = -1.0
	return H

def crossValidation(data, times, n_cv = 10, dims = (6,2)):
	''' 
		Perform a randomized cross-validation 
		of PCA -> jPCA
		dims = (dimension reduction of pca, dimension reduction of jpca)
	'''
	from sklearn.model_selection import KFold
	from sklearn.decomposition import PCA
	cv_kf = KFold(n_splits = n_cv, shuffle = True, random_state=42)
	skf = cv_kf.split(data)
	scorecv = np.zeros( (data.shape[0],2) )
	phicv = np.zeros(data.shape[0])
	n = dims[0]
	for idx_r, idx_t in skf:
		Xtrain = data[idx_r, :]
		Xtest  = data[idx_t, :]		
		pca = PCA(n_components = n)
		zpca = pca.fit_transform(Xtrain)
		X = pca.components_.transpose()
		dX = np.hstack([np.vstack(derivative(times, X[:,i])) for i in range(X.shape[1])])
		#build the H mapping for a given n
		# work by lines but H is made for column based
		n = X.shape[1]
		H = buildHMap(n)
		# X tilde
		Xtilde = np.zeros( (X.shape[0]*X.shape[1], X.shape[1]*X.shape[1]) )
		for i, j in zip( (np.arange(0,n**2,n) ), np.arange(0, n*X.shape[0], X.shape[0]) ):
			Xtilde[j:j+X.shape[0],i:i+X.shape[1]] = X
		# put dx in columns
		dXv = np.vstack(dX.transpose().reshape(X.shape[0]*X.shape[1]))
		# multiply Xtilde by H
		XtH = np.dot(Xtilde, H)
		# solve XtH k = dXv
		k, residuals, rank, s = np.linalg.lstsq(XtH, dXv)
		# multiply by H to get m then M
		m = np.dot(H, k)
		Mskew = m.reshape(n,n).transpose()
		# Contruct the two vectors for projection with MSKEW
		evalues, evectors = np.linalg.eig(Mskew)
		# index = np.argsort(evalues).reshape(5,2)[:,1]
		index = np.argsort(np.array([np.linalg.norm(i) for i in evalues]).reshape(int(n/2),2)[:,0])
		evectors = evectors.transpose().reshape(int(n/2),2,n)
		u = np.vstack([
						np.real(evectors[index[-1]][0] + evectors[index[-1]][1]),
						np.imag(evectors[index[-1]][0] - evectors[index[-1]][1])
					]).transpose()
		# PRoject X
		rX = np.dot(X, u)
		score = np.dot(Xtest, rX)
		phi = np.mod(np.arctan2(score[:,0], score[:,1]), 2*np.pi)
		scorecv[idx_t,:] = score
		phicv[idx_t] = phi

	return np.array(scorecv), np.array(phicv)

def quartiles(data, times, n_fold = 4, dims = (6,2)):
	''' 		
		PCA -> jPCA
		dims = (dimension reduction of pca, dimension reduction of jpca)
	'''	
	from sklearn.decomposition import PCA
	indexdata = np.linspace(0,len(data),n_fold+1).astype('int')	
	scorecv = []
	phicv = []
	n = dims[0]
	jpca = []
	for i in range(n_fold):
		Xtrain = data[indexdata[i]:indexdata[i+1], :]		
		pca = PCA(n_components = n)
		zpca = pca.fit_transform(Xtrain)
		X = pca.components_.transpose()
		dX = np.hstack([np.vstack(derivative(times, X[:,i])) for i in range(X.shape[1])])
		#build the H mapping for a given n
		# work by lines but H is made for column based
		n = X.shape[1]
		H = buildHMap(n)
		# X tilde
		Xtilde = np.zeros( (X.shape[0]*X.shape[1], X.shape[1]*X.shape[1]) )
		for i, j in zip( (np.arange(0,n**2,n) ), np.arange(0, n*X.shape[0], X.shape[0]) ):
			Xtilde[j:j+X.shape[0],i:i+X.shape[1]] = X
		# put dx in columns
		dXv = np.vstack(dX.transpose().reshape(X.shape[0]*X.shape[1]))
		# multiply Xtilde by H
		XtH = np.dot(Xtilde, H)
		# solve XtH k = dXv
		k, residuals, rank, s = np.linalg.lstsq(XtH, dXv)
		# multiply by H to get m then M
		m = np.dot(H, k)
		Mskew = m.reshape(n,n).transpose()
		# Contruct the two vectors for projection with MSKEW
		evalues, evectors = np.linalg.eig(Mskew)
		# index = np.argsort(evalues).reshape(5,2)[:,1]
		index = np.argsort(np.array([np.linalg.norm(i) for i in evalues]).reshape(int(n/2),2)[:,0])
		evectors = evectors.transpose().reshape(int(n/2),2,n)
		u = np.vstack([
						np.real(evectors[index[-1]][0] + evectors[index[-1]][1]),
						np.imag(evectors[index[-1]][0] - evectors[index[-1]][1])
					]).transpose()
		# PRoject X
		rX = np.dot(X, u)
		score = np.dot(Xtrain, rX)
		phi = np.mod(np.arctan2(score[:,1], score[:,0]), 2*np.pi)
		scorecv.append(score)
		phicv.append(phi)
		jpca.append(rX)

	index = np.array([np.arange(indexdata[i],indexdata[i+1]) for i in range(len(indexdata)-1)])
	return np.array(scorecv), np.array(phicv), index, np.array(jpca)

def downsample(tsd, up, down):
	import scipy.signal
	import neuroseries as nts
	dtsd = scipy.signal.resample_poly(tsd.values, up, down)
	dt = tsd.as_units('s').index.values[np.arange(0, tsd.shape[0], down)]
	if len(tsd.shape) == 1:		
		return nts.Tsd(dt, dtsd, time_units = 's')
	elif len(tsd.shape) == 2:
		return nts.TsdFrame(dt, dtsd, time_units = 's')

def getPhase(lfp, fmin, fmax, nbins, fsamp, power = False):
	""" Continuous Wavelets Transform
		return phase of lfp in a Tsd array
	"""
	import neuroseries as nts
	from Wavelets import MyMorlet as Morlet
	if isinstance(lfp, nts.time_series.TsdFrame):
		allphase 		= nts.TsdFrame(lfp.index.values, np.zeros(lfp.shape))
		allpwr 			= nts.TsdFrame(lfp.index.values, np.zeros(lfp.shape))
		for i in lfp.keys():
			allphase[i], allpwr[i] = getPhase(lfp[i], fmin, fmax, nbins, fsamp, power = True)
		if power:
			return allphase, allpwr
		else:
			return allphase			

	elif isinstance(lfp, nts.time_series.Tsd):
		cw 				= Morlet(lfp.values, fmin, fmax, nbins, fsamp)
		cwt 			= cw.getdata()
		cwt 			= np.flip(cwt, axis = 0)
		wave 			= np.abs(cwt)**2.0
		phases 			= np.arctan2(np.imag(cwt), np.real(cwt)).transpose()	
		cwt 			= None
		index 			= np.argmax(wave, 0)
		# memory problem here, need to loop
		phase 			= np.zeros(len(index))	
		for i in range(len(index)) : phase[i] = phases[i,index[i]]
		phases 			= None
		if power: 
			pwrs 		= cw.getpower()		
			pwr 		= np.zeros(len(index))		
			for i in range(len(index)):
				pwr[i] = pwrs[index[i],i]	
			return nts.Tsd(lfp.index.values, phase), nts.Tsd(lfp.index.values, pwr)
		else:
			return nts.Tsd(lfp.index.values, phase)

def getPeaksandTroughs(lfp, min_points):
	"""	 
		At 250Hz (1250/5), 2 troughs cannont be closer than 20 (min_points) points (if theta reaches 12Hz);		
	"""
	import neuroseries as nts
	import scipy.signal
	if isinstance(lfp, nts.time_series.Tsd):
		troughs 		= nts.Tsd(lfp.as_series().iloc[scipy.signal.argrelmin(lfp.values, order =min_points)[0]], time_units = 'us')
		peaks 			= nts.Tsd(lfp.as_series().iloc[scipy.signal.argrelmax(lfp.values, order =min_points)[0]], time_units = 'us')
		tmp 			= nts.Tsd(troughs.realign(peaks, align = 'next').as_series().drop_duplicates('first')) # eliminate double peaks
		peaks			= peaks[tmp.index]
		tmp 			= nts.Tsd(peaks.realign(troughs, align = 'prev').as_series().drop_duplicates('first')) # eliminate double troughs
		troughs 		= troughs[tmp.index]
		return (peaks, troughs)
	elif isinstance(lfp, nts.time_series.TsdFrame):
		peaks 			= nts.TsdFrame(lfp.index.values, np.zeros(lfp.shape))
		troughs			= nts.TsdFrame(lfp.index.values, np.zeros(lfp.shape))
		for i in lfp.keys():
			peaks[i], troughs[i] = getPeaksandTroughs(lfp[i], min_points)
		return (peaks, troughs)

def getCircularMean(theta, high = np.pi, low = -np.pi):
	""" 
	see CircularMean.m in TSToolbox_Utils/Stats/CircularMean.m
	or Fisher N.I. Analysis of Circular Data p. 30-35
	"""
	from scipy.stats import circmean
	n 			= float(len(theta))
	alpha 		= 0.05	
	S 			= np.sum(np.sin(theta))
	C 			= np.sum(np.cos(theta))
	mu 			= circmean(theta, high, low)
	Rmean		= np.sqrt(S**2.0 + C**2.0) / n
	rho2 		= np.sum(np.cos(2*(theta - mu)))/n
	delta		= (1 - rho2) / (2* Rmean**2)
	sigma		= np.sqrt(-2.0*np.log(Rmean))
	Z 			= n * Rmean**2.0
	pval 		= np.exp(-Z)*(1+(2*Z-Z**2.0)/(4*n) - (24*Z - 132*Z**2.0 + 76*Z**3.0 - 9*Z**4.0)/(288.0*n**2.0))
	if Rmean < 0.5:
		Kappa 	= 2.0*Rmean + Rmean**3.0 + 5*(Rmean**5.0)/6.0
	elif Rmean >= 0.53 and Rmean < 0.85:
		Kappa 	= -0.4 + 1.39*Rmean + 0.43/(1-Rmean)
	else:
		Kappa 	= 1/(Rmean**3.0 - 4*Rmean**2.0 + 3*Rmean)
	if n < 15:
		if Kappa < 2:
			Kappa = np.max([Kappa-2/(n*Kappa),0])
		else:
			Kappa = (((n-1)**3) * Kappa)/(n**3 + n)
	return (mu, Kappa, pval)

def butter_bandpass(lowcut, highcut, fs, order=5):
	from scipy.signal import butter
	nyq = 0.5 * fs
	low = lowcut / nyq
	high = highcut / nyq
	b, a = butter(order, [low, high], btype='band')
	return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
	from scipy.signal import lfilter
	b, a = butter_bandpass(lowcut, highcut, fs, order=order)
	y = lfilter(b, a, data)
	return y

def getFiringRate(tsd_spike, bins):
	"""bins shoud be in us
	"""
	import neuroseries as nts
	frate 		= nts.Tsd(bins, np.zeros(len(bins)))
	bins_size 	= (bins[1] - bins[0])*1.e-6 # convert to s for Hz
	if type(tsd_spike) is dict:
		for n in tsd_spike.keys():
			index = np.digitize(tsd_spike[n].index.values, bins)
			for i in index:
				frate[bins[i]] += 1.0
		frate = nts.Tsd(bins+(bins[1]-bins[0])/2, frate.values/len(tsd_spike)/bins_size)
		return frate
	else:
		index 	= np.digitize(tsd_spike.index.values, bins)
		for i in index:
			frate[bins[i]] += 1.0
		frate = nts.Tsd(bins+(bins[1]-bins[0])/2, frate.values/bins_size)
		return frate	

def computePhaseModulation(phase, spikes, ep, get_phase = False):
	n_neuron 		= len(spikes)
	spikes_evt		= {n:spikes[n].restrict(ep) for n in spikes.keys()}
	spikes_phase	= {n:phase.realign(spikes_evt[n], align = 'closest') for n in spikes_evt.keys()}
	evt_mod 		= np.ones((n_neuron,3))*np.nan	
	for n in range(len(spikes_phase.keys())):
		neuron = list(spikes_phase.keys())[n]
		ph = spikes_phase[neuron]
		mu, kappa, pval = getCircularMean(ph.values)
		evt_mod[n] = np.array([mu, pval, kappa])
	if get_phase:
		return evt_mod, spikes_phase
	else:
		return evt_mod
	
#########################################################
# CORRELATION
#########################################################
def crossCorr(t1, t2, binsize, nbins):
	''' 
		Fast crossCorr 
	'''
	nt1 = len(t1)
	nt2 = len(t2)
	if np.floor(nbins/2)*2 == nbins:
		nbins = nbins+1

	m = -binsize*((nbins+1)/2)
	B = np.zeros(nbins)
	for j in range(nbins):
		B[j] = m+j*binsize

	w = ((nbins/2) * binsize)
	C = np.zeros(nbins)
	i2 = 1

	for i1 in range(nt1):
		lbound = t1[i1] - w
		while i2 < nt2 and t2[i2] < lbound:
			i2 = i2+1
		while i2 > 1 and t2[i2-1] > lbound:
			i2 = i2-1

		rbound = lbound
		l = i2
		for j in range(nbins):
			k = 0
			rbound = rbound+binsize
			while l < nt2 and t2[l] < rbound:
				l = l+1
				k = k+1

			C[j] += k

	# for j in range(nbins):
	# C[j] = C[j] / (nt1 * binsize)
	C = C/(nt1 * binsize/1000)

	return C

def crossCorr2(t1, t2, binsize, nbins):
	'''
		Slow crossCorr
	'''
	window = np.arange(-binsize*(nbins/2),binsize*(nbins/2)+2*binsize,binsize) - (binsize/2.)
	allcount = np.zeros(nbins+1)
	for e in t1:
		mwind = window + e
		# need to add a zero bin and an infinite bin in mwind
		mwind = np.array([-1.0] + list(mwind) + [np.max([t1.max(),t2.max()])+binsize])	
		index = np.digitize(t2, mwind)
		# index larger than 2 and lower than mwind.shape[0]-1
		# count each occurences 
		count = np.array([np.sum(index == i) for i in range(2,mwind.shape[0]-1)])
		allcount += np.array(count)
	allcount = allcount/(float(len(t1))*binsize / 1000)
	return allcount

def xcrossCorr(t1, t2, binsize, nbins, nbiter, jitter):	
	allcount = crossCorr(t1, t2, binsize, nbins)
	# JITTERING by randomizing the interval position
	jitter_count = np.zeros((nbiter,nbins+1))
	t0 = t2[0]
	iset = np.hstack((np.vstack(t2[0:-1]),np.vstack(t2[1:])))		
	length = iset[:,1] - iset[:,0]
	t2_shuffle = np.zeros(len(t2))
	t2_shuffle[0] = t0
	for i in range(nbiter):				
		shuff = np.random.permutation(length)		
		t2_shuffle[1:] = t0+np.cumsum(shuff)		
		jitter_count[i,:] = crossCorr(t1, t2_shuffle, binsize, nbins)
	mean_jitter_count = jitter_count.mean(0)		
	std_jitter_count = jitter_count.std(0)
	return (allcount - mean_jitter_count)/std_jitter_count

def corr_circular_(alpha1, alpha2):
	axis = None
	from pycircstat import center
	from scipy.stats import norm
	alpha1_bar, alpha2_bar = center(alpha1, alpha2, axis=axis)
	num = np.sum(np.sin(alpha1_bar) * np.sin(alpha2_bar), axis=axis)
	den = np.sqrt(np.sum(np.sin(alpha1_bar) ** 2, axis=axis) * np.sum(np.sin(alpha2_bar) ** 2, axis=axis))
	rho = num/den
	# pvalue
	l20 = np.mean(np.sin(alpha1 - alpha1_bar)**2)
	l02 = np.mean(np.sin(alpha2 - alpha2_bar)**2)
	l22 = np.mean((np.sin(alpha1-alpha1_bar)**2) * (np.sin(alpha2 - alpha2_bar)**2))
	ts = np.sqrt((float(len(alpha1)) * l20 * l02)/l22) * rho
	pval = 2.0 * (1.0 - norm.cdf(np.abs(ts)))

	return rho, pval

#########################################################
# WRAPPERS
#########################################################
def loadShankStructure(generalinfo):
	shankStructure = {}
	for k,i in zip(generalinfo['shankStructure'][0][0][0][0],range(len(generalinfo['shankStructure'][0][0][0][0]))):
		if len(generalinfo['shankStructure'][0][0][1][0][i]):
			shankStructure[k[0]] = generalinfo['shankStructure'][0][0][1][0][i][0]-1
		else :
			shankStructure[k[0]] = []
	
	return shankStructure	

def loadSpikeData(path, index):
	# units shoud be the value to convert in s 
	import scipy.io
	import neuroseries as nts
	spikedata = scipy.io.loadmat(path)
	shank = spikedata['shank']
	shankIndex = np.where(shank == index)[0]

	spikes = {}	
	for i in shankIndex:	
		spikes[i] = nts.Ts(spikedata['S'][0][0][0][i][0][0][0][1][0][0][2], time_units = 's')

	a = spikes[0].as_units('s').index.values	
	if ((a[-1]-a[0])/60.)/60. > 20. : # VERY BAD		
		spikes = {}	
		for i in shankIndex:	
			spikes[i] = nts.Ts(spikedata['S'][0][0][0][i][0][0][0][1][0][0][2]*0.0001, time_units = 's')

	return spikes, shank

def loadEpoch(path, epoch):
	import scipy.io
	import neuroseries as nts
	sampling_freq = 1250	
	behepochs = scipy.io.loadmat(path+'/Analysis/BehavEpochs.mat')

	if epoch == 'wake':
		wake_ep = np.hstack([behepochs['wakeEp'][0][0][1],behepochs['wakeEp'][0][0][2]])
		return nts.IntervalSet(wake_ep[:,0], wake_ep[:,1], time_units = 's').drop_short_intervals(0.0)

	elif epoch == 'sleep':
		sleep_pre_ep, sleep_post_ep = [], []
		if 'sleepPreEp' in behepochs.keys():
			sleep_pre_ep = behepochs['sleepPreEp'][0][0]
			sleep_pre_ep = np.hstack([sleep_pre_ep[1],sleep_pre_ep[2]])
			sleep_pre_ep_index = behepochs['sleepPreEpIx'][0]
		if 'sleepPostEp' in behepochs.keys():
			sleep_post_ep = behepochs['sleepPostEp'][0][0]
			sleep_post_ep = np.hstack([sleep_post_ep[1],sleep_post_ep[2]])
			sleep_post_ep_index = behepochs['sleepPostEpIx'][0]
		if len(sleep_pre_ep) and len(sleep_post_ep):
			sleep_ep = np.vstack((sleep_pre_ep, sleep_post_ep))
		elif len(sleep_pre_ep):
			sleep_ep = sleep_pre_ep
		elif len(sleep_post_ep):
			sleep_ep = sleep_post_ep						
		return nts.IntervalSet(sleep_ep[:,0], sleep_ep[:,1], time_units = 's')

	elif epoch == 'sws':
		import os
		file1 = path.split("/")[-1]+'.sts.SWS'
		file2 = path.split("/")[-1]+'-states.mat'
		listdir = os.listdir(path)
		if file1 in listdir:
			sws = np.genfromtxt(path+'/'+file1)/float(sampling_freq)
			return nts.IntervalSet.drop_short_intervals(nts.IntervalSet(sws[:,0], sws[:,1], time_units = 's'), 0.0)

		elif file2 in listdir:
			sws = scipy.io.loadmat(path+'/'+file2)['states'][0]
			index = np.logical_or(sws == 2, sws == 3)*1.0
			index = index[1:] - index[0:-1]
			start = np.where(index == 1)[0]+1
			stop = np.where(index == -1)[0]
			return nts.IntervalSet.drop_short_intervals(nts.IntervalSet(start, stop, time_units = 's', expect_fix=True), 0.0)

	elif epoch == 'rem':
		import os
		file1 = path.split("/")[-1]+'.sts.REM'
		file2 = path.split("/")[-1]+'-states.mat'
		listdir = os.listdir(path)	
		if file1 in listdir:
			rem = np.genfromtxt(path+'/'+file1)/float(sampling_freq)
			return nts.IntervalSet(rem[:,0], rem[:,1], time_units = 's').drop_short_intervals(0.0)

		elif file2 in listdir:
			rem = scipy.io.loadmat(path+'/'+file2)['states'][0]
			index = (rem == 5)*1.0
			index = index[1:] - index[0:-1]
			start = np.where(index == 1)[0]+1
			stop = np.where(index == -1)[0]
			return nts.IntervalSet(start, stop, time_units = 's', expect_fix=True).drop_short_intervals(0.0)

def loadRipples(path):	
	# 0 : debut
	# 1 : milieu
	# 2 : fin
	# 3 : amplitude nombre de sd au dessus de bruit
	# 4 : frequence instantan
	import neuroseries as nts
	ripples = np.genfromtxt(path+'/'+path.split("/")[-1]+'.sts.RIPPLES')
	return (nts.IntervalSet(ripples[:,0], ripples[:,2], time_units = 's'), 
			nts.Ts(ripples[:,1], time_units = 's'))

def loadTheta(path):
	import scipy.io
	import neuroseries as nts
	thetaInfo = scipy.io.loadmat(path)
	troughs = nts.Tsd(thetaInfo['thetaTrghs'][0][0][2].flatten(), thetaInfo['thetaTrghs'][0][0][3].flatten(), time_units = 's')
	peaks = nts.Tsd(thetaInfo['thetaPks'][0][0][2].flatten(), thetaInfo['thetaPks'][0][0][3].flatten(), time_units = 's')
	good_ep = nts.IntervalSet(thetaInfo['goodEp'][0][0][1], thetaInfo['goodEp'][0][0][2], time_units = 's')	
	tmp = (good_ep.as_units('s')['end'].iloc[-1] - good_ep.as_units('s')['start'].iloc[0])	
	if (tmp/60.)/60. > 20. : # VERY BAD
		good_ep = nts.IntervalSet(	good_ep.as_units('s')['start']*0.0001, 
									good_ep.as_units('s')['end']*0.0001,
									time_units = 's'
								)
	return good_ep	
	# troughs = troughs.restrict(good_ep)
	# peaks = peaks.restrict(good_ep)
	# return troughs, peaks

def loadSWRMod(path):
	import _pickle as cPickle
	tmp = cPickle.load(open(path, 'rb'))
	z = []
	for session in tmp.keys():
		z.append(tmp[session]['Hcorr'])
	z = np.vstack(z)
	return z

def loadThetaMod(path):
	import _pickle as cPickle	
	tmp = cPickle.load(open(path, 'rb'))
	z = {'wake':[],'rem':[]}
	for k in z.keys():
		for session in tmp.keys():
			z[k].append(tmp[session]['theta_mod'][k])
		z[k] = np.vstack(z[k])
	return z	

def loadXML(path):
	from xml.dom import minidom
	xmldoc 		= minidom.parse(path)
	nChannels 	= xmldoc.getElementsByTagName('acquisitionSystem')[0].getElementsByTagName('nChannels')[0].firstChild.data
	fs 			= xmldoc.getElementsByTagName('fieldPotentials')[0].getElementsByTagName('lfpSamplingRate')[0].firstChild.data	
	shank_to_channel = {}
	groups 		= xmldoc.getElementsByTagName('anatomicalDescription')[0].getElementsByTagName('channelGroups')[0].getElementsByTagName('group')
	for i in range(len(groups)):
		shank_to_channel[i] = np.sort([int(child.firstChild.data) for child in groups[i].getElementsByTagName('channel')])
	return int(nChannels), int(fs), shank_to_channel

def loadLFP(path, n_channels=90, channel=64, frequency=1250.0, precision='int16'):
	import neuroseries as nts
	if type(channel) is not list:
		f = open(path, 'rb')
		startoffile = f.seek(0, 0)
		endoffile = f.seek(0, 2)
		bytes_size = 2
		
		n_samples = int((endoffile-startoffile)/n_channels/bytes_size)
		duration = n_samples/frequency
		f.close()
		with open(path, 'rb') as f:
			data = np.fromfile(f, np.int16).reshape((n_samples, n_channels))[:,channel]
		timestep = np.arange(0, len(data))/frequency
		return nts.Tsd(timestep, data, time_units = 's')
	elif type(channel) is list:
		f = open(path, 'rb')
		startoffile = f.seek(0, 0)
		endoffile = f.seek(0, 2)
		bytes_size = 2
		
		n_samples = int((endoffile-startoffile)/n_channels/bytes_size)
		duration = n_samples/frequency
		f.close()
		with open(path, 'rb') as f:
			data = np.fromfile(f, np.int16).reshape((n_samples, n_channels))[:,channel]
		timestep = np.arange(0, len(data))/frequency
		return nts.TsdFrame(timestep, data, time_units = 's')

def loadSpeed(path):
	import neuroseries as nts
	import scipy.io
	raw = scipy.io.loadmat(path)
	return nts.Tsd(raw['speed'][:,0], raw['speed'][:,1], time_units = 's')

def writeNeuroscopeEvents(path, ep, name):
	f = open(path, 'w')
	for i in range(len(ep)):
		f.writelines(str(ep.as_units('ms').iloc[i]['start']) + " "+name+" start "+ str(1)+"\n")
		f.writelines(str(ep.as_units('ms').iloc[i]['end']) + " "+name+" end "+ str(1)+"\n")
	f.close()		
	return

def plotEpoch(wake_ep, sleep_ep, rem_ep, sws_ep, ripples_ep, spikes_sws):
	from pylab import figure, plot, legend, show
	figure()
	plot([wake_ep['start'][0], wake_ep['end'][0]], np.zeros(2), '-', color = 'blue', label = 'wake')
	[plot([wake_ep['start'][i], wake_ep['end'][i]], np.zeros(2), '-', color = 'blue') for i in range(len(wake_ep))]
	plot([sleep_ep['start'][0], sleep_ep['end'][0]], np.zeros(2), '-', color = 'green', label = 'sleep')
	[plot([sleep_ep['start'][i], sleep_ep['end'][i]], np.zeros(2), '-', color = 'green') for i in range(len(sleep_ep))]	
	plot([rem_ep['start'][0], rem_ep['end'][0]],  np.zeros(2)+0.1, '-', color = 'orange', label = 'rem')
	[plot([rem_ep['start'][i], rem_ep['end'][i]], np.zeros(2)+0.1, '-', color = 'orange') for i in range(len(rem_ep))]
	plot([sws_ep['start'][0], sws_ep['end'][0]],  np.zeros(2)+0.1, '-', color = 'red', label = 'sws')
	[plot([sws_ep['start'][i], sws_ep['end'][i]], np.zeros(2)+0.1, '-', color = 'red') for i in range(len(sws_ep))]	
	plot([ripples_ep['start'][0], ripples_ep['end'][0]],  np.zeros(2)+0.2, '-', color = 'black', label = 'ripples')
	[plot([ripples_ep['start'][i], ripples_ep['end'][i]], np.zeros(2)+0.2, '-', color = 'black') for i in range(len(ripples_ep))]	
	for n in spikes_sws.keys():
		plot(spikes_sws[n].index.values, np.zeros(spikes_sws[n].size)+0.4, 'o')


	legend()
	show()

def plotThetaEpoch(wake_ep, sleep_ep, rem_ep, sws_ep, rem_peaks, rem_troughs, wake_peaks, wake_troughs):
	from pylab import figure, plot, legend, show
	figure()
	plot([wake_ep['start'][0], wake_ep['end'][0]], np.zeros(2), '-', color = 'blue', label = 'wake')
	[plot([wake_ep['start'][i], wake_ep['end'][i]], np.zeros(2), '-', color = 'blue') for i in range(len(wake_ep))]
	plot([sleep_ep['start'][0], sleep_ep['end'][0]], np.zeros(2), '-', color = 'green', label = 'sleep')
	[plot([sleep_ep['start'][i], sleep_ep['end'][i]], np.zeros(2), '-', color = 'green') for i in range(len(sleep_ep))]	
	plot([rem_ep['start'][0], rem_ep['end'][0]],  np.zeros(2)+0.1, '-', color = 'orange', label = 'rem')
	[plot([rem_ep['start'][i], rem_ep['end'][i]], np.zeros(2)+0.1, '-', color = 'orange') for i in range(len(rem_ep))]
	plot([sws_ep['start'][0], sws_ep['end'][0]],  np.zeros(2)+0.1, '-', color = 'red', label = 'sws')
	[plot([sws_ep['start'][i], sws_ep['end'][i]], np.zeros(2)+0.1, '-', color = 'red') for i in range(len(sws_ep))]	

	plot(rem_peaks.index.values, np.zeros(rem_peaks.size)+0.4, 'o')
	plot(wake_peaks.index.values, np.zeros(wake_peaks.size)+0.4, 'o')
	plot(rem_troughs.index.values, np.zeros(rem_troughs.size)+0.3, '+')
	plot(wake_troughs.index.values, np.zeros(wake_troughs.size)+0.3, '+')

	legend()
	show()


