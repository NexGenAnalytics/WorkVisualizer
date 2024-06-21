# Potentially useful video: https://www.youtube.com/watch?v=qN3n0TM4Jno

import stumpy

# import torch
# import torch.nn as nn
# import torch.optim as optim
# from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from math import isclose
import numpy.random as rnd
import matplotlib.pyplot as plt
from scipy.stats import mode
from scipy.signal import find_peaks
from scipy.fft import fft, fftshift, fftfreq, rfft, rfftfreq

from t1_generate_time_series import create_time_series
import scipy.linalg as lin

# import pandas as pd
import matplotlib.dates as dates
from matplotlib.patches import Rectangle
import datetime as dt

################################################################################

num_loops = 17      # This is setting the problem
num_samples = 100000 # This is affecting the analysis
add_anomaly = True
timesteps, data, typical_loop_time = create_time_series(num_samples=num_samples, num_loops=num_loops, anomaly=add_anomaly)

## performing FFT to get guess of timestep ##

duration = timesteps[-1] - timesteps[0]
sr = num_samples / duration

yf = rfft(data)
xf = rfftfreq(num_samples, 1/sr)

plt.plot(xf, np.abs(yf))
plt.title("FFT Plot")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Power")
plt.show()

# X = fftshift(fft(data)) * sr / data.size
# N = len(X)
# n = np.arange(N)
# T = N/sr
# freq = np.linspace(-sr/2, sr/2, N, endpoint=False)

# # Determine peak frequency (find highest freqs and see if they are peaks)
# sorted_indices = np.argsort(np.abs(X))
# peaks, _ = find_peaks(np.abs(X))

# max_freq_index = sorted_indices[-2]  # set as default (ignoring peak at 0 Hz)
# for i in range(sorted_indices.size - 1):
#     index = -2 - i
#     if sorted_indices[index] in peaks:
#         max_freq_index = sorted_indices[index]

#         # Now see if there is a similar peak at half of this frequency
#         next_indices = [index - j for j in range(1, 4)]
#         for next_index in next_indices:
#             if sorted_indices[next_index] in peaks and isclose(np.abs(freq[sorted_indices[next_index]]), np.abs(freq[max_freq_index] / 2), rel_tol=1e-2):
#                 max_freq_index = sorted_indices[next_index]
#                 break # Use the half frequency as the max

#         break  # Use the original max_freq_index

#     if i > 5:
#         break  # Something has gone wrong

# peak_freq = np.abs(freq[max_freq_index])
# peak_T = 1/peak_freq
# peak_mag = np.abs(X)[max_freq_index]
# point = [peak_freq, peak_mag]

# plt.figure()
# plt.plot(freq, np.abs(X))
# plt.scatter(point[0], point[1], 60, marker="o", color="black", facecolors="none")

# plt.xlabel("Frequency (Hz)")
# plt.ylabel("FFT Magnitude |X(freq)|")
# plt.grid(True)

# plt.show()

# print(f"Found a period of {peak_T:2f} s")
# print(f"This is compared to the known loop time of {typical_loop_time}")

#################################################################################

## once we've found the frequency, use STUMPY to find motifs
peak_T = 0.6
window_size = int(sr * peak_T)
print(f"sr: {sr}, peak_T: {peak_T}")
print(f"Using window_size: {window_size}")

mp = stumpy.stump(data, window_size)
motif_idx = np.argsort(mp[:, 0])[0]

first_motif_idx = np.where(mp[:, 0] == mp[motif_idx, 0])[0][0]

print(f"The motif is located at index {first_motif_idx}")
print(f"this is time {timesteps[first_motif_idx]}")

fig, axs = plt.subplots(2, sharex=True, gridspec_kw={'hspace': 0})
plt.suptitle('Motif (Pattern) Discovery', fontsize='30')

axs[0].plot(data)
axs[0].set_ylabel('Number of Function Calls', fontsize='20')
rect = Rectangle((first_motif_idx, 0), window_size, 40, facecolor='lightgrey')
axs[0].add_patch(rect)
# rect = Rectangle((nearest_neighbor_idx, 0), m, 40, facecolor='lightgrey')
# axs[0].add_patch(rect)
axs[1].set_xlabel('Sample Index', fontsize ='20')
axs[1].set_ylabel('Matrix Profile', fontsize='20')
axs[1].axvline(x=first_motif_idx, linestyle="dashed")
# axs[1].axvline(x=nearest_neighbor_idx, linestyle="dashed")
axs[1].plot(mp[:, 0])
plt.show()
#################################################################################

## trying ML approach from stack overflow () ##
# https://stackoverflow.com/questions/11752727/pattern-recognition-in-time-series

# midpoint = data.size // 2
# dK=230

# # Finding the "pattern" is the hard part--maybe we can use STUMPY for this
# pattern=data[midpoint:midpoint+dK]
# data = np.concatenate((data[:midpoint], data[midpoint + dK:]))

# def create_mats(dat):
#     '''
#     create
#         A - an initial transition matrix
#         pA - pseudocounts for A
#         w - emission distribution regression weights
#         K - number of hidden states
#     '''
#     step=5  #adjust this to change the granularity of the pattern
#     eps=.1
#     dat=dat[::step]
#     K=len(dat)+1
#     A=np.zeros( (K,K) )
#     A[0,1]=1.
#     pA=np.zeros( (K,K) )
#     pA[0,1]=1.
#     for i in range(1,K-1):
#         A[i,i]=(step-1.+eps)/(step+2*eps)
#         A[i,i+1]=(1.+eps)/(step+2*eps)
#         pA[i,i]=1.
#         pA[i,i+1]=1.
#     A[-1,-1]=(step-1.+eps)/(step+2*eps)
#     A[-1,1]=(1.+eps)/(step+2*eps)
#     pA[-1,-1]=1.
#     pA[-1,1]=1.

#     w=np.ones( (K,2) , dtype=float)
#     w[0,1]=dat[0]
#     w[1:-1,1]=(dat[:-1]-dat[1:])/step
#     w[-1,1]=(dat[0]-dat[-1])/step

#     return A,pA,w,K

# # Initialize stuff
# A,pA,w,K=create_mats(pattern)

# eta=10. # precision parameter for the autoregressive portion of the model
# lam=.1  # precision parameter for the weights prior

# N=1 #number of sequences
# M=2 #number of dimensions - the second variable is for the bias term
# T=len(data) #length of sequences

# x=np.ones( (T+1,M) ) # sequence data (just one sequence)
# x[0,1]=1
# x[1:,0]=data

# # Emissions
# e=np.zeros( (T,K) )

# # Residuals
# v=np.zeros( (T,K) )

# # Store the forward and backward recurrences
# f=np.zeros( (T+1,K) )
# fls=np.zeros( (T+1) )
# f[0,0]=1
# b=np.zeros( (T+1,K) )
# bls=np.zeros( (T+1) )
# b[-1,1:]=1./(K-1)

# # Hidden states
# z=np.zeros( (T+1),dtype=int )

# # Expected hidden states
# ex_k=np.zeros( (T,K) )

# # Expected pairs of hidden states
# ex_kk=np.zeros( (K,K) )
# nkk=np.zeros( (K,K) )

# def fwd(xn):
#     global f,e
#     for t in range(T):
#         f[t+1,:]=np.dot(f[t,:],A)*e[t,:]
#         sm=np.sum(f[t+1,:])
#         fls[t+1]=fls[t]+np.log(sm)
#         f[t+1,:]/=sm
#         assert f[t+1,0]==0

# def bck(xn):
#     global b,e
#     for t in range(T-1,-1,-1):
#         b[t,:]=np.dot(A,b[t+1,:]*e[t,:])
#         sm=np.sum(b[t,:])
#         bls[t]=bls[t+1]+np.log(sm)
#         b[t,:]/=sm

# def em_step(xn):
#     global A,w,eta
#     global f,b,e,v
#     global ex_k,ex_kk,nkk

#     x=xn[:-1] #current data vectors
#     y=xn[1:,:1] #next data vectors predicted from current

#     # Compute residuals
#     v=np.dot(x,w.T) # (N,K) <- (N,1) (N,K)
#     v-=y
#     e=np.exp(-eta/2*v**2,e)

#     fwd(xn)
#     bck(xn)

#     # Compute expected hidden states
#     for t in range(len(e)):
#         ex_k[t,:]=f[t+1,:]*b[t+1,:]
#         ex_k[t,:]/=np.sum(ex_k[t,:])

#     # Compute expected pairs of hidden states
#     for t in range(len(f)-1):
#         ex_kk=A*f[t,:][:,np.newaxis]*e[t,:]*b[t+1,:]
#         ex_kk/=np.sum(ex_kk)
#         nkk+=ex_kk

#     # max w/ respect to transition probabilities
#     A=pA+nkk
#     A/=np.sum(A,1)[:,np.newaxis]

#     # Solve the weighted regression problem for emissions weights
#     # x and y are from above
#     for k in range(K):
#         ex=ex_k[:,k][:,np.newaxis]
#         dx=np.dot(x.T,ex*x)
#         dy=np.dot(x.T,ex*y)
#         dy.shape=(2)
#         w[k,:]=lin.solve(dx+lam*np.eye(x.shape[1]), dy)

#     # Return the probability of the sequence (computed by the forward algorithm)
#     return fls[-1]

# if __name__=='__main__':
#     # Run the em algorithm
#     for i in range(20):
#         em_step(x)

#     # Get rough boundaries by taking the maximum expected hidden state for each position
#     r=np.arange(len(ex_k))[np.argmax(ex_k,1)<3]

#     # Plot
#     plt.plot(range(T),x[1:,0])

#     yr=[np.min(x[:,0]),np.max(x[:,0])]
#     for i in r:
#         plt.plot([i,i],yr,'-r')

#     plt.show()
