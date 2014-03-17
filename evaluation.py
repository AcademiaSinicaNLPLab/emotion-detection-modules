import pymongo
mc = pymongo.Connection('doraemon')
db = mc['LJ40K']

# get all emotions
emotions = sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}) ])

docscores = db['docscores']

def get_test_instances():
	options = {
		'ds_function': ,
		'ps_function': ,
		'smoothing': ,
		# '': ,
		# '': ,
		# '': ,
	}
	for emotion in emotions:
		query = { 'emotion': emotion }
		query.update(options)

		docscores.find( query )