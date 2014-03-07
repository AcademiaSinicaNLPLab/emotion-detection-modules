## rebuild sentence and dependency database
import pymongo, os
import dependency
from nltk import Tree
# os.path.join
deps_root = '/Users/Maxis/corpus/LJ40K/'

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
# sent_root = '/Users/Maxis/corpus/LJ40K_sent/'

# epath = os.path.join(deps_root, 'annoyed/30.txt')

# doc = open(epath).read()
def digest_deps(deps, tree_pos):
	dobj = {}
	dobj['rel'] = deps['rel']
	dobj['x'] = deps['ltoken']
	dobj['xIdx'] = deps['lidx']
	dobj['y'] = deps['rtoken']
	dobj['yIdx'] = deps['ridx']

	lidx = deps['lidx']-1
	ridx = deps['ridx']-1
	dobj['xPos'] = tree_pos[lidx][1]
	dobj['yPos'] = tree_pos[ridx][1]

	return dobj

udocID, usentID = 0, 0

for emotion in [x for x in os.listdir(deps_root) if not x.startswith('.')]:
	efolder = os.path.join(deps_root, emotion)
	for ef in [y for y in os.listdir(efolder) if y.endswith('.txt')]:
		epath = os.path.join(efolder, ef)

		# assign udocID
		udocID += 1
		doc = open(epath).read()

		for section in doc.split('(ROOT\r\n'):

			# assign usentID
			usentID += 1
			if len(section.strip()) == 0: continue
			
			tree_str, deps_str = section.split('\r\n\r\n')

			# tree
			tree_str = '(ROOT\r\n' + tree_str
			t = Tree(tree_str)
			tree_pos = t.pos()
			sent = [x[0] for x in tree_pos]
			sent_pos = ['/'.join(x) for x in tree_pos]
			sent_length = len(tree_pos)

			sobj = {'emotion':emotion, 'udocID':udocID, 'usentID': usentID, 'sent':sent, 'sent_pos':sent_pos,'sent_length':sent_length}


			# deps
			deps_str = deps_str.strip()
			deps = dependency.read(deps_str, delimiter='), ', auto_detect=False, return_type=dict)


			dobj = digest_deps(deps, tree_pos)

			dobj['emotion'] = emotion
			dobj['udocID'] = udocID
			dobj['usentID'] = usentID
			dobj['sent_length'] = sent_length


			mc['deps'].insert(sobj)
			mc['sents'].insert(sobj)

		print 'processed',epath

# for emotion_file in [x for x in os.listdir(sent_root) if x.endswith('.txt')]:
	# emotion_file_path = os.path.join(sent_root, emotion_file)


	