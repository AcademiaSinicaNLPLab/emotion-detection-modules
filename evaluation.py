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

if __name__ == '__main__':
	gen_test(cfg)




