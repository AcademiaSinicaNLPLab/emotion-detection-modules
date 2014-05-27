### 

import os, re, color

from collections import defaultdict

fns = defaultdict(dict)

for fn in os.listdir('tmp'):
	r = re.match(r'^([0-9a-z]{24})', fn)

	abs_path = os.path.join('tmp', fn)
	if r:
		sid = r.group(1)
		# print os.stat(abs_path)
		size = os.stat(abs_path).st_size

		if fn.endswith('.m'):
			fns[sid]['model'] = size
		elif fn.endswith('.gold.txt'):
			fns[sid]['gold'] = size
		elif fn.endswith('.train.txt'):
			fns[sid]['train'] = size
		elif fn.endswith('.test.txt'):
			fns[sid]['test'] = size
		elif fn.endswith('.out'):
			fns[sid]['out'] = size
	else:
		continue

for sid in fns:

	if 0 in fns[sid].values():
		status = 'need to check'
	elif len(fns[sid]) == 3:
		status = color.render('3/5', 'r')
	elif len(fns[sid]) == 4:
		status = color.render('4/5', 'y')
	elif len(fns[sid]) == 5:
		status = color.render('all done', 'g')

	print sid, '(', status ,')'

	for ftype in fns[sid]:
		print '\t',ftype, '\t',fns[sid][ftype]
