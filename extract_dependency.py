# -*- coding: utf-8 -*-

## 
## python extract_dependency.py -p /corpus/NTCIR/formalrun_released_TC -d NTCIR
import config
import logging, json
import pymongo, os, sys

from pprint import pprint
from collections import Counter

from util import read_words, read_deps

mc = pymongo.Connection(config.mongo_addr)

db_name = None
co_docs = None
co_sents = None
co_deps = None

# corpus_root = '/Users/Maxis/corpus/NTCIR/'
# corpus_root = False

## sections:
# default output of Stanford Parser
	# {
	# 	'words': 0,
	# 	'tree':  1,
	# 	'deps':  2
	# }
# if `tree` didn't output: words and followed by deps
	# {
	# 	'words': 0,
	# 	'deps':  1
	# }
def process_parsed_files(corpus_root, category, sections):

	usentID = 0
	## identify sections: words,tree,deps
	sections = sections.split(',')
	section_idx = {x:sections.index(x) for x in sections}

	for mdoc in co_docs.find():

		fn = mdoc['fn']
		udocID = mdoc['udocID']
		ldocID = mdoc['ldocID']
		categorize_target = mdoc[category]
		
		logging.info( 'processing document %s:%s, udocID:%s, ldocID:%s' % (category,categorize_target, udocID, ldocID) )

		## load parsed text
		fpath = os.path.join(corpus_root, fn)
		doc = open(fpath).read().strip().split('\n\n')

		for i in range(len(doc)/len(sections)): 
			block = doc[i*len(sections):(i+1)*len(sections)]
			
			word_pos_list = read_words(block[section_idx['words']]) # even line number, words and POS tags
			## tree = read_tree(block[section_idx['tree']])
			deps = read_deps(block[section_idx['deps']]) # odd line number,  dependencies

			### insert sent to db.sents
			msent = {
				category: categorize_target,
				'sent_length': len(word_pos_list),
				'sent_pos': block[0],
				'usentID': usentID,
				'sent': ' '.join(map(lambda x:x[0], word_pos_list)),
				'udocID': udocID,
				'ldocID': ldocID
			}
			co_sents.insert(msent)

			### process deps
			for rel, left, right in deps:
				mdep = {
					category: categorize_target,
					'sent_length': len(word_pos_list),
					'udocID': udocID,
					'ldocID': ldocID,
					'usentID': usentID,
					'rel': rel
				}
				mdep['x'] = left[0]
				mdep['y'] = right[0]

				mdep['xIdx'] = left[1]
				mdep['yIdx'] = right[1]

				x_list_idx = left[1]-1
				y_list_idx = right[1]-1
				mdep['xPos'] = word_pos_list[x_list_idx][1]
				mdep['yPos'] = word_pos_list[y_list_idx][1]

				### insert to db.deps
				co_deps.insert(mdep)

			usentID += 1

if __name__ == '__main__':

	program = __file__.split('.py')[0]

	import getopt
	add_opts = [
		('--path', ['-p or --path: specify the input corpus path']),
		('--database', ['-d or --database: specify the destination database name']),
	]
	try:
		opts, args = getopt.getopt(sys.argv[1:],'hp:d:ov',['help','path=', 'database=', 'overwrite','verbose'])
	except getopt.GetoptError:
		config.help(program, addon=add_opts, exit=2)

	### read options
	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(program, addon=add_opts)
		elif opt in ('-p','--path'): config.corpus_root = arg.strip()
		elif opt in ('-d','--database'): config.db_name = arg.strip()
		elif opt in ('-o','--overwrite'): config.overwrite = True
		elif opt in ('-v','--verbose'): config.verbose = True

	loglevel = logging.DEBUG if config.verbose else logging.INFO
	logging.basicConfig(format='[%(levelname)s] %(message)s', level=loglevel)

	if not config.corpus_root:
		logging.error('specify the input corpus path: e.g., python '+program+'.py -p /corpus/NTCIR/')
		exit(-1)


	## use db
	db = mc[config.db_name]

	## src collection
	co_docs = db[config.co_docs_name]
	## dest collections
	co_sents = db[config.co_sents_name]
	co_deps = db[config.co_deps_name]

	### check whether destination collection is empty or not
	dest_cos = [co_sents, co_deps]
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

	process_parsed_files(corpus_root=config.corpus_root, category=config.category, sections='words,deps')

	logging.info('create index')
	co_sents.create_index('udocID')
	co_deps.create_index('udocID')

