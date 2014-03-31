# z1(i)=(x1{i}(1)-avg)/(std/39^0.5)

import sys, mathutil, math, json, pickle
import matplotlib.pyplot as plt
from collections import defaultdict

# p_value = json.load(open('p-value.json'))

alpha = math.exp(1)
# alpha = 39

P = pickle.load(open('data/P-value.dict.pkl'))

def fill(v, num=0, total=40):
	return v+[num]*(total-len(v))


def gen_vector(i, vtype):

	## 1 |   0, 0,...,0
	## 1 |   1, 0,...,0
	## 1 |   1, 1,...,0
	## ...
	## 1 |   1, 1,...,1
	if vtype == 1:
		v = [1]+[1]*i+[0]*(39-i)

	## normalized, balance sum
	## 1 |   0,   0,     0, ...,0
	## 1 |   1,   0,     0, ...,0
	## 1 |   0.5, 0.5,   0, ...,0
	## 1 |   0.3, 0.3, 0.3, ...,0
	## ...
	## 1 |   0.025, 0.025,...,0.025
	if vtype == 2:

		v = [i+1] + [1]*(i+1)
		v = fill(v, num=0, total=40)
		# ni = 0 if i ==0 else 1.0/i
		# v = [1]+[ni]*i+[0]*(39-i)
	

	## 10|   0, 0,...,0
	## 10|   1, 0,...,0
	## 10|   1, 1,...,0
	## ...
	## 10|   1, 1,...,1
	if vtype == 3:
		v = [10]+[1]*i+[0]*(39-i)


	## 1 |   0,  0,...,0
	## 1 |   1,  0,...,0
	## 1 |   2,  0,...,0	
	## 1 |   3,  0,...,0	
	## ...
	## 1 |   39, 0,...,0
	if vtype == 4:
		v = [1]+[i]+[0]*38

	return v

def cal_fs1(v, avg, nstd):
	s_bar = avg + nstd*(max(v)-avg)/0.158
	fs1 = v[0]/float(v[0]+s_bar)
	return fs1

def cal_pval(v, avg, std, P):
	z = (v[0]-avg)/(std/( alpha**0.5 ))
	z = round(z, 2)
	if z not in P:
		p_value = 0.9999 if z > 0 else -0.9999
	else:
		p_value = P[z]
	print v, '\t', avg, '\t', round(std,3), '\t', z, '\t',p_value
	return p_value	


def cal_gaussian(V):
	anchor = V[0]
	VR = sorted(V, reverse=True)


	# print VR
	# for i,x in enumerate(VR):
	# 	print i+1, x
		# print [i+1]*x+[(i+1)*-1]*x


	dist = reduce(lambda a,b:a+b, [[i+1]*x+[(i+1)*-1]*x for (i, x) in enumerate(VR)])

	# print dist

	std = mathutil.standard_deviation(dist)
	var = mathutil.variance(dist)

	xloc = mathutil.avg([i+1 for (i, v) in enumerate(VR) if v == anchor])

	## -1 or 1
	inverse = -1 if anchor < max(V) else 1

	## cal z
	alpha1 = 1.0/var
	z = (xloc-0)/(std/(alpha1**0.5)) * inverse

	## cal p-value
	z = round(z, 2)
	if z not in P:
		p_value = 0.9999 if z > 0 else -0.9999
	else:
		p_value = P[z]

	if V.count(0) == 39: p_value = 1.0

	print V, '\t',xloc, '\t', max(V), '\t', round(std, 3), '\t', z, '\t', round(p_value, 4)
	return p_value

if __name__ == '__main__':


	PVs, FS1, GDs = [], [], []

	GDs = defaultdict(list)

	# print '   '*40, '\t', 'mean', '\t', 'std', '\t', 'z', '\t','p-value'

	color = ['b','g', 'r', 'y']
	# label = ['1 | [0,0,...,0] ~ [1,1,...,1]', '10 | [0,0,...,0] ~ [1,1,...,1]', '1 | [0,0,...,0] ~ [39,0,...,0]']
	label = ['1','2','3','4']

	for t in [1,2,3,4]:
		print '\t'.join(['   '*40, 'xloc', 'max', 'std', 'z', 'p-value'])
		# print '   '*40, '\t', 'mean', '\t', 'std', '\t', 'z', '\t','p-value'
		print '==='*55
		for i in range(40):

			v = gen_vector(i, vtype=t)

			avg = mathutil.avg(v)
			std = mathutil.standard_deviation(v)

			nv = mathutil.normalize(v)
			nstd = mathutil.standard_deviation(nv)

			if std == 0: std = 1
			if nstd == 0: nstd = 1
				
			g = cal_gaussian(v)
			GDs[t].append(g)

		# print v

		### calculate fs1
		# fs1 = scoring_fs1(v, avg, nstd)
		# FS1.append(fs1)
		
		### calculate p-value
		# p_value = cal_pval(v, avg, std, P)
		# PVs.append(p_value)
		
		



	# plt.plot(PVs)
	legend = []
	for i,t in enumerate(GDs):
		# print i, t
		# print color[i]
		# print label[i]
		plt.plot(range(40), GDs[t], color=color[i])
		legend.append('Case '+label[i])
	# plt.plot(FS1)
	plt.xlabel("# of zero in a vector")
	plt.ylabel("p-value")
	plt.legend( legend, loc='upper right')
	# plt.legend(loc='upper right')
	plt.ylim([0, 1.1])
	plt.xlim([0, 39])

	plt.show()

