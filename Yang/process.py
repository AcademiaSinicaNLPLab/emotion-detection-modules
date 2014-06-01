# -*- coding: utf-8 -*-

import re, json, os, sys
from collections import Counter

def output(fn, folder=''):
	# scenario/eval/test/src
	# scenario/Yang/
	outpath = folder+fn.split('/')[-1].replace('.csv','.txt')
	with open(outpath, 'w') as fw:
		fw.write('\n'.join(str_res))
	print >> sys.stderr, 'process',fn,'-->',outpath

def load_docID(docID_dict_path): return json.load(open(docID_dict_path))

def load_test_docID(test_id_path): return open(test_id_path).read().strip().split()

def load_test_res(test_res_path): return [map(float, line.split(',')) for line in open(test_res_path).read().strip().split('\n')]

def map_id_emo(testidList, id2emoLex): return [id2emoLex[docID] for docID in testidList]

if __name__ == '__main__':

	docID_dict_path = 'LJ40K_docid.json'
	test_id_path = 'idx_d.test.txt'
	emolist_path = 'tagNames_LJ40k.txt'

	emolist = sorted(open(emolist_path).read().strip().split('\n'))

	## (global)
	## <dict> docID
	##   |_ <list> [DocName, Emotion]
	id2emoLex = load_docID(docID_dict_path)

	## (global)
	## <list> [testDocID1, ..., testDocIDn]
	testidList = load_test_docID(test_id_path)

	## (global)
	## <list> idx
	##         |_ [DocName, Emotion]
	idemoList = map_id_emo(testidList, id2emoLex)

	for approach_id in range(1,8):

		test_res_path = 'raw/Yest_prob_te_mean_f'+str(approach_id)+'.csv'
		## (local)
		## <list> [prob1, ..., prob40]
		testresList = load_test_res(test_res_path)

		str_res = []
		for i in range(len(idemoList)):
			docName, gold = idemoList[i]
			system = json.dumps(dict(zip(emolist, testresList[i])))
			str_res.append('\t'.join([docName, gold, system]))

		output(test_res_path, folder='../eval/test/src/')

