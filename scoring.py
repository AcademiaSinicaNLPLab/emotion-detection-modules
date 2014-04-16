# z1(i)=(x1{i}(1)-avg)/(std/39^0.5)

import sys, mathutil, math, json, pickle
import matplotlib.pyplot as plt
from collections import defaultdict

# M1: ps1
# M2: p-value
# M3: gaussian
# M4: probability
# M5: probability + smoothing
Method = 5

## plot or not
toPlot = True

## free
alpha = math.exp(1)


color = ['b','r', 'g', 'k']
markers = ['+', '1', '2', '3', '4']
# labels = ['Case 1','Case 2','Case 3','Case 4']
## custom labels
# custom = ['10, 1...1', '1000, 1...1']
custom = None

x_label = "i-th vector"
y_label = ["possibility", "p-value", "p-value", "probability", "probability"]


D = defaultdict(list)
P = pickle.load(open('data/P-value.dict.pkl'))

def fill(v, num=0, total=40):
	# print total, len(v), total-len(v)
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
	## 1  |   1, 0, 0, 0, ...,0
	## 2  |   1, 1, 0, 0, ...,0
	## 3  |   1, 1, 1, 0, ...,0
	## 4  |   1, 1, 1, 1, ...,0
	## ...
	## 40 |   1, 1, 1, 1, ...,1
	if vtype == 2:
		v = [i+1]+[1]*i+[0]*(39-i)
	

	## 100 |   1, 0, 0, ...,0
	## 100 |   1, 1, 0, ...,0
	## 100 |   1, 1, 1, ...,0
	## ...
	## 100 |   1, 1, 1, ...,1
	if vtype == 3:
		v = [100]+[1]*i+[0]*(39-i)


	## 5 |   0,  0,...,0
	## 5 |   1,  0,...,0
	## 5 |   2,  0,...,0	
	## 5 |   3,  0,...,0	
	## ...
	## 5 |   39, 0,...,0
	if vtype == 4:
		v = [5]+[i]+[0]*38

	return v

def cal_fs1(v):
	avg = mathutil.avg(v)
	nv = mathutil.normalize(v)
	nstd = mathutil.standard_deviation(nv)	

	if nstd == 0: 
		nstd = 1	

	s_bar = avg + nstd*(max(v)-avg)/0.158
	fs1 = v[0]/float(v[0]+s_bar)


	print v, '\t',avg, '\t', max(v), '\t', round(nstd, 3), '\t', s_bar, '\t', round(fs1, 4)

	return fs1

def cal_pval(v):

	avg = mathutil.avg(v)
	std = mathutil.standard_deviation(v)

	nv = mathutil.normalize(v)

	if std == 0: 
		std = 1	

	z = (v[0]-avg)/(std/( alpha**0.5 ))
	z = round(z, 2)
	if z not in P:
		p_value = 0.9999 if z > 0 else -0.9999
	else:
		p_value = P[z]

	print v, '\t',avg, '\t', round(std, 3), '\t', z, '\t', round(p_value, 4)
	# print v, '\t', avg, '\t', round(std,3), '\t', z, '\t',p_value
	return p_value	

def cal_gaussian(V):
	anchor = V[0]
	VR = sorted(V, reverse=True)

	dist = reduce(lambda a,b:a+b, [[i+1]*x+[(i+1)*-1]*x for (i, x) in enumerate(VR)])

	std = mathutil.standard_deviation(dist)
	var = mathutil.variance(dist)

	# xloc = mathutil.avg([i+1 for (i, v) in enumerate(VR) if v == anchor])
	xloc = min([i+1 for (i, v) in enumerate(VR) if v == anchor])

	## -1 or 1
	inverse = -1 if anchor < max(V) else 1

	## cal z
	alpha1 = 1.0/var
	z = (xloc-0)/(std/(alpha**0.5)) * inverse
	# z = (xloc-0)/( std2/(alpha**0.5)) * inverse

	## cal p-value
	z = round(z, 2)
	if z not in P:
		p_value = 0.9999 if z > 0 else -0.9999
	else:
		p_value = P[z]

	if V.count(0) == 39: p_value = 1.0

	print V, '\t',xloc, '\t', max(V), '\t', round(std, 3), '\t', z, '\t', round(p_value, 4)
	return p_value

## v2: proposed by Dr. Ku on Arp. 9
def cal_prob_v2(v, smoothing=False):

	if smoothing == 1:
		v = [x+1/float(len(v)) for x in v]
	elif smoothing == 2:
		v = [x+1/float(len(v)/20) for x in v]

	right = v[1:]
	rightSum = float(sum(right))
	portion = [0 if rightSum == 0 else x/rightSum for x in right]

	rightWeighted = [value*weight for (value, weight) in zip(right, portion)]
	left = v[0]

	r_avg = sum(rightWeighted)
	prob = left/float(left+r_avg)
	print v, '\t',left, '\t', round(r_avg, 3), '\t', round(prob, 4)
	
	return prob

if __name__ == '__main__':
	
	for t in [1,2, 3,4]:

		print

		if Method == 1: # M1: origin
			print '\t'.join(['   '*40, 'avg', 'max', 'nstd', 's_bar', 'fs1'])
		elif Method == 2: # M2: cal_pval
			print '\t'.join(['   '*40, 'avg', 'std', 'z', 'p_value'])
		elif Method == 3:	# M3: cal_gaussian
			print '\t'.join(['   '*40, 'xloc', 'max', 'std', 'z', 'p-value'])
		elif Method == 4:	# M3: cal_gaussian
			print '\t'.join(['   '*40, 'left', 'r-avg', 'prob'])
		elif Method == 5:	# M3: cal_gaussian
			print '\t'.join(['   '*40, 'left', 'r-avg', 'prob'])

		print '==='*55

		for i in range(40):

			v = gen_vector(i, vtype=t)
			
			if Method == 1:
				score = cal_fs1(v)
			elif Method == 2:
				score = cal_pval(v)
			elif Method == 3:
				score = cal_gaussian(v)	
			elif Method == 4:
				score = cal_prob_v2(v)
			elif Method == 5:
				score = cal_prob_v2(v, smoothing=2)

			D[t].append(score)

	if toPlot:
		legend = []
		labels = []
		for i,t in enumerate(D):
			lines = plt.plot(range(40), D[t])
			# lines = plt.scatter(range(40), D[t])
			if not custom:
				labels.append( 'Case ' + str(t) )
			else:
				labels.append( custom[i] )
			plt.setp(lines, color=color[i], linewidth=1.5)

		
		plt.title('Method '+str(Method))
		plt.xlabel(x_label)
		plt.ylabel(y_label[ Method-1 ])
		plt.legend( labels, loc=3)
		plt.ylim([0, 1.1])
		plt.xlim([-0.5, 39])

		plt.show()

