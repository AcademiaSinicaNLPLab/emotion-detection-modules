## read from mongodb.features.xxx
## generate svm feature file

import config, color
import pickle
import pymongo, sys, os, re
from collections import defaultdict
from bson.objectid import ObjectId

# print >> sys.stderr, '[info]\tconnecting mongodb'
db = pymongo.Connection(config.mongo_addr)[config.db_name]

# later used in getting emotion id
emotion_list = sorted([d['emotion'] for d in db['emotions'].find({'label': 'LJ40K'})])
# print >> sys.stderr, '[info]\tget emotion list:', len(emotion_list), 'emotions'

eids = { emotion_list[i]: i for i in range(len(emotion_list)) }

## ------------------------------------------------------- ##

# feature_names = {} # global used because of multiple feature sets
list_setting_ids = False
setting_id = None
settings = {}
fusion_mode = False
fusion_all = False
sids_map = {}

setting_ids = []
co_feature_names = []
co_features = {}

## default: path to files of train/test/gold
pathes = {
	'_root_': 'tmp', # path generation will ignore entry surrounded with "_"
	'train': None,
	'test': None,
	'gold': None
}

def setting_prompt():
	for i, setting in enumerate(db[config.co_feature_setting_name].find()):
		if setting['feature_name'] == 'fusion':
			continue
		sid = str(setting['_id'])
		sids_map[i] = sid
		settings[sid] = setting
		sname = setting['feature_name']
		print >> sys.stderr, i,'>', color.render( sid, 'yellow' )
		for x in setting:
			if x == '_id': continue
			print >> sys.stderr, '\t' ,x, ':', color.render( str(setting[x]), 'g' )
		print >> sys.stderr

def choose():
	while True:
		print >> sys.stderr,'> choose setting ID(s) [ 0 ~ '+str(len(sids_map)-1)+' ]: ',
		str_sids = raw_input()
		try:
			setting_ids = map(lambda x: sids_map[int(x)], re.findall(r'([0-9]+)\s*,?', str_sids))
			break
		except:
			print >> sys.stderr, color.render( '\n[error] input CORRECT format: e.g., "0,1,2" or "1", and valid index number\n', 'r' )
	print >> sys.stderr
	return setting_ids

def get_fusion_id(setting_ids):

	if len(setting_ids) < 2:
		return False

	sids = sorted(setting_ids)
	
	fns = [settings[sid]['feature_name'] for sid in sids]
	if len(set(fns)) < len(fns):
		print >> sys.stderr, "[error] don't fuse the same kind of feature"
		exit(-1)

	source = '+'.join(fns)
	fused_ids = ','.join(sids)

	mdoc = db[config.co_feature_setting_name].find_one({'fusion': fused_ids})

	if not mdoc:
		if config.verbose:
			print >> sys.stderr, '[info] create a new feature instance'
		fusion_setting = {'fusion': fused_ids, 'feature_name': 'fusion', 'source': source}
		fusion_id = str(db[config.co_feature_setting_name].insert( fusion_setting ))
		## store
		settings[fusion_id] = fusion_setting
	else:
		if config.verbose:
			print >> sys.stderr, '[info] feature instance fetched'
		fusion_id = str(mdoc['_id'])
		settings[fusion_id] = mdoc

	return fusion_id

def check_destination(pathes, token, ext='txt'):

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
			if not fusion_all:
				print >> sys.stderr, '[error] destination file', color.render(dest_path, 'red') ,'is already existed'
				print >> sys.stderr, '        use -o or --overwrite to force overwrite'
				exit(-1)
			else:
				return False

	return new_pathes

def generate_vectors():
	vectors = defaultdict(list)
	# udocID : [feature1] + [feature2] + ...
	featurePool = defaultdict(list)
	# udocID : <emotion>
	docEmotion = {}
	# feature_modifiers[setting_id]
	# mdoc:
	# {
	# 	"_id" : ObjectId("53730f67d4388c27cc4c06f2"),
	# 	"emotion" : "sleepy",
	# 	"setting" : "53730f67d4388c27cc4c06f1",  ## <setting_id>
	# 	"udocID" : 38000,
	# 	"feature": [
	# 		['what way end', 1],
	# 		['i think its', 1],
	# 		...
	# 	]
	# }
	feature_names = {}

	for setting_id in co_features:
		co_feature = co_features[setting_id]

		feature_modifier = co_feature.name.split('.')[-1]

		for mdoc in co_feature.find({'setting': setting_id}):
			udocID = mdoc['udocID']
			featurePool[udocID] += [(feature_modifier+'_'+f, v) for (f,v) in mdoc['feature']]
			docEmotion[udocID] = mdoc['emotion']

	for udocID in featurePool:

		feature = featurePool[udocID]
		emotion = docEmotion[udocID]

		
		# feature_name: 	"I think"
		# feature_value: 	3
		# 

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

		if len(set([k for (k,v) in feature_vector])) < len(feature_vector):

			print feature
			print feature_vector
			raw_input()

		# ready to generate plain text feature vector
		feature_vector = [str(fid)+':'+str(feature_value) for (fid, feature_value) in feature_vector]



		# put the gold answer at the first place
		feature_vector.insert(0, str(emotion_list.index(emotion)) )

		# toString
		# 3 0:2.768 1:1.909 2:1.46201119074 3:6.365 4:3.641 5:2.166 ...
		feature_vector = ' '.join(feature_vector)

		vectors[ emotion ].append( (udocID, feature_vector) )



	return vectors

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

		eid = emotion_list.index(e)
		### format of <setting_id>.golt.txt
		### eid docID	emotion
		### -------------------
		### 3	3950	annoyed
		### 3	3951	annoyed
		### ...
		gold_txt  = '\n'.join([ '\t'.join([str(eid),str(x[0]),e]) for x in test])  + '\n'

		fw['train'].write(train_txt)
		fw['test'].write(test_txt)
		fw['gold'].write(gold_txt)

	# close all file pointer
	for ftype in fw:
		fw[ftype].close()

def find_available_fusion_targets():
	from itertools import product, combinations
	F = defaultdict(list)
	for mdoc in [x for x in db[config.co_feature_setting_name].find() if x['feature_name'] != 'fusion' ]:
		sid = str(mdoc['_id'])
		settings[sid] = mdoc
		F[mdoc['feature_name']].append(str(mdoc['_id']))
	candidates = []
	for i in range(2, len(F)+1):
		for target_types in list(combinations(F.keys(), i)):
			sid_lists = [F[target_type] for target_type in target_types]
			candidates += list(product( *sid_lists ))
	return candidates

if __name__ == '__main__':
	import getopt

	add_opts = [
		('--setting', ['--setting: specify a setting ID (e.g., 537086fcd4388c7e81676914)', 
					   '           which can be retrieved from the mongo collection features.settings' ]),
		('--train', ['--train: specify the output filename for training file']),
		('--list', ['--list: only list available setting IDs; no further move']),
		('--fuse', ['--fuse: enter the feature fusion mode']),
		('--test', ['--test: specify the output filename for testing file']),
		('--gold', ['--gold: specify the output filename for gold file']),
		('--root', ['--root: specify the output root directory'])
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hvo',['help', 'verbose', 'overwrite', 'setting=', 'train=', 'test=', 'gold=', 'root=', 'list', 'fuse', 'fuseall'])
	except getopt.GetoptError:
		config.help('toSVM', addon=add_opts, exit=2)

	## read options
	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('toSVM', addon=add_opts)
		elif opt in ('--train'): pathes['train'] = arg.strip()
		elif opt in ('--test'): pathes['test'] = arg.strip()
		elif opt in ('--gold'): pathes['gold'] = arg.strip()
		elif opt in ('--root'): pathes['_root_'] = arg.strip()
		elif opt in ('--setting'): setting_id = arg.strip()
		elif opt in ('--list'): list_setting_ids = True
		elif opt in ('--fuse'): fusion_mode = True
		elif opt in ('--fuseall'): 
			fusion_mode = True
			fusion_all = True
		elif opt in ('-v','--verbose'): config.verbose = True
		elif opt in ('-o','--overwrite'): config.overwrite = True

	if fusion_all:
		candidates = find_available_fusion_targets()
		for setting_ids in candidates:

			## each run

			# feature_names = {} # clear feature_names

			for setting_id in setting_ids:
				### =======================================
				### check if fetch collection existed
				### =======================================
				
				co_feature_name = 'features.'+settings[setting_id]['feature_name']
				if settings[setting_id]['feature_name'] == 'position':
					co_feature_name = 'features.pattern_emotion_position'
				co_feature_existed = co_feature_name in db.collection_names()
				if co_feature_existed:

					co_features[setting_id] = db[co_feature_name]
				else:
					print >> sys.stderr, '(error) source collection', color.render(co_feature_name, 'yellow'),'is NOT existed'
					print >> sys.stderr, '\tcheck the fetch target and run again!!'
					exit(-1)

			print >> sys.stderr, '[info] fetching -->',
			sys.stderr.flush()
			fusion_id = get_fusion_id(setting_ids)

			### =======================================
			## check destination files/folder
			### =======================================
			new_pathes = check_destination(pathes, token=fusion_id, ext='txt')
			
			if not new_pathes:
				print >> sys.stderr, fusion_id, 'next'
				continue

			else:
				print >> sys.stderr, fusion_id, '-->', 

			sys.stderr.flush()

			## generate svm vectors
			print >> sys.stderr, 'building vectors --> ',
			sys.stderr.flush()
			vectors = generate_vectors()

			## generate test and train files
			print >> sys.stderr, 'generate files --> ',
			sys.stderr.flush()

			generate_test_train_files(vectors, new_pathes)
			print >> sys.stderr, 'done.'
	else:

		### =======================================
		### get setting ids
		### =======================================
		if setting_id:
			# use setting_id to retrieve setting from db.feature.settings, which is defined in config.co_feature_setting_name
			## check if input is a valid setting id
			mdoc = db[config.co_feature_setting_name].find_one( {'_id': ObjectId(setting_id) } )
			if mdoc:
				setting_ids.append(setting_id)
				settings[setting_id] = mdoc
			else:
				print >> sys.stderr, '(error) cannot match setting using', color.render(setting_id, 'yellow'),' this setting_id'
				print >> sys.stderr, '\tcheck the setting_id and run again!!'
				exit(-1)
		## no specified setting id, list all, show prompt
		else:
			# list all setting ids
			setting_prompt()
			# choose (a) setting id(s)
			setting_ids = choose()

		### =======================================
		### determine fusion mode or not
		### =======================================
		if fusion_mode:
			fusion_id = get_fusion_id(setting_ids)
		## if not in fusion mode, keep the setting_ids list, do nothing
		else:
			pass

		### =======================================
		### pring current setting and setting_id
		### =======================================
		if fusion_mode and fusion_id:
			print >> sys.stderr, '[info] mode:', color.render('FUSION', 'lp')	
		else:
			print >> sys.stderr, '[info] mode:', color.render('NORMAL', 'lp')
		for setting_id in setting_ids:
			# print setting_ids
			print >> sys.stderr, '\t> setting id:', color.render(setting_id, 'lc')
			print >> sys.stderr, '\t> setting:', '\n\t', '-'*30
			for key in settings[setting_id]:
				print >> sys.stderr, '\t', color.render(key, 'w'), ':', color.render( str(settings[setting_id][key]), 'g')
			print >> sys.stderr, '\t', '-'*30

		### =======================================
		### check if fetch collection existed
		### =======================================
		for setting_id in setting_ids:

			
			if settings[setting_id]['feature_name'] == 'position':
				co_feature_name = 'features.pattern_emotion_position'
			else:
				co_feature_name = 'features.'+settings[setting_id]['feature_name']

			co_feature_existed = co_feature_name in db.collection_names()
			if co_feature_existed:

				co_features[setting_id] = db[co_feature_name]

			else:
				print >> sys.stderr, '(error) source collection', color.render(co_feature_name, 'yellow'),'is NOT existed'
				print >> sys.stderr, '\tcheck the fetch target and run again!!'
				exit(-1)
		
		### only fuse mode supports multiple setting_id
		# print len(co_features), fusion_mode
		if len(co_features) > 1 and not fusion_mode:
			print >> sys.stderr, '(error) use',color.render('--fuse','r'), 'to enable multiple setting_ids'
			exit(-1)

		### =======================================
		## check destination files/folder
		### =======================================
		if fusion_mode and fusion_id:
			new_pathes = check_destination(pathes, token=fusion_id, ext='txt')
		else:
			new_pathes = check_destination(pathes, token=setting_id, ext='txt')

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
		print >> sys.stderr, 'generating ','fused' if fusion_mode and fusion_id else '', ' vectors...',
		sys.stderr.flush()
		vectors = generate_vectors()
		print >> sys.stderr, 'done.'

		## generate test and train files
		print >> sys.stderr, 'generate test train files...'
		generate_test_train_files(vectors, new_pathes)
		sys.stderr.flush()
		print >> sys.stderr, 'done.'

		if fusion_mode:
			print >> sys.stderr, 'fusion id: ', fusion_id


