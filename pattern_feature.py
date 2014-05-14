import config
import sys, pymongo, color
from collections import defaultdict, Counter

db = pymongo.Connection(config.mongo_addr)[config.db_name]

cache = {}

## input: pattern
## output: number of occurrence
def get_count(pattern):

	global cache

	if pattern not in cache:
		
		query = { 'pattern': pattern.lower() }
		projector = { '_id': 0, 'count':1 }
		res = co_nestedLexicon.find_one(query, projector)
		
		if not res:
			cache[pattern] = 0
		else:
			cache[pattern] = sum( [ res['count'][e] for e in res['count'] ] )

	return cache[pattern]

## input: udocID
## output: a dictionary of (pattern: occurrence)
def get_pattern_feature(udocID):

	patFeature = {}

	## find all pats in the document <udocID>
	pats = list( co_pats.find( {'udocID': udocID} ) )

	if config.verbose:
		print >> sys.stderr, '\t%s (%d pats)\t' % (  color.render('#' + str(udocID), 'y'), len(pats))

	for pat in pats:

		count = get_occurrence(pat['pattern'])

		if count >= config.min_count:
			patFeature[pat['pattern']] = count

	return patFeature

def create_pattern_features(setting_id):

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
			# co_feature.insert(mdoc)

	# co_feature.create_index("setting")


if __name__ == '__main__':

	## select mongo collections
	co_emotions = db[config.co_emotions_name]
	co_docs = db[config.co_docs_name]
	co_pats = db[config.co_pats_name]
	co_nestedLexicon = db['lexicon.nested']

	## target mongo collections
	co_setting = db['features.settings']
	co_feature = db['features.pattern']

	## input arguments
	import getopt

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hl:v',['help', 'min_count=', 'verbose'])
	except getopt.GetoptError:
		config.help(config.pf_name, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.pf_name)
		elif opt in ('-l','--limit'): config.min_count = int(arg.strip())
		elif opt in ('-v','--verbose'): config.verbose = True

	## insert metadata
	setting = { 
		"feature_name": "pattern", 
		"min_count": config.min_count 
	}

	## print confirm message
	config.print_confirm(setting.items(), bar=40, halt=True)
	
	## insert metadata
	setting_id = str(co_setting.insert( setting ))

	## run
	import time
	s = time.time()	
	create_pattern_features(setting_id)
	print 'Time total:',time.time() - s,'sec'

