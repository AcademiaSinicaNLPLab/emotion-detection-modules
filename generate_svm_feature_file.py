## read from mongodb.features.xxx
## generate svm feature file

import config
import pymongo

db = pymongo.Connection(config.mongo_addr)[config.db_name]

setting = {
	"section": "b20_m60_e20",
	"feature_type": "position",
	"f": 0,
	"c": 0
}

# use collection e.g., features.position
co_feature = db['features.'+setting['feature_type']]

# get setting id
setting_id = str(db['features.settings'].find_one(setting)['_id'])

# later used in getting emotion id
emotion_list = sorted([d['emotion'] for d in db['emotions'].find({'label': 'LJ40K'})])

feature_names = {}
for mdoc in co_feature.find({'setting': setting_id}):

	# skip if no feature extracted for the current doc
	if not mdoc['feature']:
		continue

	if type(mdoc['feature']) == dict:
		feature = mdoc['feature'].items()
	elif type(mdoc['feature']) == list:
		feature = mdoc['feature']
	else:
		print >> sys.stderr, '[error] cannot read feature with', type(mdoc['feature']) ,'type'
		exit(-1)

	## form the vector
	vector = [ str(emotion_list.index(mdoc['emotion'])) ]

	for feature_name, feature_value in feature:

		# get feature id
		if feature_name in feature_names:
			fid = feature_names[feature_name]
		else:
			fid = len(feature_names)
			feature_names[feature_name] = fid

		# store as the form 1:100
		vector.append( ( str(fid)+':'+str(feature_value)) )

	print ' '.join(vector)
	raw_input()
