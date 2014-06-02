# -*- coding: utf-8 -*-
import config
import color
import re
import pymongo, sys, os
from collections import Counter, defaultdict
# from itertools import product
from pprint import pprint
# import logging

db = pymongo.Connection(config.mongo_addr)[config.db_name]
Positive, Negative = True, False
# eval_mdoc = None

def accuracy(res, ratio=1):
	TP = res['TP']
	TN = res['TN']/float(ratio)
	FP = res['FP']/float(ratio)
	FN = res['FN']
	return 0.0 if TP+TN+FN+FP == 0 else round((TP+TN)/float(TP+TN+FN+FP), 4)

def precision(res, ratio=1):
	TP = res['TP']
	TN = res['TN']/float(ratio)
	FP = res['FP']/float(ratio)
	FN = res['FN']
	return 0.0 if TP+FP == 0 else round((TP)/float(TP+FP), 4)

def recall(res, ratio=1):
	TP = res['TP']
	TN = res['TN']/float(ratio)
	FP = res['FP']/float(ratio)
	FN = res['FN']
	return 0.0 if TP+FN == 0 else round((TP)/float(TP+FN), 4)

def load_eval_from_mongo(sid, param, prob):
	eval_mdoc = co_svm_eval.find_one({'setting': sid, 'param': param, 'prob': prob})
	return False if not eval_mdoc else eval_mdoc

def save_eval_to_mongo(sid, param, prob, results):
	eval_mdoc = {'setting': sid, 'param': param, 'prob':prob}
	for measure in ['accuracy', 'precision', 'recall', 'f1']:
		eval_mdoc[measure] = dict(results[measure])
		eval_mdoc['avg_'+measure] = round(sum(map(lambda x:x[1], results[measure]))/float(len(results[measure])), 4)
	co_svm_eval.insert(eval_mdoc)
	co_svm_eval.create_index([('setting', pymongo.ASCENDING), ('param', pymongo.ASCENDING)])
	return eval_mdoc

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
		print 'no output files'
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


def evaluate_binary_svm(pairs, prob, topk=1):
	# ('0',	('-1', '1', '1', '-1', '1', '-1', '-1', '1', '-1', '-1', '-1', '-1', '-1', '-1', '-1', '1', '1', '1', '1', '-1', '1', '1', '1', '-1', '-1', '-1', '-1', '1', '-1', '-1', '-1', '-1', '1', '-1', '1', '1', '1', '-1', '-1', '-1'))
	# ('39',('1', '-1', '-1', '1', '-1', '1', '-1', '-1', '1', '1', '-1', '1', '1', '1', '1', '-1', '-1', '1', '-1', '1', '1', '-1', '-1', '-1', '1', '1', '1', '-1', '-1', '-1', '-1', '1', '-1', '-1', '1', '1', '-1', '-1', '1', '1'))
	
	LJ40K_emotions = sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}) ])
	eid_to_emotion = { str(i):x for i, x in enumerate(LJ40K_emotions)}

	## target_eids: ['0', '1', ..., '39']
	target_eids = sorted( list(set([x[0] for x in pairs])) , key=lambda a:int(a))

	Results = defaultdict(list)

	for target_eid in target_eids:

		emotion = eid_to_emotion[target_eid]

		print >> sys.stderr, '>',emotion

		really_is_positive, really_is_negative = 0, 0
		res = Counter()
		
		for gold_label, binary_predict in pairs:

			
			if prob:
				predict = [str(eid) for eid, p in sorted(list(enumerate(binary_predict)), key=lambda x:float(x[1]),reverse=True)]
			else:
				# print binary_predict
				# for i, p in enumerate(binary_predict):

				# raw_input()
				predict = [str(i) for i, p in enumerate(binary_predict) if int(p) > 0]
			
				# print predict
			really_is = Positive if target_eid == gold_label else Negative



			if prob:
				classified_as = Positive if target_eid in predict[:topk] else Negative
			else:
				classified_as = Positive if target_eid in predict else Negative

			# print 'target_eid:',target_eid, type(target_eid), target_eid in predict[:topk]
			# print 'gold_label:',gold_label
			# print 'binary_predict:',binary_predict
			# print 'predict:',predict
			# print 'predict[:topk]:',predict[:topk]
			# print 'really_is:',really_is
			# print 'classified_as:',classified_as
			# raw_input()				

			really_is_positive += 1 if really_is == Positive else 0
			really_is_negative += 1 if really_is == Negative else 0

			TP = classified_as == Positive and really_is == Positive
			TN = classified_as == Negative and really_is == Negative
			FP = classified_as == Positive and really_is == Negative
			FN = classified_as == Negative and really_is == Positive

			# print 'TP:',TP
			# print 'TN:',TN
			# print 'FP:',FP
			# print 'FN:',FN

			res['TP'] += 1 if TP else 0
			res['TN'] += 1 if TN else 0
			res['FP'] += 1 if FP else 0
			res['FN'] += 1 if FN else 0

		r = really_is_negative/float(really_is_positive)
		A = accuracy(res, ratio=r)
		P = precision(res, ratio=r)
		R = recall(res, ratio=r)
		F = round(2*P*R/float(P+R), 4) if P+R > 0 else 0.0

		if config.verbose: print >> sys.stderr, A

		Results['accuracy'].append((emotion, A))
		Results['precision'].append((emotion, P))
		Results['recall'].append((emotion, R))
		Results['f1'].append((emotion, F))

	return Results

def find_intersection(eval_mdoc):

	LJ40K = sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}) ])
	Mishne05 = sorted([x['emotion'] for x in db['emotions'].find({'label':'Mishne05'}) ])

	inter = []
	for e in set(LJ40K+Mishne05):
		if e in LJ40K and e in Mishne05: inter.append(e)
		
	inter_accuracy = {}
	for e in eval_mdoc['accuracy']:
		if e in inter:
			inter_accuracy[e] = eval_mdoc['accuracy'][e]

	pprint(eval_mdoc['accuracy'])

	print >> sys.stderr, 'avg accuracy in overall\t\t', color.render( str(eval_mdoc['avg_accuracy']), 'g')
	print >> sys.stderr, 'avg accuracy in intersection\t', color.render( str(round( sum(inter_accuracy.values())/float(len(inter_accuracy.values())), 4)), 'y')


def run(sid, param, prob):

	eval_mdoc = load_eval_from_mongo(sid, param, prob)

	if not eval_mdoc or overwrite:
		prediction_results = load(sid, param, prob)

		if not prediction_results:
			print 'no prediction results for this param'
			exit(-1)

		results = evaluate_binary_svm(prediction_results, prob)

		eval_mdoc = save_eval_to_mongo(sid, param, prob, results)
		if not eval_mdoc: 
			print >> sys.stderr, "[error] failed to save eval mdoc to mongo"
			exit(-1)
	return eval_mdoc

if __name__ == '__main__':


	# sid = '53875eead4388c4eac581415'
	# param = 'default'

	sid = sys.argv[1]
	param = sys.argv[2]

	if '-p' in sys.argv or '--prob' in sys.argv: prob = True
	else: prob = False

	if '-o' in sys.argv or '--overwrite' in sys.argv: overwrite = True
	else: overwrite = False

	co_svm_eval = db['svm.binary.eval']

	eval_mdoc = run(sid, param, prob)
	find_intersection(eval_mdoc)
	


