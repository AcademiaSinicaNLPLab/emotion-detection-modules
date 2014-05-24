## read from mongodb.features.xxx
## generate svm feature file

import config, color
import pickle
import pymongo, sys, os, re
from collections import defaultdict
from bson.objectid import ObjectId

#### global
## ------------------------------------------------------- ##

db = pymongo.Connection(config.mongo_addr)[config.db_name]
udocID_eid = {}
co_feature_setting = None
setting_id_str = ''
eids = { emotion : i for i, emotion in enumerate(sorted([d['emotion'] for d in db['emotions'].find({'label': 'LJ40K'})])) }

def parse_src_setting_ids():
	# support delimiters: [, . ; : white_space]
	# case insensitive
	# e.g., "537086fcd4388c7e81676914,537086fcd4388c7e816762139 537086fcd4388c7e81676916"
	parsed = re.findall(r'([0-9a-z]{24})[.,;:\s]?', setting_id_str.lower())
	return False if not parsed else sorted(parsed)

## src_setting_id:  used for mongo fetching
## dest_setting_id: used for train/test naming
def obtain_dest_setting_id(src_setting_ids):

	global co_feature_setting
	# input format error
	if not src_setting_ids or len(src_setting_ids) == 0:
		dest_setting_id = False

	# normal mode
	elif len(src_setting_ids) == 1: 
		dest_setting_id = src_setting_ids[0]

	# fused mode
	else:
		# combine src_setting_id(s) to get dest_setting_id
		sources = ','.join(src_setting_ids)

		mdoc = co_feature_setting.find_one({'sources': sources})
		# new fusion
		if not mdoc:
			# generate fused setting_id
			dest_setting_id = str( co_feature_setting.insert( {'sources': sources, 'feature_name': 'fusion'} ) )

		# already fused, just get fusion id
		else:
			dest_setting_id = str( mdoc['_id'] )

	return dest_setting_id

def is_dest_files_exist(dest_paths):
	return False if False in [os.path.exists(dest_path) for dest_path in dest_paths] else True

def get_dest_paths(dest_setting_id, ext='txt'):
	# check 
	# generate paths
	dest_paths = {
		'_root_': 'tmp', # path generation will ignore entry surrounded with "_"
		'train': None,
		'test': None,
		'gold': None
	}

	if not os.path.exists(dest_paths['_root_']):
		os.mkdir(dest_paths['_root_'])

	ftypes = filter(lambda x:not x.startswith('_'), dest_paths.keys())
	for ftype in ftypes:

		fn = '.'.join([dest_setting_id, ftype, ext])
		dest_path = os.path.join(dest_paths['_root_'], fn)
		dest_paths[ftype] = dest_path

	return dest_paths

# src_setting_ids: [537086fcd4388c7e81676914, 537086fcd4388c7e816762139 ,...]
def generate_feature_vectors(src_setting_ids):

	global co_feature_setting, eids, udocID_eid

	feature_pool = {}
	feature_vectors = {}

	# for each src_setting_id
	for src_setting_id in src_setting_ids:
		
		# find feature_name --> collection_name
		try:
			feature_name = co_feature_setting.find_one( {'_id': ObjectId(src_setting_id) } )['feature_name']
		except:
			print 'check the format feature setting:',src_setting_id,'in mongodb'
			return False


		collection_name = 'features.' + feature_name

		## use src_setting_id as prefix
		prefix = src_setting_id

		## gathering
		for mdoc in db[collection_name].find():
			udocID = mdoc['udocID']
			emotion = mdoc['emotion']

			## use emotion index as eid
			eid = eids[emotion]

			if eid not in feature_vectors:
				feature_vectors[eid] = defaultdict(list)

			## save the mapping of udocID -> eid
			# udocID_gid[udocID] = eid

			for f_name, f_value in mdoc['feature']:

				# combine f_name with prefix
				f_name = '#'.join([prefix, f_name])

				# generate fid
				if f_name not in feature_pool:
					feature_pool[f_name] = len(feature_pool)
				# get fid
				fid = feature_pool[f_name]

				# feature_vectors[udocID].append( (fid, f_value) )

				feature_vectors[eid][udocID].append( (fid, f_value) )

	return feature_vectors

def tranform_to_svm_format(feature_vectors):
	## (before) feature_vectors:
	# {
	# 	'38000': [(3, 1), (2, 1), (1, 6), (0, 2)],
	# 	...
	# }
	str_feature_vectors = defaultdict(list)

	### transform feature_vectors into all string type
	for eid in feature_vectors:

		for udocID in feature_vectors[eid]:

			# sort
			# [(0, 2), (1, 6), (2, 1), (3, 1)]
			vector = sorted(feature_vectors[eid][udocID], key=lambda x:x[0])

			# toString
			# ['0:2', '1:6', '2:1', '3:1']
			vector = map(lambda x: str(x[0])+':'+str(x[1]), vector)

			# insert the gold_id
			# ['38', '0:2', '1:6', '2:1', '3:1']
			vector.insert(0, str(eid))

			# join whitespace
			# '38 0:2 1:6 2:1 3:1'
			str_vector = ' '.join(vector)

			str_feature_vectors[eid].append( (udocID, str_vector) )

	# str_feature_vectors
	# {
	# 	38: [(31000, '38 0:2 1:6 2:1 3:1'), ...],
	#	...
	# }
	return str_feature_vectors

# {'test': 'tmp/5380557a3681dfc8523cd24e.test.txt', 'train': 'tmp/5380557a3681dfc8523cd24e.train.txt', '_root_': 'tmp', 'gold': 'tmp/5380557a3681dfc8523cd24e.gold.txt'}
def generate_train_test_files(str_feature_vectors, dest_paths):

	fw = {}
	for ftype in dest_paths:
		if ftype.startswith('_'): 
			continue
		else:
			fw[ftype] = open(dest_paths[ftype], 'w')

	# default: [800:200]
	for eid in str_feature_vectors:
		# str_feature_vectors[eid]
		# [(31000, '38 0:2 1:6 2:1 3:1'), ...]

		## sort by udocID
		vectors = sorted(str_feature_vectors[eid], lambda x:x[0])

		train = vectors[:800]
		test  = vectors[800:]

		train_txt = '\n'.join([x[1] for x in train]) + '\n'
		test_txt  = '\n'.join([x[1] for x in test]) + '\n'
		gold_txt  = '\n'.join([str(eid)]*len(test)) + '\n'

		fw['train'].write(train_txt)
		fw['test'].write(test_txt)
		fw['gold'].write(gold_txt)

	for ftype in fw:
		fw[ftype].close()

def run():
	global co_feature_setting
	# collection pointer of feature settings
	co_feature_setting = db[config.co_feature_setting_name]

	# sorted src_setting_id
	src_setting_ids = parse_src_setting_ids()
	
	dest_setting_id = obtain_dest_setting_id(src_setting_ids)

	dest_paths = get_dest_paths(dest_setting_id)

	print 'src_setting_ids:', src_setting_ids
	print 'dest_setting_id:', dest_setting_id
	print 'dest_paths:', dest_paths

	# raw_input()

	# files are all existed
	if is_dest_files_exist(dest_paths):
		print 'all files are existed'
		return True
	# files are not all existed
	else:
		print 'generate feature vectors'
		feature_vectors = generate_feature_vectors(src_setting_ids)

		print 'transform to svm format'
		str_feature_vectors = tranform_to_svm_format(feature_vectors)

		print 'generate train/test files'
		generate_train_test_files(str_feature_vectors, dest_paths)
	
	return True


if __name__ == '__main__':
	import getopt

	add_opts = [
		('setting_id', ['<setting_id>: specify a setting ID (e.g., 537086fcd4388c7e81676914)', 
					   '           which can be retrieved from the mongo collection features.settings' ]),
		# ('--train', ['--train: specify the output filename for training file']),
		# ('--list', ['--list: only list available setting IDs; no further move']),
		# ('--fuse', ['--fuse: enter the feature fusion mode']),
		# ('--test', ['--test: specify the output filename for testing file']),
		# ('--gold', ['--gold: specify the output filename for gold file']),
		# ('--root', ['--root: specify the output root directory'])
	]

	try:
		opts, args = getopt.getopt(sys.argv[2:],'hvo',['help', 'verbose', 'overwrite'])
		setting_id_str = sys.argv[1].strip()
	except:
		config.help('toSVM', addon=add_opts, args=['<setting_id>'], exit=2)

	## read options
	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('toSVM',args=['setting_id'], addon=add_opts)
		elif opt in ('-v','--verbose'): config.verbose = True


	run()
