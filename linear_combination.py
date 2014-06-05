# combine binary classifier probibility

import os,sys,pickle,subprocess

import evaluate_fusion

# for i in range(40):
# 	# 1.b.c2g0.001t2.p.out
# 	# 1.b.gold
# 	gold_fn = str(i)+'.b.gold'
# 	out_fn = str(i)+'.b.'+param+'.p.out'

# 	col = map(lambda x:x.strip().split()[1], open('tmp/'+sid+'/'+out_fn).read().strip().split('\n')[1:])
# 	cols.append(col)


def load(sid, param, prob):
	# 0.b.default.out
	# 0.b.gold
	root = 'tmp/'+sid
	if prob:
		related_files = [x for x in os.listdir(root) if x.endswith(param+'.p.out') or x.endswith('.gold')]
	else:
		related_files = [x for x in os.listdir(root) if x.endswith(param+'.out') or x.endswith('.gold')]

	out_files = [x for x in related_files if x.endswith('.out')]
	gold_files = [x for x in related_files if x.endswith('.gold')]

	if len(out_files) == 0:
		print 'no output files for sid =',sid, 'param =',param
		print 'use: python run_binary_svm.py '+sid+' '+param+' -p'
		print 
		return False

	Res = {}

	## load gold
	gold_label_in_eids = []
	for gold_file in gold_files:
		eid = gold_file.split('.')[0] # gold_file: "0.b.gold"
		gold_label_in_eid = [eid if x == '+1' else False for x in open(os.path.join(root,gold_file) ).read().strip().split('\n')]
		gold_label_in_eids.append(gold_label_in_eid)

	# list of eids: [0,0,....,1,..1,...39,39,...39]
	gold_labels = [reduce(lambda a,b:a or b, x) for x in zip(*gold_label_in_eids)]

	out_files = sorted(out_files, key=lambda x:int(x.split('.')[0]))

	predictions = []
	for out_file in out_files:
		eid = out_file.split('.')[0] # out_file: "0.b.default.out", eid: '0'

		if not prob:
			prediction = open(os.path.join(root,out_file) ).read().strip().split('\n')
		else:
			prediction = map(lambda x:x.split()[1], open(os.path.join(root,out_file) ).read().strip().split('\n')[1:])

		predictions.append(prediction)
	predict_labels = zip(*predictions)

	prediction_results = zip(gold_labels, predict_labels)
	return prediction_results

# kw-TF3xIDF2	{ "_id" : ObjectId("538bcfaad4388c59136665df"), "keyword_type" : "extend", "lemma" : true, "TFIDF_type" : "TF3xIDF2", "feature_name" : "keyword_TFIDF" }
# kw-emo-s-50%	[score] cut 50, min_count 4, -frequency (538a1df3d4388c32be4c2c9b)
# kw-bag	extend, lemma (537451d1d4388c7843516ba4)
# pat-emo-b-50%	[b] cut 50, min_count 4, -frequency (53876efbd4388c3e013e9272)

def apply_weight(prediction_results, weight):
	return [(gold, map(lambda x: float(x)*weight, predicts)) for gold, predicts in prediction_results]

def run(candidates, weights=[]):

	normalized_weights = [x/float(sum(weights)) for x in weights]

	# print normalized_weights

	systems = [(x[0],x[1], normalized_weights[i]) for i,x in enumerate(candidates)]

	# for sid, param, weight in systems:
	# 	print sid, param, 'x',weight 


	fn = 'fusion'+'x'.join([str(x[2]) for x in systems])+'.csv'

	if not os.path.exists('cache/fusion/'+fn):

		# print 'fusion','x'.join([str(x[2]) for x in systems])

		weighted_results = []
		for sid, param, weight in systems:
			res = load(sid, param, prob=True)
			weighted_res = apply_weight(res, weight)
			weighted_results.append(weighted_res)

		

		fw = open('cache/fusion/'+fn, 'wb')
		for line in zip(*weighted_results):
			label = line[0][0]
			probs = [round(reduce(lambda a,b:a+b, x), 4) for x in zip(*map(lambda x:x[1], line))]
			str_line = ' '.join([label] + [str(x) for x in probs])
			fw.write(str_line + '\n')
		fw.close()

	# print 'evaluation'
	pkl_fn = fn.replace('.csv','.pkl')
	if not os.path.exists('cache/fusion/'+pkl_fn):
		eval_mdoc = evaluate_fusion.evaluation('cache/fusion/'+fn, k='binary')
		pickle.dump(eval_mdoc, open('cache/fusion/'+pkl_fn, 'wb'))
	else:
		eval_mdoc = pickle.load(open('cache/fusion/'+pkl_fn, 'rb'))

	evaluate_fusion.find_intersection(eval_mdoc, show=False)



# def grid(candidates, length=4, ranges=10, step=1):
# 	weight_list = [x for x in ListCombination([ range(ranges) for x in range(length)]) if sum(x) == 10 and 0 not in x]
# 	for i, w in enumerate(weight_list): 
# 		print w, '\t','('+str(i+1)+'/'+str(len(weight_list))+')'
# 		run(candidates, weights=w)

def generate(length=4, ranges=10, step=1, core=8):
	from itertools import product
	from ListCombination import ListCombination

	weight_list = [x for x in ListCombination([ range(ranges) for x in range(length)]) if sum(x) == 10]
	wl = len(weight_list)
	parts = [wl/core]*(core-1) + [wl/core + wl%core]

	p = wl/core
	pws = []
	for i in range(core):
		b = i*p
		e = (i+1)*p+wl%core if i == core - 1 else (i+1)*p
		pw = weight_list[b:e]
		pws.append(pw)

	for i in range(core):
		sh_fn = str(i)+'_LC.sh'
		fw = open(sh_fn, 'w')
		for ws in pws[i]:
			fw.write('python linear_combination.py '+' '.join(map(lambda x:str(x), ws)) + '\n')
		fw.close()
		subprocess.call(['chmod','+x',sh_fn])

	# pws[-1].append(weight_list[-1*wl%core:])
		# print len(weight_list[c*parts[c]:(c+1)*parts[c]])

def find_max():
	A = []
	for fn in os.listdir('cache/fusion/'):
		if fn.startswith('fusion') and fn.endswith('.pkl'):
			eval_mdoc = pickle.load(open('cache/fusion/'+fn, 'rb'))
			# evaluate_fusion.find_intersection()
			# print fn
			# print eval_mdoc['avg_accuracy']
			A.append((eval_mdoc['avg_accuracy'], fn))
	print sorted(A, key=lambda x:x[0], reverse=True)[:5]

if __name__ == '__main__':
	
	prob = True

	candidates = [
		["538bcfaad4388c59136665df", 'c2g0.001t2'], 	# TF3xIDF2					3
		["538a1df3d4388c32be4c2c9b", 'c2g0.001t2'],		# kw-emo-s-50%				1
		["537451d1d4388c7843516ba4", 'c9g0.0005t2'],	# kw-bag					2
		["53876efbd4388c3e013e9272", 'c9g0.0005t2'],	# pat-emo-b-50%				2
		["537c6c90d4388c0e27069e7b", 'c9g0.005t2'],		# pat-bag					2
														# 63.54%
		# ['538aec90d4388c49cb5c2705', 'c9g0.0001t2']		# pat-emo-s-pos-50%
	]
	# 0.4x0.1x0.3x0.1x0.1x0.0
	#0.3x0.1x0.2x0.2x0.2x0.0
	normalized_weights = [1.0/len(candidates)]*len(candidates)

	if len(sys.argv) == 2:
		if sys.argv[1] == 'generate':
			generate(length=len(candidates), ranges=10, step=1, core=8)
		elif sys.argv[1] == 'max':
			find_max()
	else:

		if len(sys.argv[1:]) == len(candidates):
			ws = [float(x.strip()) for x in sys.argv[1:]]
			normalized_weights = [x/float(sum(ws)) for x in ws]
		print 
		print normalized_weights
		
		run(candidates, weights=normalized_weights)



