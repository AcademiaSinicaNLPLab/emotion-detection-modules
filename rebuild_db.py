## rebuild sentence and dependency database
import pymongo, os
import dependency
from nltk import Tree
# os.path.join
deps_root = '/Users/Maxis/corpus/LJ40K/'

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
db = mc['LJ40K']
# sent_root = '/Users/Maxis/corpus/LJ40K_sent/'

# epath = os.path.join(deps_root, 'annoyed/30.txt')

# doc = open(epath).read()
def digest_deps(deps, tree_pos, header={}):
	dobjs = []
	for dep in deps:

		dobj = {}
		if header:
			for x in header:
				dobj[x] = header[x]
		
		dobj['rel'] = dep['rel']
		dobj['x'] = dep['ltoken']
		dobj['xIdx'] = dep['lidx']
		dobj['y'] = dep['rtoken']
		dobj['yIdx'] = dep['ridx']

		lidx = dep['lidx']-1
		ridx = dep['ridx']-1
		dobj['xPos'] = tree_pos[lidx][1]
		dobj['yPos'] = tree_pos[ridx][1]

		dobjs.append(dobj)
	return dobjs

udocID, usentID = 0, 0

for emotion in [x for x in os.listdir(deps_root) if not x.startswith('.')]:
	efolder = os.path.join(deps_root, emotion)
	for ef in [y for y in os.listdir(efolder) if y.endswith('.txt')]:
		epath = os.path.join(efolder, ef)

		# assign udocID
		
		doc = open(epath).read()

		for section in doc.split('(ROOT\r\n'):

			# assign usentID
			
			if len(section.strip()) == 0: continue

			tree_str, deps_str = section.split('\r\n\r\n')

			# tree
			tree_str = '(ROOT\r\n' + tree_str
			t = Tree(tree_str.strip())
			tree_pos = t.pos()
			sent = ' '.join([x[0] for x in tree_pos])
			sent_pos = ' '.join(['/'.join(x) for x in tree_pos])
			sent_length = len(tree_pos)

			sobj = {'emotion':emotion, 'udocID':udocID, 'usentID': usentID, 'sent':sent, 'sent_pos':sent_pos,'sent_length':sent_length}


			# deps
			deps_str = deps_str.strip()[1:-1]
			deps = dependency.read(deps_str, delimiter='), ', auto_detect=False, return_type=dict)


			meta = {'emotion':emotion, 'udocID':udocID, 'usentID':usentID, 'sent_length':sent_length}
			dobjs = digest_deps(deps, tree_pos, header=meta)

			for dobj in dobjs:
				db['deps'].insert(dobj)

			db['sents'].insert(sobj)

			usentID += 1
		udocID += 1
		
		print 'processed',' --> '.join(epath.split('/')[-2:])

# for emotion_file in [x for x in os.listdir(sent_root) if x.endswith('.txt')]:
	# emotion_file_path = os.path.join(sent_root, emotion_file)


	