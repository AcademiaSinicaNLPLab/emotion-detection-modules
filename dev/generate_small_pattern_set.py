import pymongo, config

db = pymongo.Connection(config.mongo_addr)[config.db_name]

co_lexicon_original = db['lexicon.nested']
co_lexicon_filtered = db['lexicon.nested.min_count_4']

mdocs = list( co_lexicon_original.find() )

for mdoc in mdocs:

	if sum( [ mdoc['count'][e] for e in mdoc['count'] ] ) >= 4:
		new_mdoc = {
			'pattern': mdoc['pattern'], 
			'count': mdoc['count']
		}
		co_lexicon_filtered.insert( new_mdoc )

co_lexicon_filtered.create_index('pattern')