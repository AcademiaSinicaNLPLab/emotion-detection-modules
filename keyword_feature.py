import sys, pymongo, color
from collections import defaultdict, Counter

db = pymongo.Connection(config.mongo_addr)[config.db_name]

## input: udocID
## output: a dictionary of (word: occurrence)
def get_keyword_feature(udocID):

	keywordFeature = Counter()

	## find all pats in the document <udocID>
	pats = list( co_pats.find( {'udocID': udocID} ) )

	if config.verbose:
		print >> sys.stderr, '\t%s (%d pats)\t' % (  color.render('#' + str(udocID), 'y'), len(pats))

	for pat in pats:

		if get_count(pat['pattern']) >= config.min_count:
			patFeature[ pat['pattern'] ] += 1

	return patFeature

def create_keyword_features(setting_id):

	## list of emotions
	emotions = [ x['emotion'] for x in co_emotions.find( { 'label': 'LJ40K' } ) ]

	for (ie, gold_emotion) in enumerate(emotions):

		## get all document with emotions <gold_emotion> (ldocID: 0-799 for training, 800-999 for testing)
		docs = list( co_docs.find( { 'emotion': gold_emotion } ) )

		if config.verbose:
			print >> sys.stderr, '%d > %s ( %d docs )' % ( ie, color.render(gold_emotion, 'g'), len(docs) )

		for doc in docs:
			mdoc = {
				"emotion": gold_emotion,
				"udocID": doc['udocID'],
				"feature": get_pattern_feature(udocID=doc['udocID']).items(),
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
	co_keywords = db['resource.WordNetAffect']

	## target mongo collections
	co_setting = db['features.settings']
	co_feature = db['features.keyword']

	## input arguments
	import getopt
	try:
		opts, args = getopt.getopt(sys.argv[1:],'hk:av',['help', 'keyword_type=', 'lemma', 'verbose'])
	except getopt.GetoptError:
		config.help(config.kf_name, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.pf_name)
		elif opt in ('-k','--keyword_type'): 
			if int(arg.strip()) == 0: config.keyword_type = 'basic'
			elif int(arg.strip()) == 1: config.keyword_type = 'extend'
		elif opt in ('-a', '--lemma'): config.lemma = True
		elif opt in ('-v','--verbose'): config.verbose = True

	## insert metadata
	setting = { 
		"feature_name": "keyword", 
		"keyword_type": config.keyword_type 
		"lemma": config.lemma 
	}

	## print confirm message
	config.print_confirm(setting.items(), bar=40, halt=True)
	
	## insert metadata
	setting_id = str(co_setting.insert( setting ))

	## run
	import time
	s = time.time()	
	create_keyword_features(setting_id)
	print 'Time total:',time.time() - s,'sec'

