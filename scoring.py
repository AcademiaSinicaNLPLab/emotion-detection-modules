# z1(i)=(x1{i}(1)-avg)/(std/39^0.5)

import sys, mathutil, math, json, pickle
import matplotlib.pyplot as plt

# p_value = json.load(open('p-value.json'))

# alpha = math.exp(1)
alpha = 39

P = pickle.load(open('data/P-value.dict.pkl'))

def gen_vector(i, vtype):

	## 1 |   0, 0,...,0
	## 1 |   1, 0,...,0
	## 1 |   1, 1,...,0
	if vtype == 1:
		v = [1]+[1]*i+[0]*(39-i)

	## normalized, balance sum
	## 1 |   0,   0,     0, ...,0
	## 1 |   1,   0,     0, ...,0
	## 1 |   0.5, 0.5,   0, ...,0
	## 1 |   0.3, 0.3, 0.3, ...,0
	if vtype == 2:
		ni = 0 if i ==0 else 1.0/i
		v = [1]+[ni]*i+[0]*(39-i)
	

	## 10|   0, 0,...,0
	## 10|   1, 0,...,0
	## 10|   1, 1,...,0
	if vtype == 3:
		v = [10]+[1]*i+[0]*(39-i)


	## 1 |   0, 0,...,0
	## 1 |   1, 0,...,0
	## 1 |   2, 0,...,0	
	## 1 |   3, 0,...,0	
	if vtype == 4:
		v = [1]+[i]+[0]*38

	return v

if __name__ == '__main__':


	PVs = []
	FS1 = []
	print '   '*40, '\t', 'avg', '\t', 'std', '\t', 'z', '\t','p-value'
	print '==='*55
	for i in range(40):

		v = gen_vector(i, vtype=3)

		avg = mathutil.avg(v)
		std = mathutil.standard_deviation(v)

		nv = mathutil.normalize(v)
		nstd = mathutil.standard_deviation(nv)

		if std == 0: std = 1
		if nstd == 0: nstd = 1
			
	
		### calculate fs1
		s_bar = avg + nstd*(max(v)-avg)/0.158
		fs1 = v[0]/float(v[0]+s_bar)
		FS1.append(fs1)
		# print v, fs1
		
		### calculate p-value


		z = (v[0]-avg)/(std/( alpha **0.5))
		z = round(z, 2)
		if z not in P:
			p_value = 0.9999 if z > 0 else -0.9999
		else:
			p_value = P[z]
		print v, '\t', avg, '\t', round(std,3), '\t', z, '\t',p_value
		PVs.append(p_value)
	# print 
	print PVs
	print FS1
	plt.plot(PVs)
	plt.plot(FS1)

	# lims = plt.ylim()
	plt.ylim([0.0, 1.1])
	plt.xlim([0, 39])
	# print lims
	# xlim([lims[1], lims[0]]) 
	plt.show()
	# std(v)/39.0

