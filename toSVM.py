## read from mongodb.features.xxx
## generate svm feature file

import config, color
import pymongo, sys, os
from collections import defaultdict

# print >> sys.stderr, '[info]\tconnecting mongodb'
db = pymongo.Connection(config.mongo_addr)[config.db_name]

# later used in getting emotion id
emotion_list = sorted([d['emotion'] for d in db['emotions'].find({'label': 'LJ40K'})])
# print >> sys.stderr, '[info]\tget emotion list:', len(emotion_list), 'emotions'

## ------------------------------------------------------- ##

feature_names = {} # global used because of multiple feature sets


def check_and_generate_destination(pathes, token, ext='txt'):

	if not os.path.exists(pathes['_root_']):
		os.mkdir(pathes['_root_'])

	new_pathes = {}

	for ftype in pathes:

		if ftype.startswith('_') and ftype.endswith('_'):
			continue

		fn = pathes[ftype]
		## auto-generated filename
		fn = fn if fn else '.'.join([token, ftype, ext])

		## check if destination path already exists
		# join root to yield destination path
		dest_path = os.path.join(pathes['_root_'], fn)
		new_pathes[ftype] = dest_path

		## destination's already existed
		if os.path.exists(dest_path) and not config.overwrite:
			print >> sys.stderr, '[error] destination file', color.render(dest_path, 'red') ,'is already existed'
			print >> sys.stderr, '        use -o or --overwrite to force overwrite'
			exit(-1)

	return new_pathes

def generate_vectors():

	vectors = defaultdict(list)

	for mdoc in co_feature.find({'setting': setting_id}):

		# skip if no feature extracted for the current doc
		if not mdoc['feature']:
			continue

		if type(mdoc['feature']) == dict:
			feature = mdoc['feature'].items()
		elif type(mdoc['feature']) == list:
			feature = mdoc['feature']
		else:
			print >> sys.stderr, '[error]\tcannot read feature with', type(mdoc['feature']) ,'type'
			exit(-1)

		if config.verbose:
			print >> sys.stderr, 'got mongo doc with', len(mdoc['feature']), 'feature values'

		## form the feature vector
		feature_vector = []
		for feature_name, feature_value in feature:

			# get feature id
			if feature_name in feature_names:
				fid = feature_names[feature_name]
			else:
				fid = len(feature_names)
				feature_names[feature_name] = fid

			# store as the form 1:100
			feature_vector.append( ( fid, feature_value) )

		# feature indices must be in an ascending order
		feature_vector.sort(key=lambda x:x[0])

		# ready to generate plain text feature vector
		feature_vector = [str(fid)+':'+str(feature_value) for (fid, feature_value) in feature_vector]

		# put the gold answer at the first place
		feature_vector.insert(0, str(emotion_list.index(mdoc['emotion'])) )

		# toString
		# 3 0:2.768 1:1.909 2:1.46201119074 3:6.365 4:3.641 5:2.166 ...
		feature_vector = ' '.join(feature_vector)

		vectors[ mdoc['emotion'] ].append( (mdoc['udocID'], feature_vector) )
	
	return vectors

# out_root = 'tmp'


def generate_test_train_files(vectors, pathes):

	# setup file pointers
	fw = {}
	for ftype in pathes:
		dest_path = pathes[ftype]
		fw[ftype] = open(dest_path, 'w')

	# default: [800:200]
	for e in vectors:
		vector = sorted(vectors[e], key=lambda x:x[0])
		train, test = vector[:800], vector[800:]

		train_txt = '\n'.join([str(x[1]) for x in train]) + '\n'
		test_txt  = '\n'.join([str(x[1]) for x in test])  + '\n'
		gold_txt  = '\n'.join([str(x[0]) for x in test])  + '\n'

		fw['train'].write(train_txt)
		fw['test'].write(test_txt)
		fw['gold'].write(gold_txt)

	# close all file pointer
	for ftype in fw:
		fw[ftype].close()

if __name__ == '__main__':
	import getopt

	add_opts = [
		('--setting', ['--setting: specify a setting ID (e.g., 537086fcd4388c7e81676914)', 
					   '           which can be retrieved from the mongo collection features.settings' ]),
		('--train', ['--train: specify the output filename for training file']),
		('--test', ['--test: specify the output filename for testing file']),
		('--gold', ['--gold: specify the output filename for gold file']),
		('--root', ['--root: specify the output root directory'])
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hvo',['help', 'verbose', 'overwrite', 'setting=', 'train=', 'test=', 'gold=', 'root='])
	except getopt.GetoptError:
		config.help('toSVM', addon=add_opts, exit=2)


	## default: path to files of train/test/gold
	pathes = {
		'_root_': 'tmp', # path generation will ignore entry surrounded with "_"
		'train': None,
		'test': None,
		'gold': None
	}
	## default: setting
	setting = {
		"counting_unit_type" : 0, 
		"section" : "b20_m60_e20", 
		"feature_name" : "position", ## important ## ussed in selecting collection
		"feature_value_type" : 1
	}
	## set default setting as None
	setting_id = None

	## read options
	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('toSVM', addon=add_opts)
		elif opt in ('--train'): pathes['train'] = arg.strip()
		elif opt in ('--test'): pathes['test'] = arg.strip()
		elif opt in ('--gold'): pathes['gold'] = arg.strip()
		elif opt in ('--root'): pathes['_root_'] = arg.strip()
		elif opt in ('--setting'): 
			setting_id = arg.strip() if len(arg.strip()) > 0 else None
		elif opt in ('-v','--verbose'): config.verbose = True
		elif opt in ('-o','--overwrite'): config.overwrite = True



	## got specified setting_id
	# use setting_id to retrieve setting from db.feature.settings, which is defined in config.co_feature_setting_name
	if setting_id:
		from bson.objectid import ObjectId
		setting = db[config.co_feature_setting_name].find_one( {'_id': ObjectId(setting_id) } )
		if not setting:
			print >> sys.stderr, '(error) cannot match setting using', color.render(setting_id, 'yellow'),' this setting_id'
			print >> sys.stderr, '\tcheck the setting_id and run again!!'
			exit(-1)

	## no specified setting_id
	# use default setting to obtain setting_id
	else:
		setting_id = str(db[config.co_feature_setting_name].find_one(setting)['_id'])

	## pring current setting and setting_id
	print >> sys.stderr, '[info]\tget setting id:', color.render(setting_id, 'lc')
	print >> sys.stderr, '[info]\tcurrent setting:', '\n\t', '-'*30
	for key in setting:
		print >> sys.stderr, '\t', color.render(key, 'w'), ':', color.render( str(setting[key]), 'g')
	print >> sys.stderr, '\t', '-'*30

	## check if fetch collection existed
	co_feature_name = 'features.'+setting['feature_name']
	co_feature_existed = co_feature_name in db.collection_names()
	if not co_feature_existed:
		print >> sys.stderr, '(error) source collection', color.render(config.co_lexicon_name, 'yellow'),'is not existed'
		print >> sys.stderr, '\tcheck the fetch target and run again!!'
		exit(-1)

	## check destination files/folder
	# token: setting_id
	new_pathes = check_and_generate_destination(pathes, token=setting_id, ext='txt')

	# use collection e.g., features.position
	co_feature = db[co_feature_name]

	## confirm message
	confirm_msg = [
		('[opt]\tfetch collection', color.render(co_feature_name, 'y'), '(ok)' if co_feature_existed else '(none)'),
		('[opt]\tdestination', color.render(pathes['_root_'], 'y') ),
		('[opt]\tverbose', config.verbose ),
		('[opt]\toverwrite', config.overwrite)
	]
	config.print_confirm(confirm_msg, bar=40, halt=True)	

	# -- run --
	## generate svm vectors
	print >> sys.stderr, 'generating vectors...',
	sys.stderr.flush()
	vectors = generate_vectors()
	print >> sys.stderr, 'done.'

	## generate test and train files
	print >> sys.stderr, 'generate test train files...',
	generate_test_train_files(vectors, new_pathes)
	sys.stderr.flush()
	print >> sys.stderr, 'done.'


