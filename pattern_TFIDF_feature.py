import config
import sys, pymongo, color, pickle
from collections import defaultdict, Counter

import tfidf

db = pymongo.Connection(config.mongo_addr)[config.db_name]


def create_keyword_TFIDF_features(setting_id, training_TFIDF, testing_TFIDF):

	## list of emotions
	emotions = [ x['emotion'] for x in co_emotions.find( { 'label': 'LJ40K' } ) ]

	for (ie, gold_emotion) in enumerate(emotions):

		## get all document with emotions <gold_emotion> (ldocID: 0-799 for training, 800-999 for testing)
		docs = list( co_docs.find( { 'emotion': gold_emotion } ) )

		if config.verbose:
			print >> sys.stderr, '%d > %s ( %d docs )' % ( ie, color.render(gold_emotion, 'g'), len(docs) )

		for doc in docs:

			udocID = doc['udocID']
			ldocID = doc['ldocID']

			if ldocID < 800: # training
				if udocID in training_TFIDF:
					feature = dict(training_TFIDF[udocID]).items()
				else:
					feature = []
			else:
				if udocID in testing_TFIDF:
					feature = dict(testing_TFIDF[udocID]).items()
				else:
					feature = []

			mdoc = {
				"emotion": gold_emotion,
				"udocID": udocID,
				"feature": feature,
				"setting": setting_id # looks like "5369fb11d4388c0aa4c5ca4e"
			}
			co_feature.insert(mdoc)

	co_feature.create_index("setting")


if __name__ == '__main__':

	## select mongo collections
	co_emotions = db[config.co_emotions_name]
	co_docs = db[config.co_docs_name]
	co_pats = db[config.co_pats_name]
	co_sents = db[config.co_sents_name]
	# co_keywords = db['resource.WordNetAffect']

	# config.keyword_type = 'extend'
	# config.lemma = True

	## input arguments
	import getopt

	add_opts = [
		# ('-k', ['-k: keyword set in WordNetAffect',
		# 		'                 0: basic',
		# 		'                 1: extend']),
		# ('--lemma', ['--lemma: use word lemma when looking for keywords'])
	]

	if len(sys.argv) < 3:
		print 'usage: python pattern_TFIDF_feature <ty_type> <idf_type> [options]'
		config.help(config.keywordFeat_name, addon=add_opts, exit=2)
		exit(-1)

	tf_type = sys.argv[1].strip()
	idf_type = sys.argv[2].strip()

	TFIDF_type = 'TF'+tf_type+'xIDF'+idf_type

	try:
		opts, args = getopt.getopt(sys.argv[3:],'hk:v',['help', 'verbose', 'debug'])
	except getopt.GetoptError:
		config.help(config.keywordFeat_name, addon=add_opts, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.keywordFeat_name, addon=add_opts)
		# elif opt in ('--lemma'): config.lemma = True
		elif opt in ('-v','--verbose'): config.verbose = True
		elif opt in ('--debug'): config.debug = True

	## target mongo collections
	co_setting = db['features.settings'] if not config.debug else db['debug.features.settings']
	co_feature = db['features.pattern_TFIDF'] if not config.debug else db['debug.features.pattern_TFIDF']

	## insert metadata
	setting = { 
		"feature_name": "pattern_TFIDF",
		"TFIDF_type": TFIDF_type,
		"min_count": 5,
		'min_df': 3
	}

	## print confirm message
	config.print_confirm(setting.items(), bar=40, halt=True)
	
	## insert metadata
	setting_id = str(co_setting.insert( setting ))


	## create keyword_list
	# keyword_list = set([ mdoc['word'] for mdoc in list( co_keywords.find( {'type': config.keyword_type} ) ) ])

	# TF3xIDF2.train.lemma.pkl
	# TF3xIDF2.test.lemma.pkl

	print 'loading '+TFIDF_type+' pickles'
	# ext = '.lemma.pkl' if config.lemma else '.pkl'
	
	# TF3xIDF2.pat.5.train.pkl
	# TF3xIDF2.pat.5.test.pkl
	training_TFIDF = pickle.load(open('cache/'+TFIDF_type+'.pat.5.3.train.pkl'))
	testing_TFIDF  = pickle.load(open('cache/'+TFIDF_type+'.pat.5.3.test.pkl'))

	# u2l  = pickle.load(open('cache/u2l.pkl'))

	print 'organizing TFIDF dict'
	training_TFIDF = tfidf.inverse_key(training_TFIDF)
	testing_TFIDF = tfidf.inverse_key(testing_TFIDF)

	print 'creating features'
	create_keyword_TFIDF_features(setting_id, training_TFIDF, testing_TFIDF) # 538ba2bfd4388c4012348f0f
	# print 'Time total:',time.time() - s,'sec'

