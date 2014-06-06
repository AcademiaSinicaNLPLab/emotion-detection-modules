import pymongo, os, sys, config
from pprint import pprint
from collections import Counter

mc = pymongo.Connection(config.mongo_addr)

db_name = None
co_docs = None
co_sents = None
co_deps = None

# corpus_root = '/Users/Maxis/corpus/NTCIR/'
corpus_root = False

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

## parse raw dependency text
def read_deps(raw_deps, delimiter=None, auto_detect=False, return_type=list):
	deps = []
	if not delimiter or auto_detect:
		delimiter = '\n' if raw_deps.count('\n') > raw_deps.count('), ') else '), '

	for dep in map(lambda x:x.strip(), raw_deps.strip().split(delimiter)):

		if ')' not in dep.split('-')[-1]: # put ")" back
			dep = dep + ')'

		lpb = [i for (i,x) in enumerate(dep) if x == '(']
		rpb = [i for (i,x) in enumerate(dep) if x == ')']
		if not lpb or not rpb: continue

		dl = min(lpb)
		dr = max(rpb)

		rel = dep[:dl]
		body = dep[dl+1:dr]

		parts = body.split(', ')

		# print map(lambda x: ( '-'.join(x.split('-')[:-1]), int( x.split('-')[-1].replace("'",'') ) ), parts)

		left, right = map(lambda x: ( '-'.join(x.split('-')[:-1]), int( x.split('-')[-1].replace("'",'') ) ), parts)

		if return_type == dict:
			deps.append( {'rel':rel, 'ltoken': left[0], 'lidx': left[1], 'rtoken': right[0], 'ridx': right[1]} )
		else:
			deps.append((rel , left, right))

	return deps


def read_words(raw_wordpos, delimiter=' '):
	return [('/'.join(word_pos_str.split('/')[:-1]), word_pos_str.split('/')[-1]) for word_pos_str in raw_wordpos.strip().split(delimiter)]

def process_parsed_files(corpus_root, docIDs):

	usentID = 0
	for mdoc in docIDs:

		fn = mdoc['filename']
		udocID = mdoc['udocID']
		ldocID = mdoc['ldocID']
		topic = mdoc['topic']

		co_docs.insert(mdoc)
		print 'processing document', 'topic:', topic, 'udocID:', udocID, 'ldocID:',ldocID

		fpath = os.path.join(corpus_root, fn)

		doc = open(fpath).read().strip().split('\n\n')
		for i in range(len(doc)/2): 
			block = doc[i*2:(i+1)*2]
			
			word_pos_list = read_words(block[0]) # even line number, words and POS tags
			deps = read_deps(block[1]) # odd line number,  dependencies


			### insert sent to db.sents
			msent = {
				'topic': topic,
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
					'sent_length': len(word_pos_list),
					'topic': topic,
					'udocID': udocID,
					'ldocID': ldocID,
					'usentID': usentID,
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


def load_docs(corpus_root):
	ldocIDs = Counter()
	udocIDs = {}
	docIDs = []
	for fn in os.listdir(corpus_root):
		if not fn.endswith('.txt'): continue
		topic = fn.split(']]')[0].strip()
		# fn = '11]]1_edn_xxx_20030518_1963619-2.txt'
		fpath = os.path.join(corpus_root, fn)
		## get udocID and ldocID
		ldocID = ldocIDs[topic] # current file count under __ topic
		udocID = len(udocIDs) # current total file count
		ldocIDs[topic] += 1
		udocIDs[fn] = True
		docIDs.append( {'filename': fn, 'topic': topic, 'ldocID': ldocID, 'udocID': udocID} )
	return docIDs

if __name__ == '__main__':

	import getopt

	add_opts = [
		('--path', ['-p or --path: specify the input corpus path']),
		('--database', ['-d or --database: specify the destination database name']),
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hp:d:',['help','path=', 'database='])
	except getopt.GetoptError:
		config.help('extract_dependency', addon=add_opts, exit=2)

	## read options
	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('extract_dependency', addon=add_opts)
		elif opt in ('-p','--path'): corpus_root = arg.strip()
		elif opt in ('-d','--database'): config.db_name = arg.strip()

	if not corpus_root:
		print 'specify the input corpus path: e.g., python extract_dependency.py -p /corpus/NTCIR/'
		exit(-1)

	if not corpus_root:
		print 'specify the destination database name: e.g., python extract_dependency.py -d NTCIR'
		exit(-1)

	db = mc[config.db_name]

	co_docs = db['docs']
	co_sents = db['sents']
	co_deps = db['deps']

	docIDs = load_docs(corpus_root)
	process_parsed_files(corpus_root, docIDs)

