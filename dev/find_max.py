
import os
from collections import Counter

def load(sid, root): return [line.strip().split() for line in open(os.path.join(root, sid+'.train.txt'))]
def find_local_max_value(lines): return sorted( [(line[0], max([float(x.split(':')[1]) for x in line[1:]])) for line in lines], key=lambda a:a[1], reverse=True )
def find_global_max_value(lines): return max([max([float(x.split(':')[1]) for x in line[1:]]) for line in lines])

def find_dimension(lines): return max([max([float(x.split(':')[0]) for x in line[1:]]) for line in lines])

if __name__ == '__main__':
	
	## pattern_emotion
	# sids = ['53855769d4388c4c1f97b796', '538558d3d4388c6748238375', '53855a35d4388c7e00d5aff4', '53855aafd4388c35710f402d', '53855c74d4388c6be1139efe']

	## pat-emo-b (old)
	# sids = ['537d838fd4388c3735dc1916','5382fa27d4388c23417ddc53']

	sids = ['538302743681df11cd509c77']

	root='../tmp'

	for sid in sids:
		lines = load(sid, root)
		top_10 = find_local_max_value(lines)[:10]
		print '='*50
		print 'Top10 value in',sid
		print top_10
		print 
		print 'Dimension:', find_dimension(lines)
		
