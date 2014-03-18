import pymongo, sys
from collections import Counter
mc = pymongo.Connection('doraemon')
db = mc['LJ40K']

# get all emotions
emotions = sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}) ])

co_docscore = db['docscore']
co_docs = db['docs']
co_test_instances = db['test_instances']

cfg = {
	'ds_function': 1,
	'ps_function': 1,
	'smoothing':  0,
	'sig_function': 0,
	'epsilon':  0.5	
}

## input: config
## output: inject test instances into mongo collection

def gen_test(cfg):
	for gold_emotion in emotions:
		for doc in co_docs.find( { 'emotion': gold_emotion, 'ldocID': {'$gte': 800}} ):
			_udocID = doc['udocID']

			## generate result vector
			res_vector = {}
			for test_emotion in emotions:

				query = {
						'udocID': _udocID,
						'gold_emotion': gold_emotion,
						'test_emotion': test_emotion,
				}
				## add config info
				query.update(cfg)

				res = co_docscore.find_one(query)
				if not res:
					print >> sys.stderr, 'check parameters'
					exit()
				else:
					res_vector[test_emotion] = res['predict']

			## store gold and predict into mongo

			test_instance = {
				'udocID': _udocID,
				'gold_emotion': gold_emotion
			}
			test_instance.update(cfg)

			co_test_instances.update( test_instance, { '$set': {'predict': res_vector } }, upsert=True )

			# test_instance['predict'] = res_vector

			# co_test_instances.insert( test_instance )

def fetch_insts(cfg):
	return list(db['test_instances'].find( cfg, {'_id':0, 'gold_emotion':1, 'predict': 1, 'udocID':1} ))

def accuracy(res, ratio=1):
	TP = res['TP']
	TN = res['TN']/float(ratio)
	FP = res['FP']/float(ratio)
	FN = res['FN']
	return round((TP+TN)/float(TP+TN+FN+FP))

def precision(res, ratio=1):
	TP = res['TP']
	TN = res['TN']/float(ratio)
	FP = res['FP']/float(ratio)
	FN = res['FN']
	return round((TP)/float(TP+FP))

def recall(res, ratio=1):
	TP = res['TP']
	TN = res['TN']/float(ratio)
	FP = res['FP']/float(ratio)
	FN = res['FN']
	return round((TP)/float(TP+FN))

# def fscore(P, R, f=1, ratio=1):
# 	P = precision(res, ratio=ratio)
# 	R = recall(res, ratio=ratio)
# 	return 2*P*R/float(P+R)

def evals(cfg):

	Positive, Negative = True, False

	insts = fetch_insts(cfg)

	# target: happy
	# really is Positive
	# 	classify as happy	
	#	classify as ~happy	
	# really is Negative	
	# 	classify as happy	
	# 	classify as ~happy	

	Results = {}

	for target_gold in emotions:

		really_is_positive = 0
		really_is_negative = 0

		res = Counter()
		for inst in insts:

			really_is = Positive if target_gold == inst['gold_emotion'] else Negative
			classified_as = Positive if inst['predict'][target_gold] == 1 else Negative

			## stat really_is_Positive: really_is_Negative = 200: 7900
			really_is_positive += 1 if really_is == Positive else 0
			really_is_negative += 1 if really_is == Negative else 0

			TP = classified_as == Positive and really_is == Positive
			TN = classified_as == Negative and really_is == Negative
			FP = classified_as == Positive and really_is == Negative
			FN = classified_as == Negative and really_is == Positive

			res['TP'] += 1 if TP else 0
			res['TN'] += 1 if TN else 0
			res['FP'] += 1 if FP else 0
			res['FN'] += 1 if FN else 0


		r = really_is_negative/float(really_is_positive)


		Results[target_gold] = {
			'res': res,
			'ratio': r
		}


	for target_gold in emotions:

		res = Results[target_gold]['res']
		r = Results[target_gold]['ratio']

		query = {}
		query.update(cfg)
		query['emotion'] = target_gold



		A = accuracy(res, ratio=r)
		P = precision(res, ratio=r)
		R = recall(res, ratio=r)


		upadte = { 
			'ratio': r, 
			'res': res,
			'accuracy': A,
			'precision': P,
			'recall': R,
			'f1': 2*P*R/float(P+R) if P+R > 0 else 0.0
		}
		
		db['results'].update( query, { '$set': upadte }, upsert=True )




if __name__ == '__main__':

	# gen_test(cfg)

	res = evals(cfg)



	

