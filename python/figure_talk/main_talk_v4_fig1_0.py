#!/usr/bin/env python


import numpy as np
import pandas as pd
# from matplotlib.pyplot import plot,show,draw
import scipy.io
import sys
sys.path.append("../")
from functions import *
from pylab import *
from sklearn.decomposition import PCA
import _pickle as cPickle
import neuroseries as nts
import os
import hsluv

data_directory 	= '/mnt/DataGuillaume/MergedData/'
datasets 		= np.loadtxt(data_directory+'datasets_ThalHpc.list', delimiter = '\n', dtype = str, comments = '#')

session = 'Mouse32/Mouse32-140822'

lfp_hpc 		= pd.read_hdf(data_directory+session+'/'+session.split("/")[1]+'_EEG_SWR.h5')

data = cPickle.load(open('../../figures/figures_articles_v4/figure1/good_100ms_pickle/'+session.split("/")[1]+'.pickle', 'rb'))

iwak		= data['swr'][0]['iwak']
iswr		= data['swr'][0]['iswr']
rip_tsd		= data['swr'][0]['rip_tsd']
rip_spikes	= data['swr'][0]['rip_spikes']
times 		= data['swr'][0]['times']
wakangle	= data['swr'][0]['wakangle']
neurons		= data['swr'][0]['neurons']
tcurves		= data['swr'][0]['tcurves']
irand 		= data['rnd'][0]['irand']
iwak2 		= data['rnd'][0]['iwak2']

# sys.exit()

tcurves = tcurves.rolling(window=100,win_type='gaussian',center=True,min_periods=1).mean(std=1.0)

# rip_tsd = pd.Serrip_tsd.index.values)

colors = np.hstack((np.linspace(0, 1, int(len(times)/2)), np.ones(1), np.linspace(0, 1, int(len(times)/2))[::-1]))

colors = np.arange(len(times))

H = wakangle.values/(2*np.pi)

HSV = np.vstack((H*360, np.ones_like(H)*85, np.ones_like(H)*45)).T

# from matplotlib.colors import hsv_to_rgb

# RGB = hsv_to_rgb(HSV)
RGB = np.array([hsluv.hsluv_to_rgb(HSV[i]) for i in range(len(HSV))])

# 4644.8144
# 4924.4720
# 5244.9392
# 7222.9480
# 7780.2968
# 11110.1888
# 11292.3240
# 11874.5688

good_ex = (np.array([4644.8144,4924.4720,5244.9392,7222.9480,7780.2968,11110.1888,11292.3240,11874.5688])*1e6).astype('int')

exemple = [np.where(i == rip_tsd.index.values)[0][0] for i in [good_ex[0],good_ex[1],good_ex[2]]]

# normwak = np.sqrt(np.sum(np.power(iwak,2), 1))
# normswr = np.sqrt(np.sum(np.power(iswr, 2), -1))
# normrnd = np.sqrt(np.sum(np.power(irand,2), -1))

# angwak 		= np.arctan2(iwak[:,1], iwak[:,0])
# angwak 		= (angwak + 2*np.pi)%(2*np.pi)
# tmp 			= pd.Series(index = wakangle.index.values, data = np.unwrap(angwak))
# tmp2 			= tmp.rolling(window=100,win_type='gaussian',center=True,min_periods=1).mean(std=30.0)
# tmp2 			= nts.Tsd(tmp2)
# tmp3 			= np.abs(np.diff(tmp2.values))/np.diff(tmp2.as_units('s').index.values)
# wakvel			= nts.Tsd(t = tmp2.index.values[1:], d = tmp3)



# angswr = np.arctan2(iswr[:,:,1], iswr[:,:,0])
# angswr = (angswr + 2*np.pi)%(2*np.pi)

# angrnd = np.arctan2(irand[:,:,1], irand[:,:,0])
# angrnd = (angrnd + 2*np.pi)%(2*np.pi)


# swrvel 			= []
# for i in range(len(angswr)):
# 	a = np.unwrap(angswr[i])
# 	b = pd.Series(index = times, data = a)
# 	c = b.rolling(window = 10, win_type='gaussian', center=True, min_periods=1).mean(std=1.0)
# 	swrvel.append(np.abs(np.diff(c.values))/0.1)
# swrvel = np.array(swrvel)


# rndvel 			= []
# for i in range(len(angrnd)):
# 	a = np.unwrap(angrnd[i])
# 	b = pd.Series(index = times, data = a)
# 	c = b.rolling(window = 10, win_type='gaussian', center=True, min_periods=1).mean(std=1.0)
# 	rndvel.append(np.abs(np.diff(c.values))/0.1)
# rndvel = np.array(rndvel)


# meannorm = (normswr[:,0:-1] + normswr[:,1:])/2 
# swrvel /= meannorm

###############################################################################################################
# PLOT
###############################################################################################################
def figsize(scale):
	fig_width_pt = 483.69687                         # Get this from LaTeX using \the\textwidth
	inches_per_pt = 1.0/72.27                       # Convert pt to inch
	golden_mean = (np.sqrt(5.0)-1.0)/2.0            # Aesthetic ratio (you could change this)
	fig_width = fig_width_pt*inches_per_pt*scale    # width in inches
	fig_height = fig_width*golden_mean*1.3          # height in inches
	fig_size = [fig_width,fig_height]
	return fig_size

def simpleaxis(ax):
	ax.spines['top'].set_visible(False)
	ax.spines['right'].set_visible(False)
	ax.get_xaxis().tick_bottom()
	ax.get_yaxis().tick_left()
	# ax.xaxis.set_tick_params(size=6)
	# ax.yaxis.set_tick_params(size=6)

def noaxis(ax):
	ax.spines['top'].set_visible(False)
	ax.spines['right'].set_visible(False)
	ax.spines['left'].set_visible(False)
	ax.spines['bottom'].set_visible(False)
	ax.get_xaxis().tick_bottom()
	ax.get_yaxis().tick_left()
	ax.set_xticks([])
	ax.set_yticks([])
	# ax.xaxis.set_tick_params(size=6)
	# ax.yaxis.set_tick_params(size=6)



import matplotlib as mpl
from mpl_toolkits.axes_grid1 import make_axes_locatable

# mpl.use("pdf")
pdf_with_latex = {                      # setup matplotlib to use latex for output
	"pgf.texsystem": "pdflatex",        # change this if using xetex or lautex
	# "text.usetex": True,                # use LaTeX to write all text
	# "font.family": "serif",
	"font.serif": [],                   # blank entries should cause plots to inherit fonts from the document
	"font.sans-serif": [],
	"font.monospace": [],
	"axes.labelsize": 8,               # LaTeX default is 10pt font.
	"font.size": 7,
	"legend.fontsize": 7,               # Make the legend/label fonts a little smaller
	"xtick.labelsize": 7,
	"ytick.labelsize": 7,
	"pgf.preamble": [
		r"\usepackage[utf8x]{inputenc}",    # use utf8 fonts becasue your computer can handle it :)
		r"\usepackage[T1]{fontenc}",        # plots will be generated using this preamble
		],
	"lines.markeredgewidth" : 0.2,
	"axes.linewidth"        : 0.8,
	"ytick.major.size"      : 1.5,
	"xtick.major.size"      : 1.5
	}  
mpl.rcParams.update(pdf_with_latex)
import matplotlib.gridspec as gridspec
from matplotlib.pyplot import *
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

markers = ['d', 'o', 'v']

fig = figure(figsize = figsize(1.0))

outergs = GridSpec(2,1, figure = fig, height_ratios = [0.25, 0.7], hspace = 0.15)

gs_top = gridspec.GridSpecFromSubplotSpec(2,4, subplot_spec = outergs[0,0], width_ratios = [0.1, 0.5, 0.5, 0.5], height_ratios = [0.2, 0.8], hspace = 0)

####################################################################
# A TUNING CURVES
####################################################################
gsA = gridspec.GridSpecFromSubplotSpec(len(neurons), 1, subplot_spec = gs_top[1,0], hspace = 0.0)

for i, n in enumerate(neurons[::-1]):
	subplot(gsA[i,0])
	plot(tcurves[n], color = hsluv.hsluv_to_rgb([tcurves[n].idxmax()*180/np.pi,85,45]), linewidth = 1)
	if i == len(neurons)-1:
		simpleaxis(gca())
		xticks([0, 2*np.pi], ["0", r"$2\pi$"], fontsize = 6)
		yticks([],[])
		gca().spines['left'].set_visible(False)	
	else:
		gca().axis('off')		
		xticks([])
		yticks([])
	
		

# ####################################################################
# # B WAKE
# ####################################################################
# subplot(gs_top[1,1:])
# simpleaxis(gca())
# session = 'Mouse32/Mouse32-140822'
# generalinfo 	= scipy.io.loadmat(data_directory+session+'/Analysis/GeneralInfo.mat')
# shankStructure 	= loadShankStructure(generalinfo)
# if len(generalinfo['channelStructure'][0][0][1][0]) == 2:
# 	hpc_channel 	= generalinfo['channelStructure'][0][0][1][0][1][0][0] - 1
# else:
# 	hpc_channel 	= generalinfo['channelStructure'][0][0][1][0][0][0][0] - 1		
# spikes,shank	= loadSpikeData(data_directory+session+'/Analysis/SpikeData.mat', shankStructure['thalamus'])		
# n_channel,fs, shank_to_channel = loadXML(data_directory+session+"/"+session.split("/")[1]+'.xml')	
# wake_ep 		= loadEpoch(data_directory+session, 'wake')
# sleep_ep 		= loadEpoch(data_directory+session, 'sleep')
# sws_ep 			= loadEpoch(data_directory+session, 'sws')
# rem_ep 			= loadEpoch(data_directory+session, 'rem')
# sleep_ep 		= sleep_ep.merge_close_intervals(threshold=1.e3)		
# sws_ep 			= sleep_ep.intersect(sws_ep)	
# rem_ep 			= sleep_ep.intersect(rem_ep)
# rip_ep,rip_tsd 	= loadRipples(data_directory+session)
# rip_ep			= sws_ep.intersect(rip_ep)	
# rip_tsd 		= rip_tsd.restrict(sws_ep)
# speed 			= loadSpeed(data_directory+session+'/Analysis/linspeed.mat').restrict(wake_ep)
# hd_info 		= scipy.io.loadmat(data_directory+session+'/Analysis/HDCells.mat')['hdCellStats'][:,-1]
# hd_info_neuron	= np.array([hd_info[n] for n in spikes.keys()])
# position 		= pd.read_csv(data_directory+session+"/"+session.split("/")[1] + ".csv", delimiter = ',', header = None, index_col = [0])
# angle 			= nts.Tsd(t = position.index.values, d = position[1].values, time_units = 's')

# # tmp 			= (angle.values * len(neurons))/(2*np.pi)
# # angle 			= nts.Tsd(t = angle.index.values, d = tmp)

# spikes 		= {k:spikes[k] for k in np.where(hd_info_neuron==1)[0] if k not in []}
# # neurons 		= np.sort(list(spikes.keys()))
# # neurons = tcurves.keys()

# ep = nts.IntervalSet(start = 1.06128e+10, end = 1.06469e+10)
# for k, n in enumerate(neurons):
# 	spk = spikes[n].restrict(ep).index.values
# 	if len(spk):
# 		clr = hsluv.hsluv_to_rgb([tcurves[n].idxmax()*180/np.pi,85,45])
# 		plot(spk, np.ones_like(spk)*tcurves[n].idxmax(), '|', color = clr, linewidth = 5, markeredgewidth = 1)
# plot(angle.restrict(ep), linewidth = 2, color = 'black')
# # xlim(times[0], times[-1])
# # ylim(-1, len(neurons)+1)
# ylim(0, 2*np.pi)
# xlim(ep.loc[0,'start'], ep.loc[0,'end'])
# # xticks([-500,0,500], fontsize = 6)
# # xlabel("Time from SWR (ms)")
# yticks([0, 2*np.pi], ["0", r"$2\pi$"], fontsize = 6)
# xticks(list(ep.loc[0].values), ['0', str(ep.tot_length('s'))+' s'])
# # if i == 0:
# ylabel("HD neurons", labelpad = -5)
# title("Wake")

# vline = np.arange(ep.loc[0,'start'], ep.loc[0, 'end'], 1000000)
# for t in vline:
# 	axvline(t, color = 'grey', alpha = 0.6, linewidth = 1)





# for i, j in zip(range(3),exemple):
# 	axlfp = subplot(gs_top[0,i+1])
# 	noaxis(axlfp)
# 	lfp = lfp_hpc.loc[rip_tsd.index[j]-5e5:rip_tsd.index[j]+5e5]
# 	lfp = nts.Tsd(t = lfp.index.values - rip_tsd.index[j], d = lfp.values)
# 	plot(lfp.as_units('ms'), color = 'black', linewidth = 0.8)
# 	plot([0], [lfp.max()+200], '*', color = 'red', markersize = 5, clip_on=False)
# 	# if i == 0:
# 	# 	ylabel('CA1')#, labelpad = 25)
# 	xlim(times[0], times[-1])
# 	ylim(lfp.min(),lfp.max()+100)

# 	if i == 0:
# 		# gca().text(-0.4, 0.60, "a", transform = gca().transAxes, fontsize = 10, fontweight='bold')
# 		# gca().text(-0.11, 0.60, "b", transform = gca().transAxes, fontsize = 10, fontweight='bold')
# 		gca().text(0.01, 0.6, "CA1", transform = gca().transAxes, fontsize = 8)
		

# 	axspk = subplot(gs_top[1,i+1])	
# 	simpleaxis(axspk)
# 	for k, n in enumerate(neurons):
# 		spk = rip_spikes[j][n]
# 		if len(spk):
# 			clr = hsluv.hsluv_to_rgb([tcurves[n].idxmax()*180/np.pi,85,45])
# 			plot(spk, np.ones_like(spk)*k, '|', color = clr, linewidth = 5, markeredgewidth = 1)

# 	xlim(times[0], times[-1])
# 	ylim(-1, len(neurons)+1)
# 	xticks([-500,0,500], fontsize = 6)
# 	xlabel("Time from SWR (ms)")
# 	yticks([])
# 	if i == 0:
# 		ylabel("HD neurons")
		
# 	else:
# 		gca().spines['left'].set_visible(False)		




gs_bot = gridspec.GridSpecFromSubplotSpec(1,2, subplot_spec = outergs[1,0], width_ratios = [0.8, 0.5], wspace = 0.1)
####################################################################
# C RING
####################################################################
axC = subplot(gs_bot[0,0])
gca().axis('off')		
# gca().text(-0.0, 0.98, "c", transform = gca().transAxes, fontsize = 10, fontweight='bold')
axC.set_aspect(aspect=1)
# for i in range(len(iswr)):
# 	scatter(iswr[i,:,0], iswr[i,:,1], c = 'lightgrey', marker = '.', alpha = 0.7, zorder = 2, linewidth = 0, s= 40)

# SEQUENCE EXEMPLE

# wake_ep = wake_ep.intersect(nts.IntervalSet(start=wake_ep.loc[0,'start'], end = wake_ep.loc[0,'start']+20*60*1e6))
# bin_size = 200
# bins = np.arange(wake_ep.as_units('ms').start.iloc[0], wake_ep.as_units('ms').end.iloc[-1]+bin_size, bin_size)

# iwak2 = nts.TsdFrame(t = bins[0:-1]+np.diff(bins), d = iwak, time_units = 'ms')
# iwak2 = iwak2.restrict(ep)

# scatter(i)

# scatter(iwak[~np.isnan(H),0], iwak[~np.isnan(H),1], c = RGB[~np.isnan(H)], marker = '.', alpha = 0.5, zorder = 2, linewidth = 0, s= 40)


# def intersect(xy):
# 	x = xy[0]
# 	y = xy[1]
# 	idx = np.unique(np.hstack((np.where(np.abs(np.diff(x)) > 0.01)[0], np.where(np.abs(np.diff(y)) > 0.01)[0])))
# 	newx = []
# 	newy = []
# 	for i in idx:
# 		a = np.linspace(x.iloc[i], x.iloc[i+1], 10)
# 		b = np.linspace(y.iloc[i], y.iloc[i+1], 10)
# 		t = np.linspace(x.index.values[i], x.index.values[i+1], 10)
# 		newx.append(pd.Series(index=t,data=a))
# 		newy.append(pd.Series(index=t,data=b))
# 	newx.append(x)	
# 	newx = pd.concat(newx)
# 	newx = newx.drop_duplicates()
# 	newx = newx.sort_index()
# 	newy.append(y)	
# 	newy = pd.concat(newy)
# 	newy = newy.drop_duplicates()
# 	newy = newy.sort_index()
# 	return pd.concat([newx, newy], 1)

# cmap = matplotlib.cm.get_cmap('gray')



# for i, j in zip(range(3), exemple):
# 	# arrows
# 	x = iswr[j,:,0]
# 	y = iswr[j,:,1]
# 	dx = np.diff(x)
# 	dy = np.diff(y)
# 	cmap = plt.cm.get_cmap('gray')
# 	cl = np.abs(times)/np.max(times)
# 	for k in range(0,len(x)-1,4):
# 		arrow(x[k], y[k], dx[k]*0.01, dy[k]*0.01, head_width=0.02, head_length=0.02, linewidth = 0, fc=cmap(cl[k]), ec=cmap(cl[k]), zorder = 5, alpha = 1)

# 	# colors
# 	xy = pd.DataFrame(index = times, data = np.vstack((x, y)).T)
# 	newxy = intersect(xy)
# 	newxy = newxy.rolling(window=100,win_type='gaussian',center=True,min_periods=1).mean(std=1)
# 	newtime = newxy.index.values
# 	# cl = np.linspace(0, 0.7, len(newxy.index.values))	
# 	cl = np.abs(newtime)/np.max(newtime)
# 	for k in range(len(newxy)-1):
# 		tmp = newxy.iloc[k:k+2]
# 		plot(tmp[0].values, tmp[1].values, color = cmap(cl[k]), alpha = 1, linewidth = 2)

# 	idx = np.where(times == 0)[0][0]
# 	plot(iswr[j,idx,0], iswr[j,idx,1], '*', color = 'red', zorder = 6, markersize = 9)
# 	# idx = np.where(times == times[0])[0][0]
# 	# plot(iswr[j,idx,0], iswr[j,idx,1], 's', color = 'green', zorder = 6, markersize = 5)
# 	# idx = np.where(times == times[-1])[0][0]
# 	# plot(iswr[j,idx,0], iswr[j,idx,1], 'o', color = 'blue', zorder = 6, markersize = 5)


# ax = gca()
# # colorbar
# from matplotlib.colorbar import ColorbarBase
# colors = [hsluv.hsluv_to_hex([i,85,45]) for i in np.arange(0, 361)]
# cmap= matplotlib.colors.ListedColormap(colors)
# # cmap.set_under("hsluv")
# # cmap.set_over("w")''''
# cax = inset_axes(ax, "20%", "3%",
#                    bbox_to_anchor=(0.68, 0.08, 1, 1),
#                    bbox_transform=ax.transAxes, 
#                    loc = 'lower left')
# cb1 = mpl.colorbar.ColorbarBase(cax, cmap=cmap,
#                                 norm=matplotlib.colors.Normalize(vmin=0,vmax=360),
#                                 orientation='horizontal')
# cb1.set_ticks([0,360])
# cb1.set_ticklabels(['0', r"$2\pi$"])
# cax.set_title("Wake", pad = 3)

# cmap = matplotlib.cm.get_cmap('gray')
# colors = [cmap(i) for i in cl]
# cmap= matplotlib.colors.ListedColormap(colors)
# # cmap.set_under("hsluv")
# # cmap.set_over("w")''''
# cax = inset_axes(ax, "20%", "2%",
#                    bbox_to_anchor=(0.68, -0.05, 1, 1),
#                    bbox_transform=ax.transAxes, 
#                    loc = 'lower left')
# noaxis(cax)
# cb1 = mpl.colorbar.ColorbarBase(cax, cmap=cmap,
#                                 norm=matplotlib.colors.Normalize(vmin=0,vmax=1),
#                                 orientation='horizontal')
# cb1.set_ticks([0,0.5,1])
# cb1.set_ticklabels([-500, 0, 500])
# cb1.outline.set_edgecolor(None)
# cax.set_title("SWR trajectory (ms)", pad = 3)

# # ####################################################################
# # D Various
# ####################################################################
# # gs_bot_right = gridspec.GridSpecFromSubplotSpec(5,1, subplot_spec = gs_bot[0,1], hspace = 0.75, height_ratios = [0.0001, 0.5, 0.5, -0.1, 0.6])
# gs_bot_right = gridspec.GridSpecFromSubplotSpec(3,2, subplot_spec = gs_bot[0,1], height_ratios = [0.0, 0.7, 0.5], hspace = 0.5, wspace = 0.5)#, hspace = 0.75, height_ratios = [0.0001, 0.5, 0.5, -0.1, 0.6])

# data2 = cPickle.load(open('../../figures/figures_articles_v4/figure1/RING_DECODING_30ms.pickle', 'rb'))

# # norm r
# # ax = subplot(gs_bot_right[1,0])
# ax = subplot(gs_bot_right[1,0])
# simpleaxis(ax)
# axhline(0, color = 'grey', linewidth = 0.75, alpha = 0.75)
# radius = data2['radius']
# plot(radius, color = 'grey', alpha = 0.5, linewidth = 0.4)
# plot(radius.mean(1), color = 'black', linewidth = 2)
# xticks([-500,0,500], fontsize = 6)
# yticks(np.arange(-0.1, 0.4, 0.1), fontsize = 6)
# title("Radius")
# ylabel("Modulation")

# # gca().text(-0.45, 1.05, "d", transform = gca().transAxes, fontsize = 10, fontweight='bold')



# # angular velocity
# # ax = subplot(gs_bot_right[2,0])
# ax = subplot(gs_bot_right[1,1])
# simpleaxis(ax)
# axhline(0, color = 'grey', linewidth = 0.75, alpha = 0.75)
# velocity = data2['velocity']
# plot(velocity, color = 'grey', alpha = 0.5, linewidth = 0.4)
# plot(velocity.mean(1), '-', color = 'black', linewidth = 2)

# title("Angular velocity")
# xticks([-500,0,500], fontsize = 6)
# yticks(np.arange(-0.2, 0.3, 0.1), fontsize = 6)
# xlabel("Time from SWRs (ms)", horizontalalignment='right', y = 1)

# gca().text(-0.3, 1.05, "e", transform = gca().transAxes, fontsize = 10, fontweight='bold')

# # UP/DOWN
# ax = subplot(gs_bot_right[2,:])
# simpleaxis(ax)

# data3 = cPickle.load(open('../../figures/figures_articles_v4/figure1/UP_DOWN_RATES.pickle', 'rb'))
# allmua_hd = data3['mua_hd']
# allmua_nohd = data3['mua_nohd']
# allswr_rates = data3['swr_rates']
# colors = ['black', 'grey', 'red']
# styles = ['-', '--', '-']
# labels = ['HD', 'non-HD', 'SWRs']
# for i, d in enumerate([allmua_hd, allmua_nohd, allswr_rates]):
# 	m = d.mean(1)
# 	s = d.sem(1)
# 	x = d.index.values
# 	plot(x, m, styles[i], label = labels[i], color= colors[i], linewidth = 0.8)
# 	fill_between(x, m-s, m+s, alpha = 0.3, color = colors[i], linewidth=0)

# yticks([0, 0.01], [0, 1], fontsize = 6.5)
# xticks([-0.5, 0, 0.5, 1], ['DOWN', '', 'UP', ''], fontsize = 6.5)
# ylabel("Density (%)")
# legend(frameon=False,loc = 'lower left', bbox_to_anchor=(0.55,-0.06) )#,handlelength=1,ncol = 1)

# # xlabel("Time from SWRs (ms)")
# gca().text(-0.12, 1.02, "f", transform = gca().transAxes, fontsize = 10, fontweight='bold')

# # INSET 
# axins = inset_axes(gca(), width="25%", height=0.4, loc=2)
# data4 = pd.read_hdf('../../figures/figures_articles_v4/figure1/UP_DOWN_CC.h5')

# data4 = data4.rolling(window = 40, win_type = 'gaussian', center = True, min_periods = 1).mean(std = 4.0)

# m = data4.mean(1)
# s = data4.sem(1)
# x = data4.index.values
# plot(x, m, color = 'black', linewidth = 1)
# fill_between(x, m-s, m+s, alpha = 0.2)
# xticks([-2000,0,2000], [-2, 0, 2])
# gca().xaxis.set_tick_params(labelsize=6)
# yticks([0.41, 0.49])
# gca().yaxis.tick_right()
# gca().yaxis.set_tick_params(labelsize=6)
# title("UP/SWRs", fontsize = 7, pad = 2)
# ylim(0.41,0.49)
# xlabel("Time lag (s)", fontsize = 6, labelpad = 0)



outergs.update(top= 0.98, bottom = 0.04, right = 0.97, left = 0.02)

# savefig("../../figures/figures_articles_v4/figart_1.pdf", dpi = 900, facecolor = 'white')
savefig(r"/home/guillaume/Dropbox (Peyrache Lab)/Talks/figtalk_ring1.pdf", dpi = 200, facecolor = 'white')
savefig(r"/home/guillaume/Dropbox (Peyrache Lab)/Talks/figtalk_ring2.png", dpi = 200, facecolor = 'white')
# os.system('"evince /home/guillaume/Dropbox (Peyrache Lab)/Talks/figtalk_ring1.pdf &"')
