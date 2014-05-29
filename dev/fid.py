## find fusion id

import pymongo, re, sys

db = pymongo.Connection('doraemon.iis.sinica.edu.tw')['LJ40K']

if __name__ == '__main__':
	
	if len(sys.argv) > 1:
		sids = [x for x in sys.argv[1:] if re.match(r'[0-9a-z]{24}',x)]
	else:
		print 'sid(s) >', 
		sids = raw_input()
		sids = re.findall(r'[0-9a-z]{24}[\s\.\,]*', sids)
	sids = list(set(sids))
	if len(sids) == 1:
		print 'Not a fusion'
	## fusion id
	else:
		sources = ','.join( sorted(sids) )
		mdoc = db['features.settings'].find_one({ 'sources': sources })
		if mdoc:
			print 'fusion id >',str(mdoc['_id'])
		

	