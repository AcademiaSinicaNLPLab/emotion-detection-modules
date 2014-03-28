# z1(i)=(x1{i}(1)-avg)/(std/39^0.5)

import sys, mathutil, math, json, pickle
import matplotlib.pyplot as plt

# p_value = json.load(open('p-value.json'))

alpha = math.exp(1)

P = pickle.load(open('P-value.dict.pkl'))

PVs = []
print '   '*40, '\t', 'avg', '\t', 'std', '\t', 'z', '\t','p-value'
print '==='*55
for i in range(40):
	# v = [1]+[1]*i+[0]*(39-i)
	# v = [10]+[1]*i+[0]*(39-i)
	v = [1]+[i]+[0]*38

	avg = mathutil.avg(v)
	std = mathutil.standard_deviation(v)

	if std == 0:
		std = 1

	z = (v[0]-avg)/(std/( alpha **0.5))

	z = round(z, 2)

	if z not in P:
		p_value = 0.9999 if z > 0 else -0.9999
	else:
		p_value = P[z]


	print v, '\t', avg, '\t', round(std,3), '\t', z, '\t',p_value
	PVs.append(p_value)



# plt.plot(PVs)
# plt.show()
	# std(v)/39.0

