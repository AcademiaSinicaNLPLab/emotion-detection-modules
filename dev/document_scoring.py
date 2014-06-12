# -*- coding: utf-8 -*-
import config, color
import pymongo,sys
from itertools import product
from collections import defaultdict, Counter

db = pymongo.Connection(config.mongo_addr)[config.db_name]

# a local cache for event_scoring to reduce mongo access times
cache = {}
search_list = False

def check_indexes(target, indexes, auto=True):
	# |-- idx_name --| |---------   idx_value  --------------|
	# [(u'_id_',       {u'key': [(u'_id', 1)], u'v': 1}),
	#  (u'pattern_1',  {u'key': [(u'pattern', 1.0)], u'v': 1})]
	existed = set()
	for (idx_name, idx_value) in target.index_information().items():
		for idx_str, idx_n in idx_value['key']:
			idx_n = int(idx_n)
			if idx_str in indexes: existed.add( idx_str )

	## index's not fully-functional
	if len(existed) < len(set(indexes)):
		to_be_created = [x for x in indexes if x not in existed]
		# index_to_be_created = color.render( ', '.join([x for x in to_be_created]), 'green')
		to_be_created_str = color.render(', '.join(to_be_created), 'g')

		if auto:
			print >> sys.stderr, '(warning) missing necessary index(es)', to_be_created_str

			for idx_str in to_be_created:
				print >> sys.stderr, 'automatically creating index', idx_str, '...',
				sys.stderr.flush()
				## create index in target collection
				target.create_index(idx_str)
				print >> sys.stderr, 'done'

		else:
			print >> sys.stderr, '(error) please manully create index(es)',to_be_created_str,'first before calculating the score'
			return False

	return True

## generate/fetch the patterns search list
def get_search_list():

	if config.min_count < 1: # 0, -1
		return False
	# check if the list existed
	# {
	# 	'limit': 1, # occur more than 1. i.e., drop all pattern with only 1 occurrence
	# 	'pats': [p1, ... pn]
	# }
	print >> sys.stderr, 'loading search pattern list...',
	sys.stderr.flush()

	res = co_patsearch.find_one({'limit':config.min_count})
	if res:
		# use current list
		_search_list = res['pats']
	else:
		# generate the list
		print >> sys.stderr, 'failed'
		print >> sys.stderr, 'cannot find limit search pattern list, re-generating...',
		sys.stderr.flush()

		C = Counter()
		for x in db['lexicon'].find(): C[x['pattern']] += x['count']
		mdoc = { 'limit': limit, 'pats': [] }
		for pat,count in sorted(C.items(), key=lambda x:x[1], reverse=True):
			if count <= limit: break
			mdoc['pats'].append(pat)

		# store in mongo
		db['pats_trim'].insert(mdoc)

		_search_list = mdoc['pats']

	print >> sys.stderr, 'done'

	return _search_list


def significance_factor(pat):
	sf = config.sig_function_type
	if sf == 0: return 1
	elif sf == 1: return pat['pattern_length']
	elif sf == 2: return float(1)/pat['sent_length']
	elif sf == 3: return pat['pattern_length'] * ( float(1)/pat['sent_length'] )
	else: return False

def event_scoring(pat):

	query = { 'pattern': pat['pattern'].lower() }
	projector = { '_id': 0, 'scores':1 }

	global cache

	key = pat['pattern']

	if key not in cache:
		res = co_patscore.find_one( query, projector )

		if not res:
			cache[key] = {}
		else:
			cache[key] = res['scores']
	
	pat_scores = cache[key]
	
	return dict([(emotion, pat['weight'] * significance_factor(pat) * pat_scores[emotion]) for emotion in pat_scores])


## udocID=1000, emotion='happy'
## input: udocID, emotions to be tested, cfg for fetching pat scores
## output: a dictionary of emotion, doc_score
# {
# 	'happy': 0.2,
# 	'sad': 0.6,
# }
# def document_scoring(udocID, limited_search_list=False):
def document_scoring(udocID):
	# find all pats in the document <udocID>
	pats = list( co_pats.find( {'udocID': udocID} ) )

	global search_list

	if config.verbose:
		print >> sys.stderr, '\t%s (%d pats)\t' % (  color.render('#' + str(udocID), 'y'), len(pats))

	D = defaultdict(list)
	
	# calculate the event score in each pattern
	for pat in pats:

		# ignore patterns with occurrence less than x
		# use -l x or --limit x to specify
		if search_list:
			if pat['pattern'] not in search_list:
				continue

		EventScores = event_scoring(pat)
		for emotion in EventScores:
			D[emotion].append( EventScores[emotion] )

	scores = dict([(e, sum(D[e])/float(len(D[e])) ) for e in D])

	return scores

def update_all_document_scores():

	global search_list

	search_list = get_search_list()


	emotions = [ x['emotion'] for x in co_emotions.find( { 'label': 'LJ40K' } ) ]

	## drop docscore collection if overwrite is enabled
	if config.overwrite:
		print >> sys.stderr, 'drop collection', config.co_docscore_name
		co_docscore.drop()


	for (ie, gold_emotion) in enumerate(emotions):

		## get all document with emotions <gold_emotion> and ldocID is great than 800
		docs = list( co_docs.find( { 'emotion': gold_emotion, 'ldocID': {'$gte': 800}} ) )

		if config.verbose:
			print >> sys.stderr, '%d > %s ( %d docs )' % ( ie, color.render(gold_emotion, 'g'), len(docs) )

		else:
			print >> sys.stderr, '%d > %s' % ( ie, color.render(gold_emotion, 'g') )

		for doc in docs:

			# score a document in 40 diff emotions
			scores = document_scoring(doc['udocID'])

			mdoc = { 
				'udocID': doc['udocID'], 
				'gold_emotion': gold_emotion, 
				'scores': scores
			}
			co_docscore.insert( mdoc )

if __name__ == '__main__':
	  
	import getopt

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hp:d:g:s:l:vo',['help','ps_function=', 'ds_function=', 'sig_function=', 'smoothing=', 'limit=', 'verbose', 'overwrite'])
	except getopt.GetoptError:
		config.help(config.ds_name, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.ds_name)
		elif opt in ('-p','--ps_function'): config.ps_function_type = int(arg.strip())
		elif opt in ('-d','--ds_function'): config.ds_function_type = int(arg.strip())
		elif opt in ('-g','--sig_function'): config.sig_function_type = int(arg.strip())
		elif opt in ('-s','--smoothing'): config.smoothing_type = int(arg.strip())
		elif opt in ('-l','--limit'): config.min_count = int(arg.strip())
		elif opt in ('-v','--verbose'): config.verbose = True
		elif opt in ('-o','--overwrite'): config.overwrite = True

	## select mongo collections
	co_emotions = db[config.co_emotions_name]
	co_docs = db[config.co_docs_name]
	co_pats = db[config.co_pats_name]
	co_lexicon = db[config.co_lexicon_name]
	co_patsearch = db[config.co_patsearch_name]

	# check if fetch source existed
	config.co_patscore_name = '_'.join([config.co_patscore_prefix] + config.getOpts(fields=config.opt_fields[config.ps_name], full=False))
	co_patscore_existed = config.co_patscore_name in db.collection_names()
	if not co_patscore_existed:
		print >> sys.stderr, '(error) source collection', color.render(config.co_patscore_name, 'yellow'),'is not existed'
		print >> sys.stderr, '\tcheck the fetch target and run again!!'
		exit(-1)

	
	# check if the destination collection existed
	config.co_docscore_name = '_'.join([config.co_docscore_prefix] + config.getOpts(fields=config.opt_fields[config.ds_name], full=False))
	co_docscore_existed = config.co_docscore_name in db.collection_names()
	if co_docscore_existed and not config.overwrite:
		## (warning) destination's already existed
		print >> sys.stderr, '(warning) destination collection', color.render(config.co_docscore_name, 'red'),'is already existed'
		print >> sys.stderr, '\t  use -o or --overwrite to force update'
		exit(-1)


	## use mongo collection
	co_patscore = db[ config.co_patscore_name ]
	co_docscore = db[ config.co_docscore_name ]

	# check if the index(es) are fully-functional
	good_index = check_indexes(target=co_patscore, indexes=['pattern'], auto=False)
	if not good_index:
		exit(-1)

	## confirm message
	confirm_msg = [
		(config.ps_function_name, config.ps_function_type),
		(config.ds_function_name, config.ds_function_type),
		(config.sig_function_name, config.sig_function_type),
		(config.smoothing_name, config.smoothing_type),
		(config.limit_name, config.min_count),
		('fetch collection', config.co_patscore_name, '(existed)' if co_patscore_existed else '(none)'),
		('insert collection', config.co_docscore_name, '(existed)' if co_docscore_existed else '(none)'),
		('verbose', config.verbose),
		('overwrite', config.overwrite, { True: color.render('!Note: This will drop the collection [ '+config.co_docscore_name+' ]' if co_docscore_existed else '', 'red'), False: '' } )
	]

	config.print_confirm(confirm_msg, bar=40, halt=True)
	
	## run
	import time
	s = time.time()
	update_all_document_scores()
	print 'Time total:',time.time() - s,'sec'

				
