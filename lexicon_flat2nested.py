import pymongo
import config
from collections import defaultdict, Counter

db = pymongo.Connection(config.mongo_addr)[config.db_name]

co_f = db['lexicon.flat']
co_n = db['lexicon.nested']

cache = defaultdict( dict )

docs = list( co_f.find() )

for doc in docs:
	cache[doc['pattern']][doc['emotion']] = doc['count']

for key in cache:
	mdoc = {
		"pattern": key,
		"count": cache[key] 
	}
	co_n.insert(mdoc)



## lexicon.flat
# {
#     "emotion" : "blank",
#     "pattern" : "i am pissed",
#     "count" : 1
# }

## lexicon.nested
# {
#     "pattern" : "i am pissed",
#     "count" : 
#     {
#         "blank": 1,
#         ...
#     }
# }