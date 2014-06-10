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
corpus_root = False

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
def process_parsed_files(corpus_root, docIDs, category, sections):

	usentID = 0
	## identify sections: words,tree,deps
	sections = sections.split(',')
	section_idx = {x:sections.index(x) for x in sections}

	for mdoc in docIDs:

		fn = mdoc['fn']
		udocID = mdoc['udocID']
		ldocID = mdoc['ldocID']
		categorize_target = mdoc[category]
		
		logging.info( 'processing document %s:%s, udocID:%s, ldocID:%s' % (category,categorize_target, udocID, ldocID) )
		# print 'processing document', category+':', categorize_target, 'udocID:', udocID, 'ldocID:',ldocID
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

def load_NTCIR_docs(corpus_root, category, ext='txt'):
	udocIDs, ldocIDs, docIDs = {}, Counter(), []
	# fn:
	# T=N01.F=1_edn_xxx_20031204_2244111.S=0003.P=POS.txt
	for fn in os.listdir(corpus_root):
		if not fn.endswith('.'+ext): continue

		### --------- modify following code to read meta data from filename --------- ###

		# meta: { T: N01, F: ..., S: 0003 }
		meta = dict([x.split('=') for x in fn.split('.') if '=' in x])
		categorize_target = meta['P'] ## polarity


		## get udocID and ldocID
		ldocID = ldocIDs[categorize_target] # current file count under __ polarity
		udocID = len(udocIDs) # current total file count
		ldocIDs[categorize_target] += 1
		udocIDs[fn] = True

		doc_meta = {

			## required meta data
			'ldocID': ldocID,
			'udocID': udocID,
			'fn': fn,

			## category: 
			## e.g., `emotion`, `polarity` or `topic`
			## change setting in config.py
			category: categorize_target,

			## additional meta data
			'filename': meta['F'], 
			'topic': meta['T'], 
			'ith-sent': meta['S']
		}
		### -------------------------------- (end) --------------------------------- ###

		docIDs.append( doc_meta )
		co_docs.insert(doc_meta)

	return docIDs

def load_LJ40K_docs():
	pass

# > db.docs.findOne()
# {
	# 	"_id" : ObjectId("53214e23d4388c4792206528"),
	# 	"emotion" : "crazy",
	# 	"ldocID" : 0,
	# 	"udocID" : 19000
# }

# > db.sents.findOne()
# {
	# 	"_id" : ObjectId("531944ac3681dfca09875205"),
	# 	"emotion" : "accomplished",
	# 	"sent_length" : 10,
	# 	"udocID" : 0,
	# 	"sent_pos" : "I/PRP got/VBD new/JJ hair/NN :/: O/RB omfg/VBG I/PRP love/VBP it/PRP",
	# 	"usentID" : 0,
	# 	"sent" : "I got new hair : O omfg I love it"
# }

# > db.deps.findOne()
# {
	# "_id" : ObjectId("531944ac3681dfca098751fc"),
	# "emotion" : "accomplished",
	# "sent_length" : 10,
	# "udocID" : 0,
	# "xIdx" : 2,
	# "xPos" : "VBD",
	# "yPos" : "PRP",
	# "usentID" : 0,
	# "rel" : "nsubj",
	# "y" : "I",
	# "x" : "got",
	# "yIdx" : 1
# }

if __name__ == '__main__':

	import getopt
	add_opts = [
		('--path', ['-p or --path: specify the input corpus path']),
		('--database', ['-d or --database: specify the destination database name']),
	]
	try:
		opts, args = getopt.getopt(sys.argv[1:],'hp:d:ov',['help','path=', 'database=', 'overwrite','verbose'])
	except getopt.GetoptError:
		config.help('extract_dependency', addon=add_opts, exit=2)

	### read options
	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('extract_dependency', addon=add_opts)
		elif opt in ('-p','--path'): corpus_root = arg.strip()
		elif opt in ('-d','--database'): config.db_name = arg.strip()
		elif opt in ('-o','--overwrite'): config.overwrite = True
		elif opt in ('-v','--verbose'): config.verbose = True

	loglevel = logging.DEBUG if config.verbose else logging.INFO
	logging.basicConfig(format='[%(levelname)s] %(message)s', level=loglevel)

	if not corpus_root:
		logging.error('specify the input corpus path: e.g., python extract_dependency.py -p /corpus/NTCIR/')
		exit(-1)


	## use db
	db = mc[config.db_name]

	## db.<collection_name>
	co_docs = db[config.co_docs_name]
	co_sents = db[config.co_sents_name]
	co_deps = db[config.co_deps_name]

	### check whether destination collection is empty or not
	dest_cos = [co_docs, co_sents, co_deps]
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

	docIDs = load_NTCIR_docs(corpus_root, category=config.category, ext='txt')

	process_parsed_files(corpus_root, docIDs, category=config.category, sections='words,deps')

	logging.info('create index')
	co_docs.create_index('udocID')
	co_sents.create_index('udocID')
	co_deps.create_index('udocID')

