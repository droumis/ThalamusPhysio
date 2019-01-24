import ternary
import numpy as np
import pandas as pd
from functions import *
import sys
from functools import reduce
from sklearn.manifold import *
from sklearn.cluster import *
from pylab import *
import _pickle as cPickle
from skimage.filters import gaussian

############################################################################################################
# LOADING DATA
############################################################################################################
data_directory 	= '/mnt/DataGuillaume/MergedData/'
datasets 		= np.loadtxt(data_directory+'datasets_ThalHpc.list', delimiter = '\n', dtype = str, comments = '#')
burstiness 				= pd.HDFStore("/mnt/DataGuillaume/MergedData/BURSTINESS.h5")['w']
lambdaa  = pd.read_hdf("/mnt/DataGuillaume/MergedData/LAMBDA_AUTOCORR.h5")[('rem', 'b')]
lambdaa = lambdaa[np.logical_and(lambdaa>0.0,lambdaa<30.0)]



theta_mod, theta_ses 	= loadThetaMod('/mnt/DataGuillaume/MergedData/THETA_THAL_mod.pickle', datasets, return_index=True)
theta 					= pd.DataFrame(	index = theta_ses['rem'], 
										columns = pd.MultiIndex.from_product([['wak', 'rem'], ['phase', 'pvalue', 'kappa']]),
										data = np.hstack((theta_mod['wake'], theta_mod['rem'])))
theta 					= theta.dropna()
rippower 				= pd.read_hdf("../figures/figures_articles/figure2/power_ripples_2.h5")
mappings = pd.read_hdf("/mnt/DataGuillaume/MergedData/MAPPING_NUCLEUS.h5")
swr_phase = pd.read_hdf("/mnt/DataGuillaume/MergedData/SWR_PHASE.h5")

# SWR MODULATION
swr_mod, swr_ses 		= loadSWRMod('/mnt/DataGuillaume/MergedData/SWR_THAL_corr.pickle', datasets, return_index=True)
nbins 					= 400
binsize					= 5
times 					= np.arange(0, binsize*(nbins+1), binsize) - (nbins*binsize)/2
swr 					= pd.DataFrame(	columns = swr_ses, 
										index = times,
										data = gaussFilt(swr_mod, (5,)).transpose())
swr = swr.loc[-500:500]

# AUTOCORR FAST
store_autocorr = pd.HDFStore("/mnt/DataGuillaume/MergedData/AUTOCORR_ALL.h5")
autocorr_wak = store_autocorr['wake'].loc[0.5:]
autocorr_rem = 	store_autocorr['rem'].loc[0.5:]
autocorr_sws = 	store_autocorr['sws'].loc[0.5:]
autocorr_wak = autocorr_wak.rolling(window = 20, win_type = 'gaussian', center = True, min_periods = 1).mean(std = 3.0)
autocorr_rem = autocorr_rem.rolling(window = 20, win_type = 'gaussian', center = True, min_periods = 1).mean(std = 3.0)
autocorr_sws = autocorr_sws.rolling(window = 20, win_type = 'gaussian', center = True, min_periods = 1).mean(std = 3.0)
autocorr_wak = autocorr_wak[2:20]
autocorr_rem = autocorr_rem[2:20]
autocorr_sws = autocorr_sws[2:20]
store_autocorr.close()


############################################################################################################
# WHICH NEURONS
############################################################################################################
firing_rate = pd.read_hdf("/mnt/DataGuillaume/MergedData/FIRING_RATE_ALL.h5")
fr_index = firing_rate.index.values[((firing_rate >= 1.0).sum(1) == 3).values]



neurons = np.intersect1d(swr.dropna(1).columns.values, autocorr_sws.dropna(1).columns.values)
neurons = np.intersect1d(neurons, fr_index)

from sklearn.decomposition import PCA


n_shuffling = 1000

shufflings = pd.DataFrame(index = np.arange(n_shuffling), columns = ['sws', 'rem', 'wak', 'wak-rem'])
det_all = pd.Series(index = ['sws', 'rem', 'wak', 'wak-rem'])

combi = {	'sws':autocorr_sws[neurons].values,
			'rem':autocorr_rem[neurons].values,
			'wak':autocorr_wak[neurons].values,
			'wak-rem':np.vstack((autocorr_wak[neurons].values,autocorr_rem[neurons].values))
		}


for k in combi:

	shuffling = []

	for j in range(n_shuffling):
		print(k, j)
		X = np.copy(swr[neurons].values.T)
		Y = np.copy(combi[k]).T
		Y = Y - Y.mean(1)[:,np.newaxis]
		Y = Y / Y.std(1)[:,np.newaxis]	
		np.random.shuffle(X)
		np.random.shuffle(Y)
		pc_swr = PCA(n_components=10).fit_transform(X)
		pc_aut = PCA(n_components=10).fit_transform(Y)
		All = np.hstack((pc_swr, pc_aut))
		corr = np.corrcoef(All.T)
		d = np.linalg.det(corr)
		shuffling.append(d)

	X = np.copy(swr[neurons].values.T)
	Y = np.copy(combi[k]).T
	Y = Y - Y.mean(1)[:,np.newaxis]
	Y = Y / Y.std(1)[:,np.newaxis]	
	pc_swr = PCA(n_components=10).fit_transform(X)
	pc_aut = PCA(n_components=10).fit_transform(Y)
	All = np.hstack((pc_swr, pc_aut))
	corr = np.corrcoef(All.T)
	d_swr_auto = np.linalg.det(corr)
	det_all.loc[k] = d_swr_auto


	shufflings.loc[:,k] = pd.Series(np.array(shuffling))


sys.exit()

store = pd.HDFStore("../figures/figures_articles_v2/figure6/determinant_corr_noSWS.h5", 'w')
store.put('det_all', det_all)
store.put('shufflings', shufflings)
store.close()












# Ecorr = np.mean(np.power(corr[0:10,10:], 2.0))
	

# 	a = pc_swr.T.dot(pc_aut)
# 	v = np.atleast_2d(np.std(pc_swr,0)).T.dot(np.atleast_2d(np.std(pc_aut,0)))
# 	c = (a/v)
# 	shuffling.append(np.abs(np.linalg.det(c)))


# shuffling = np.array(shuffling)

# X = np.copy(swr[neurons].values.T)
# Y = np.copy(autocorr_sws[neurons].values.T)
# pc_swr = PCA(n_components=10).fit_transform(X)
# pc_aut = PCA(n_components=10).fit_transform(Y)
# #var
# a = pc_swr.T.dot(pc_aut)
# v = np.atleast_2d(np.std(pc_swr,0)).T.dot(np.atleast_2d(np.std(pc_aut,0)))
# c = (a/v)

# real = np.abs(np.linalg.det(c))




# # per nucleus
# det = pd.DataFrame(index = nucleus, columns = ['det'])
# groups = mappings.loc[neurons].groupby('nucleus').groups
# for n in nucleus:
# 	X = np.copy(swr[groups[n]].values.T)
# 	Y = np.copy(autocorr_sws[groups[n]].values.T)
# 	pc_swr = PCA(n_components=10).fit_transform(X)
# 	pc_aut = PCA(n_components=10).fit_transform(Y)
# 	det.loc[n] = np.linalg.det(pc_swr.T.dot(pc_aut))
	






# pc_swr = PCA(n_components=10).fit_transform(X)
# pc_aut = PCA(n_components=10).fit_transform(Y)

# # 1. Det All
# All = np.hstack((pc_swr, pc_aut))
# corr = np.corrcoef(All.T)

# real = np.linalg.det(corr)

# Ecorr = np.mean(np.power(corr[0:10,10:], 2.0))



# shuffling = []

# for i in range(200):
# 	X = np.copy(swr[neurons].values.T)
# 	Y = np.copy(autocorr_sws[neurons].values.T)
# 	np.random.shuffle(X)
# 	# np.random.shuffle(Y)
# 	pc_swr = PCA(n_components=10).fit_transform(X)
# 	pc_aut = PCA(n_components=10).fit_transform(Y)
# 	All = np.hstack((pc_swr, pc_aut))
# 	corr = np.corrcoef(All.T)
# 	detall = np.linalg.det(corr)
# 	shuffling.append(detall)	

# axvline(real)
# hist(shuffling, 10)
# # for n in det.index: axvline(det.loc[n].values[0], label = n)
# # legend()
# show()



	


# 	shuffling.append(np.abs(np.linalg.det(c)))


# shuffling = np.array(shuffling)

# X = np.copy(swr[neurons].values.T)
# Y = np.copy(autocorr_sws[neurons].values.T)
# pc_swr = PCA(n_components=10).fit_transform(X)
# pc_aut = PCA(n_components=10).fit_transform(Y)
# #var
# a = pc_swr.T.dot(pc_aut)
# v = np.atleast_2d(np.std(pc_swr,0)).T.dot(np.atleast_2d(np.std(pc_aut,0)))
# c = (a/v)

# real = np.abs(np.linalg.det(c))




# a = pc_swr.T.dot(pc_aut)
# v = np.atleast_2d(np.std(pc_swr,0)).T.dot(np.atleast_2d(np.std(pc_aut,0)))
# M = (a/v)











# ############################################################################################################
# # MUTUAL INFORMATION
# ############################################################################################################
# from sklearn.metrics import *

# X = burstiness.loc[tokeep,'sws'].values
# Y = theta.loc[tokeep,('rem','kappa')].values
# Xc = np.digitize(X, np.linspace(X.min(), X.max()+0.001, 20))
# Yc = np.digitize(Y, np.linspace(Y.min(), Y.max()+0.001, 20))

# mutual_info_score(Xc, Yc)

# mis = pd.DataFrame(index = nucleus, columns = ['b/k'])

# for k, n in mappings.loc[tokeep].groupby('nucleus').groups.items():
# 	X = burstiness.loc[n,'sws'].values
# 	Y = theta.loc[n,('rem','kappa')].values
# 	Xc = np.digitize(X, np.linspace(X.min(), X.max()+0.001, 20))
# 	Yc = np.digitize(Y, np.linspace(Y.min(), Y.max()+0.001, 20))

# 	mis.loc[k] = adjusted_mutual_info_score(Xc, Yc)


# mis = mis.sort_values('b/k')

# plot(mis)

# show()