import os
from collections import Counter
new = ('1', '-1')

def to_binary(sid, gold):
	c = Counter()
	for ftype in ('train', 'test'):
		fn = '.'.join([sid, ftype, gold, 'b'])
		path = os.path.join('tmp', fn)
		fw = open(path, 'w')
		for line in open('tmp/'+sid+'.'+ftype+'.txt'):
			line = line.strip().split(' ')
			label = line[0]
			if label == gold:
				line[0] = '1'
				c['1'] += 1
			else:
				line[0] = '-1'
				c['-1'] +=1
			fw.write( ' '.join(line) + '\n' )
		fw.close()
	print c
	print '1', ':', c['-1']/float(c['1'])

	
if __name__ == '__main__':

	sid = '53875c80d4388c4100cac5b2'
	gold = '38'
	to_binary(sid, gold)