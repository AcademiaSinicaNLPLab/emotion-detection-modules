import pymongo, sys
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


def evals(cfg):

	Positive, Negative = True, False

	insts = fetch_insts(cfg)

	emotinos = sorted(list(set([ x['gold_emotion'] for x in insts ])))

	# target: happy
	# really is happy
	# 	classify as happy	
	#	classify as ~happy	
	# really is ~happy		
	# 	classify as happy	
	# 	classify as ~happy	

	results = {}
	for target_gold in emotinos:

		for inst in insts:

			really_is = Positive if target_gold == inst['gold_emotion'] else Negative
			classified_as = Positive if inst['predict'][target_gold] == 1 else Negative

			TP = classified_as == Positive and really_is == Positive
			TN = classified_as == Negative and really_is == Negative
			FP = classified_as == Positive and really_is == Negative
			FN = classified_as == Negative and really_is == Positive

			results['TP'] += 1 if TP else 0
			results['TN'] += 1 if TN else 0
			results['FP'] += 1 if FP else 0
			results['FN'] += 1 if FN else 0


	return results

if __name__ == '__main__':

	# gen_test(cfg)

	
	evals(cfg)
