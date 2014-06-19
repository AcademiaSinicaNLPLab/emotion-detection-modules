# -*- coding: utf-8 -*-

import sys
sys.path.append('pymodules')
import config
import logging
import json
import pymongo
import os
import color
import util
from collections import Counter, defaultdict

db = pymongo.Connection(config.mongo_addr)[config.db_name]

co_docs = None
co_pats = None
co_lexicon = None
co_cate = None
categories = []

# calculate occurrences of patterns
def count_patterns(categories, condition={}):
	patCount = defaultdict(Counter)
	for c in categories:
		# patCount[c] = Counter()
		query = { config.category: c }
		query.update(condition)
		# get udocIDs
		for mdoc in co_docs.find(query):
			udocID = mdoc['udocID']
			## get patterns
			for mpat in co_pats.find( {'udocID': udocID} ):
				pat = mpat['pattern'].lower()
				patCount[pat][c] += 1
	return patCount	

# build lexicon storing pattern occurrence
def build_lexicon(patCount, categories):
	# for c in categories:
	for p in patCount:
		logging.debug('insert pattern %s into %s' % (color.render(p,'g'), color.render(co_lexicon.full_name,'lightyellow') ))

		mdoc = {
			'pattern': p,
			'count': dict(patCount[p]),
			'total_count': sum(patCount[p].values())
		}

		co_lexicon.insert( mdoc )

if __name__ == '__main__':


	program = __file__.split('.py')[0]

	import getopt
	try:
		opts, args = getopt.getopt(sys.argv[1:],'hov',['help','overwrite','verbose'])
	except getopt.GetoptError:
		config.help(program, exit=2)

	### read options
	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(program)
		elif opt in ('-o','--overwrite'): config.overwrite = True
		elif opt in ('-v','--verbose'): config.verbose = True

	loglevel = logging.DEBUG if config.verbose else logging.INFO
	logging.basicConfig(format='[%(levelname)s] %(message)s', level=loglevel)


	## src
	co_docs = db[config.co_docs_name]
	co_pats = db[config.co_pats_name]
	co_cate = db[config.co_category_name]
	## dest
	co_lexicon = db[config.co_lexicon_name]

	### check whether destination collection is empty or not
	dest_cos = [co_lexicon]
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

	index_check_list = [(co_docs, config.category), (co_pats, 'udocID')]
	util.check_indexes(check_list=index_check_list, verbose=config.verbose)
	
	logging.info('fetch categories from %s' % (color.render(co_cate.full_name, 'ly')))
	categories = sorted([x[config.category] for x in co_cate.find({'label':config.category})])

	logging.info('count patterns')
	# patCount = count_patterns(categories, condition={'ldocID': {'$lt': 800}} )
	patCount = count_patterns(categories)

	logging.info('build pattern lexicon at %s' % (color.render(co_lexicon.full_name, 'ly')))
	build_lexicon(patCount, categories)
