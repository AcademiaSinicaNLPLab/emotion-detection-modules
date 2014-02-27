# -*-  coding: utf-8 -*-

import sys, json, os
from collections import Counter
import reduce_target

R = '\033[0;32;31m'
G = '\033[0;32;32m'
B = '\033[0;32;34m'
Y = '\033[1;33m'
N = '\033[m'
LP = '\033[1;35m'
LC = '\033[1;36m'
W = '\033[1;37m'

data_path = '../data'

# input format: [doc_id]   [gold]   [system]

def accuracy(res, target_emotions):

	TP = res['TP']
	TN = res['TN']/float(len(target_emotions))
	FP = res['FP']/float(len(target_emotions))
	FN = res['FN']
	
	return round((TP+TN)/float(TP+TN+FN+FP), 4)

def topk_eval(input_doc, target_gold, K=1):

	Positive, Negative = True, False
	result = Counter()

	if type(input_doc) == dict:
		src = input_doc.items()
		FILE = False

	elif type(input_doc) == str:
		src = open(input_doc)
		FILE = True

	else: # for now, only accept <dict> and <str> as input
		return False

	for entry in src:
		if FILE:
			doc_id, gold, system_str = entry.strip().split('\t')
			system = [(e,score) for (e,score) in sorted(json.loads(system_str).items(), key=lambda x:x[1], reverse=True) if score != 0.0]

		else:
			((gold, doc_id), system_dict) = entry
			system = [(e,score) for (e,score) in sorted(system_dict.items(), key=lambda x:x[1], reverse=True) if score != 0.0]

		answer = [e for (e,score) in system[:K]]

		really_is = Positive if target_gold == gold else Negative
		classified_as = Positive if target_gold in answer else Negative

		TP = classified_as == Positive and really_is == Positive
		TN = classified_as == Negative and really_is == Negative
		FP = classified_as == Positive and really_is == Negative
		FN = classified_as == Negative and really_is == Positive

		result['TP'] += 1 if TP else 0
		result['TN'] += 1 if TN else 0
		result['FP'] += 1 if FP else 0
		result['FN'] += 1 if FN else 0

	return result

def topk(input_doc, target_gold, K=3):


	for line in open(input_doc):
		if line.startswith('#'): continue
		doc_id, gold, system_str = line.strip().split('\t')
		# print system_str

		system = [(e,score) for (e,score) in sorted(json.loads(system_str).items(), key=lambda x:x[1], reverse=True) if score != 0.0]

		answer = [e for (e,score) in system[:K]]

		# print >> sys.stderr, '>',Y,'G:',gold, LC,'A:',answer, LP,'T:',target_gold,N
		really_is = Positive if target_gold == gold else Negative
		classified_as = Positive if target_gold in answer else Negative

		TP = classified_as == Positive and really_is == Positive
		TN = classified_as == Negative and really_is == Negative
		FP = classified_as == Positive and really_is == Negative
		FN = classified_as == Negative and really_is == Positive

		result['TP'] += 1 if TP else 0
		result['TN'] += 1 if TN else 0
		result['FP'] += 1 if FP else 0
		result['FN'] += 1 if FN else 0

		# print >> sys.stderr, ' ',G if TP else R, 'TP', N,
		# print >> sys.stderr, ' ',G if TN else R, 'TN', N,
		# print >> sys.stderr, ' ',G if FP else R, 'FP', N,
		# print >> sys.stderr, ' ',G if FN else R, 'FN', N
	return result

def extract_targets(input_doc):
	if type(input_doc) == dict:
		src = input_doc.items()
		return sorted(list(set([x[0][0] for x in src])))

	elif type(input_doc) == str:
		src = open(input_doc)
		return sorted(list(set([line.strip().split('\t')[1] for line in src])))

def init():
	if not os.path.exists('test'): os.mkdir('test')
	if not os.path.exists('test/src'): os.mkdir('test/src')
	if not os.path.exists('test/res'): os.mkdir('test/res')

if __name__ == '__main__':

	K = 3
	
	init()

	input_path = sys.argv[1]
	
	path_stack = [p for p in input_path.split('/') if len(p)>0]

	input_srcs = ['/'.join(path_stack+[f]) for f in os.listdir(input_path) if f.endswith('.txt')] if os.path.isdir(input_path) else [input_path]

	for input_doc in input_srcs:

		res_path = input_doc.replace('.txt','.res.'+'top'+str(K)+'.txt').replace('test/src','test/res')
	
		print >> sys.stderr, '='*30
		print >> sys.stderr, '# test file:' ,G,input_doc,N
		print >> sys.stderr, '# result path:' ,Y,res_path,N
		print >> sys.stderr, '='*30

		target_emotions = extract_targets(input_doc)

		R = []

		for target_emotion in target_emotions:

			print >> sys.stderr, '> process',LC,target_emotion,N
			
			results = topk_eval(input_doc, target_emotion, K) # Top K

			acc = accuracy(results, target_emotions)

			# R.append((target_emotion, acc))
			res_entry = {'target':target_emotion, 'accuracy':acc, 'instances':results}
			R.append(res_entry)

		with open(res_path, 'w') as fw:
			SR = sorted(R, key=lambda x:x['accuracy'], reverse=True) # sort by accuracy
			fw.write('\n'.join([res_entry['target']+'\t'+str(res_entry['accuracy']) for res_entry in SR]))
		
		## reduce res
		emolist_pathes = [data_path+'LJ40K.emolist', data_path+'Mishne05.emolist']
		lines = reduce_target.filter_lines(res_path, emolist_pathes)
		reduce_target.output(lines, res_path, emolist_pathes)

		print >> sys.stderr, '='*30
		print >> sys.stderr, '# results reduced',N,'\n'
