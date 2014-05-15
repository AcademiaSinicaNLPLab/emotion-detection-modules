import config
import sys, pymongo, color
from collections import defaultdict, Counter

db = pymongo.Connection(config.mongo_addr)[config.db_name]

keyword_list = []

## input: udocID
## output: a dictionary of (word: occurrence)
def get_keyword_feature(udocID):

	keywordFeature = Counter()

	## find all words in the document <udocID>
	words = []
	sents = list( co_sents.find( {'udocID': udocID} ) )
	for sent in sents:
		words.extend( sent['sent'].split(' ') )

	if config.verbose:
		print >> sys.stderr, '\t%s (%d words)\t' % (  color.render('#' + str(udocID), 'y'), len(words))

	for word in words:
		# if config.lemma: 
			# word = lemmatize(word)
		if word in keyword_list:
			keywordFeature[ word ] += 1

	return keywordFeature

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
				"feature": get_keyword_feature(udocID=doc['udocID']).items(),
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

	add_opts = [
		('-k', ['-k: keyword set in WordNetAffect',
				'                 0: basic',
				'                 1: extend']),
		('--lemma', ['--lemma: use word lemma (not implemented yet)'])
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hk:v',['help', 'keyword_type=', 'lemma', 'verbose'])
	except getopt.GetoptError:
		config.help(config.kf_name, addon=add_opts, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.kf_name, addon=add_opts)
		elif opt in ('-k','--keyword_type'): 
			if int(arg.strip()) == 0: config.keyword_type = 'basic'
			elif int(arg.strip()) == 1: config.keyword_type = 'extend'
		elif opt in ('--lemma'): config.lemma = True
		elif opt in ('-v','--verbose'): config.verbose = True

	## insert metadata
	setting = { 
		"feature_name": "keyword", 
		"keyword_type": config.keyword_type,
		"lemma": config.lemma 
	}

	## print confirm message
	config.print_confirm(setting.items(), bar=40, halt=True)
	
	## insert metadata
	setting_id = str(co_setting.insert( setting ))

	## create keyword_list
	keyword_list = [ mdoc['word'] for mdoc in list( co_keywords.find( {'type': config.keyword_type} ) ) ]

	## run
	import time
	s = time.time()	
	create_keyword_features(setting_id)
	print 'Time total:',time.time() - s,'sec'

