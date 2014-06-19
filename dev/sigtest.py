from collections import Counter

import pymongo
db = pymongo.Connection('localhost')['LJ40K']
emotions = sorted([x['emotion'] for x in list(db['emotions'].find({'label': 'LJ40K'}))])
eid_map = dict(list(enumerate(emotions)))

def process_top1(Afn, Bfn, level):
	n = Counter()
	# P, N = [], []
	Alines = open('../cache/fusion/'+Afn).read().strip().split('\n')
	Blines = open('../cache/fusion/'+Bfn).read().strip().split('\n')

	for Aline, Bline in zip(Alines, Blines):

		Aline = Aline.strip().split()
		Bline = Bline.strip().split()

		glod = int(Aline[0])

		Aseq = sorted(list(enumerate([float(x) for x in Aline[1:]])),key=lambda x:x[1], reverse=True)
		Bseq = sorted(list(enumerate([float(x) for x in Bline[1:]])),key=lambda x:x[1], reverse=True)

		Apredict, Aaccu = Aseq[0]
		Bpredict, Baccu = Bseq[0]

		if gold != Apredict and gold !=Bpredict:
			n['n00'] += 1
		elif gold != Apredict and gold == Bpredict:
			n['n01'] += 1
		elif gold == Apredict and gold != Bpredict:
			n['n10'] += 1
		elif gold == Apredict and gold == Bpredict:
			n['n11'] += 1

	chi_square = (abs(n['n01'] - n['n10'])-1)**2 / float(n['n01']+n['n10'])
	one_star, double_star = level
	if chi_square >= double_star:
		sig = '**'
	elif chi_square >= one_star:
		sig = '*'
	else:
		sig = '-'

def process_multi(Afn, Bfn, level):
	
	# P, N = [], []
	Alines = open('../cache/fusion/'+Afn).read().strip().split('\n')
	Blines = open('../cache/fusion/'+Bfn).read().strip().split('\n')

	N = {}
	for target in range(40):


		N[target] = Counter()
		for Aline, Bline in zip(Alines, Blines):

			Aline = Aline.strip().split()
			Bline = Bline.strip().split()

			glod = int(Aline[0])

			Ascore = {i:a for (i,a) in enumerate([float(x) for x in Aline[1:]])}
			Bscore = {i:a for (i,a) in enumerate([float(x) for x in Bline[1:]])}

			if gold == target and Ascore[target] >= 0.5  or  gold != target and Ascore[target] < 0.5: A = True
			elif gold == target and Ascore[target] < 0.5  or gold != target and Ascore[target] >= 0.5: A = False

			if gold == target and Bscore[target] >= 0.5  or  gold != target and Bscore[target] < 0.5: B = True
			elif gold == target and Bscore[target] < 0.5  or gold != target and Bscore[target] >= 0.5: B = False


			if not A and not B:
				N[target]['n00'] += 1
				# N[target]['d'] += 1
			elif not A and B:
				N[target]['n01'] += 1
				# N[target]['c'] += 1
			elif A and not B:
				N[target]['n10'] += 1
				# N[target]['b'] += 1
			elif A and B:
				N[target]['n11'] += 1
				# N[target]['a'] += 1

	one_star, double_star = level
	print '| examples | chi_square | emotion | significance |'
	print '| -------- | ---------- | ------- | ------------ |'
	for target in range(40):
		chi_square = (abs(N[target]['n01'] - N[target]['n10'])-1)**2 / float((N[target]['n01']+N[target]['n10']))
		# chi_square = (abs(N[target]['b'] - N[target]['c'])-1)**2 / (N[target]['b']+N[target]['c'])

		if chi_square >= double_star:
			sig = '**'
		elif chi_square >= one_star:
			sig = '*'
		else:
			sig = '-'


		print '| %s | %.2f | %s | %s |' % (json.dumps(N[target]), chi_square, eid_map[target], sig )
		# print chi_square

		# if chi_square > threshold_chi:
		# 	print eid_map[target], '\t', chi_square, '\t', 'sig'
		# else:
		# 	print eid_map[target], '\t', chi_square, '\t','not sig'


def chi_to_p(df=39):
	
	P = [0.995,	0.975,	0.20,	0.10,	0.05,	0.025,	0.02,	0.01,	0.005,	0.002,	0.001]
	C = [19.996,23.654,	46.173,	50.660,	54.572,	58.120,	59.204,	62.428,	65.476,	69.294,	72.055]

	# alpha = 0.05

	one_star = dict(zip(P, C))[0.05]
	double_star = dict(zip(P, C))[0.01]

	return (one_star, double_star)

if __name__ == '__main__':

	Afn = '538bcfaad4388c59136665df#c2g0.001t2+537451d1d4388c7843516ba4#c9g0.0005t2+53875eead4388c4eac581415#c2g0.001t2_1.0x0.0x0.0.csv'
	Bfn = '538bcfaad4388c59136665df#c2g0.001t2+537451d1d4388c7843516ba4#c9g0.0005t2+53875eead4388c4eac581415#c2g0.001t2_0.4x0.4x0.2.csv'


	level = chi_to_p()

	process_top1(Afn, Bfn, level)
	process_multi(Afn, Bfn, level)
	


