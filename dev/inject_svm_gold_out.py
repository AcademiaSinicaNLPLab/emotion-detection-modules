### inject gold, out into mongodb

import os, pymongo, sys
from collections import defaultdict

db = pymongo.Connection('doraemon.iis.sinica.edu.tw')['LJ40K']

co_svmout = db['svm.output']
co_svmgold = db['svm.gold']

def inject(directory):
	F = defaultdict(dict)
	try:
		fns = filter(lambda x:x.endswith('.gold.txt') or x.endswith('.out'), os.listdir(directory))
	except:
		print >> stderr, 'cannot list directory:', directory
		return False
	co = None
	for fn in fns:

		fpath = os.path.join(directory, fn)
		chunk = fn.replace('.txt','').split('.')
		mdoc = { 'setting': chunk[0] }
		if chunk[-1] == 'out': # 537b00e33681df445d93d578.c9.out
			co_name = 'svm.output'
			mdoc['ftype'] = chunk[2]
			mdoc['svm_param'] = chunk[1]
			mdoc['prediction'] = open(fpath, 'r').read().strip().split() # prediction = ['15', '15', '19', '15', '2', '15', '19', '15', '6', ... ]
			
		elif chunk[-1] == 'gold': # 537b00e33681df445d93d54c.gold
			co_name = 'svm.gold'
			mdoc['ftype'] = chunk[1]
			
			gold_answer, gold_udocid, gold_emotion = [], [], []
			for line in open(fpath, 'r'):
				line = line.strip()
				if len(line) == 0: continue
				elements = line.split('\t')
				gold_answer.append( elements[0] )
				if len(elements) >= 2:
					gold_udocid.append( elements[1] )
				if len(elements) >= 3:
					gold_emotion.append( elements[2] )

			mdoc['answer'] = gold_answer
			mdoc['udocid'] = gold_udocid
			mdoc['emotion'] = gold_emotion
				# raw_input()
		else:
			continue
		print >> sys.stderr, 'inject', '"'+fn+'"', '-->', co_name
		db[co_name].update( mdoc, mdoc, upsert=True )
	return len(fns)

if __name__ == '__main__':
	inject_count = inject(directory='../tmp')


	## prevent dumping large data in mongodb  
	# db.svm.output.find({},{prediction:0})
	# db.svm.gold.find({},{answer:0, udocid:0, emotion:0})

