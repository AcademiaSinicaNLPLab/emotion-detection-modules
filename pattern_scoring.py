# -*- coding: utf-8 -*-

import sys
sys.path.append('pymodules')

import config
import json
import pymongo
import color
import os
import pickle
from collections import defaultdict, Counter
import logging
import util, feature


db = None

# global cache for pattern
cache = {}

# global cache for mongo.LJ40K.docs
mongo_docs = {}

# global cache for mongo.LJ40K.lexicon.pattern_total_count
PatTC = {}

# remove_type = '0'
### remove self count or not
remove = False

# percentage = 1.0
## input: pattern
## output: a dictionary of (emotion, occurrence)
def get_patcount(pattern):

	global cache

	if pattern not in cache:

		query = { 'pattern': pattern.lower() }
		projector = { '_id': 0, 'count':1 }
		res = co_lexicon.find_one(query, projector)

		if not res:
			cache[pattern] = {}
		else:
			cache[pattern] = res['count']

	return cache[pattern]

## input: dictionary of (emotion, count)
## output: dictionary of (emotion, count)
## condition: for LJ40K, distinguish training/testing using document ID
def remove_self_count(udocID, pattern, count_dict, category, condition=False):

	global mongo_docs
	mdoc = mongo_docs[udocID] # use pre-loaded

	new_count = dict(count_dict)

	if new_count: 

		## ldocID: 0-799
		# not condition: considering all as training
		# condition and mdoc['ldocID'] < 800: ## for LJ40K, identify training/testing
		if not condition or condition and mdoc['ldocID'] < 800:
			new_count[mdoc[category]] = new_count[mdoc[category]] - PatTC[udocID][pattern.lower()]

		
		if new_count[mdoc[category]] == 0 :
			del new_count[mdoc[category]]

	return new_count


## category: emotion or polarity
def calculate_pattern_scores_remove_self(category):

	## list of category
	categories = [ x[category] for x in co_cate.find( { 'label': category } ) ]
	logging.debug('found %d categories' % len(categories))

	for (ie, gold_category) in enumerate(categories):

		## get all document with emotions <gold_emotion> (ldocID: 0-799 for training, 800-999 for testing)
		docs = list( co_docs.find( { category: gold_category } ) )
		logging.info('%d/%d %s: %d docs' % ( ie, len(categories), color.render(gold_category, 'lg'), len(docs) ))

		for ith_doc, doc in enumerate(docs):
			udocID = doc['udocID']
			## find all pats in the document <udocID>
			pats = list( co_pats.find( {'udocID': udocID} ) )
			logging.info('%s --> %s (%d pats) [%d/%d]\t%.1f%%' % ( color.render(gold_category, 'lg'), color.render(str(udocID),'ly'), len(pats), ith_doc+1, len(docs), (ith_doc+1)/float(len(docs))*100 )  )

			for pat in pats:

				pattern_score = {}
				pattern = pat['pattern']

				count = get_patcount(pattern)
				logging.debug('get count of "%s (%d)"' % (color.render(pattern,'g'), len(count) ))

				if count:

					count = remove_self_count(udocID, pattern, count, category=config.category)
					logging.debug('remove self count of "%s" in udocID: %s' % (color.render(pattern,'g'), color.render(str(udocID),'lc')) )

					pattern_score = feature.pattern_scoring_function(count)

				mdoc = {
					'score':pattern_score,
					'udocID':udocID,
					'pattern':pattern
				}
				co_patscore.insert(mdoc)

	co_patscore.create_index("pattern")

def calculate_pattern_scores():
	total = co_lexicon.count()

	for i,mdoc in enumerate(co_lexicon.find()):
		
		pattern = mdoc['pattern']

		percent = (i+1)/float(total)*100

		if not config.verbose:
			sys.stderr.write('[%s> %.2f%%%s]\r' % ('='*(int(percent)+1), percent, ' '*(100-int(percent) ) ) )
			sys.stderr.flush()
		else:
			logging.debug('[%.2f%%] (%d/%d) process %s' % (percent, i+1, total, color.render(pattern, 'ly') ))

		count = get_patcount(pattern)
		logging.debug('get count of "%s (%d)"' % (color.render(pattern,'g'), len(count) ))

		
		pattern_score = {} if not count else feature.pattern_scoring_function(count)

		mdoc = {
			'score':pattern_score,
			'pattern':pattern
		}
		logging.debug('insert mdoc in %s' % (color.render(co_patscore.full_name, 'ly') ) )
		co_patscore.insert(mdoc)

	sys.stderr.write('\n')
	logging.info('create index on %s in %s' % (color.render('pattern', 'g'), color.render(co_patscore.full_name, 'ly') ) )
	co_patscore.create_index("pattern")

if __name__ == '__main__':

	program = __file__.split('.py')[0]

	## input arguments
	import getopt
	
	add_opts = [
		('-n', ['-n or --minCount: filter out patterns with minimum count',
			    '                  k: minimum count']),
		('--debug', ['--debug: run in debug mode']),
		('--remove', ['--remove: remove self count'])
	]

	try:
		# opts, args = getopt.getopt(sys.argv[1:],'hf:n:c:vr:',['help', 'featureValueType=', 'minCount=', 'cut=', 'verbose', 'debug'])
		opts, args = getopt.getopt(sys.argv[1:],'hn:vr:o',['help', 'minCount=', 'verbose', 'debug', 'overwrite', 'remove'])
	except getopt.GetoptError:
		config.help(program, addon=add_opts, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(program, addon=add_opts)
		# elif opt in ('-f', '--featureValueType'): config.featureValueType = arg.strip()
		elif opt in ('-n', '--minCount'): config.minCount = int( arg.strip() )
		elif opt in ('-c', '--cut'): config.cutoffPercentage = int( arg.strip() )
		elif opt in ('-v','--verbose'): config.verbose = True
		elif opt in ('-o','--overwrite'): config.overwrite = True
		elif opt in ('--remove'): remove = True
		elif opt in ('--debug'): config.debug = True

	loglevel = logging.DEBUG if config.verbose else logging.INFO
	logging.basicConfig(format='[%(levelname)s] %(message)s', level=loglevel)

	logging.debug('connecting mongodb at %s/%s' % (config.mongo_addr, config.db_name))
	db = pymongo.Connection(config.mongo_addr)[config.db_name]

	## src
	if remove:
		co_docs = db[config.co_docs_name]
		co_pats = db[config.co_pats_name]
		co_cate = db[config.co_category_name] ## db.polarity or db.emotions
	co_lexicon = db[config.co_lexicon_name]
	
	## dest
	modifier = 'remove' if remove else 'normal'
	co_patscore_name = '.'.join([config.co_patscore_prefix, modifier])
	co_patscore = db[ co_patscore_name ]

	if remove:
		index_check_list = [(co_docs, config.category), (co_pats, 'udocID'), (co_lexicon, 'pattern')]
	else:
		index_check_list = [(co_lexicon, 'pattern')]
	util.check_indexes(check_list=index_check_list, verbose=config.verbose)

	## check whether destination collection is empty or not
	dest_cos = [co_patscore]
	dest_cos_status = {co.name : co.count() for co in dest_cos}
	logging.info('current collection status: ' + json.dumps(dest_cos_status))
	if sum(dest_cos_status.values()) > 0 and not config.overwrite:
		logging.warn('use --overwrite or -o to drop current data and insert new one')
		exit(-1)
	elif sum(dest_cos_status.values()) > 0 and config.overwrite:
		# logging.warn('overwrite mode, will drop all data in ' + )
		print >> sys.stderr, 'drop all data in',', '.join(dest_cos_status.keys()), '(Y/n)? ', 
		if raw_input().lower().startswith('n'): exit(-1)
		else:
			for co in dest_cos: co.drop()

	if remove:
		import lexicon_total_count
		## load mongo doc and total count for remove_self_count()
		logging.info('load_mongo_docs')
		mongo_docs = util.load_mongo_docs(co_docs)

		## load lexicon_total_count to do "remove_self_count"
		logging.info('load lexicon pattern total count')
		lexicon_total_count.target_name = 'pattern'
		PatTC = lexicon_total_count.load()

		logging.info('calculate pattern scores')
		calculate_pattern_scores_remove_self(category=config.category)

	else:
		logging.info('calculate pattern scores')
		calculate_pattern_scores()
