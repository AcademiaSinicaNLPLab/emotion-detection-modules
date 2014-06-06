import pymongo

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')

db = mc['LJ40K']

co_docs = db['docs']
co_sents = db['sents']
co_deps = db['deps']


data = {
	'emotion':'accomplished',
	'ldocID':0,
	'udocID': 0
}

# co_docs.insert(data)

