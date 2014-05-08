## read from mongodb.features.xxx
## generate svm feature file

import pymongo
mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
db = mc['LJ40K']


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

co_feature.find({'setting': setting_id})