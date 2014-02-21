import sys, os, json
## python reduce_target.py test/res/all_test_df.res.txt data/emolist.LJ40K.txt data/emolist.Mishne05.txt

def union(lists): return list(set(reduce(lambda x,y:x+y, lists)))

def intersect(lists):

	U = union(lists)
	E = dict(zip(*(U, [0]*len(U))))

	for L in lists:
		for element in E:
			if element in L:
				E[element] += 1
	return [e for e in E if E[e] == len(lists)]

def _load_emolist(path): return open(path).read().strip().split('\n')

def filter_lines(res_path, emolist_pathes):
	lists = [_load_emolist(path) for path in emolist_pathes]
	lines = open(res_path).read().strip().split('\n')
	return [line for line in lines if line.split('\t')[0] in intersect(lists)]

# D['detail']:
#   { emotion: 
# 				PN: {}
#				accuracy: {} 
#	}
#

def patch_filter_json(res_path_root, emolist_pathes, output_path, share_path=''):
	lists = [_load_emolist(path) for path in emolist_pathes]
	intersection = intersect(lists)

	fshare = open(share_path, 'w')

	for res_path in [x for x in os.listdir(res_path_root) if x.endswith('.json')]:
		R = json.load(open(res_path_root+'/'+res_path))

		# extract emotions in the intersection
		Detail = {} # filtered detail dictionary
		ac = []
		for emotion in R['detail']:
			if emotion not in intersection: continue
			Detail[emotion] = R['detail'][emotion]
			ac.append(R['detail'][emotion]['accuracy'])
		R['detail'] = Detail


		# update accuracy
		R['avg_accuracy'] = sum(ac)/float(len(ac))

		# record <emotion>-<accuracy> list in fn
		S = sorted([(e,R['detail'][e]['accuracy']) for e in R['detail']], key=lambda x:x[1], reverse=True)
		detail_string = '\n'.join(['\t'.join(map(lambda x:str(x), s)) for s in S])

		with open(output_path+'/'+res_path.replace('.json','.txt'), 'w') as fw:
			fw.write(detail_string)
		
		# record <name_weight> <avg_accuracy> pair in share files
		system_name_weight = res_path.replace('.json','')
		fshare.write(system_name_weight+'\t'+str(R['avg_accuracy'])+'\n')


		print >> sys.stderr, '> add',system_name_weight

	fshare.close()


def output(lines, res_path, emolist_pathes):
	emolist_label = '+'.join([x.split('/')[-1].replace('emolist','').replace('.txt','').replace('.','') for x in emolist_pathes])

	F = res_path.split('.')
	F.insert(F.index('txt'), emolist_label)
	out_path = '.'.join(F)

	out_content = '\n'.join(lines)
	with open(out_path, 'w') as fw:
		fw.write(out_content)

# emolist_pathes = ['data/emolist.LJ40K.txt', 'data/emolist.Mishne05.txt']
# res_path_root = '../fusion/bruteforce'
# output_path = '../fusion/reduced_bruteforce'
# share_path = '../fusion/bruteforce.txt'
# patch_filter_json(emolist_pathes, res_path_root, output_path, share_path)

if __name__ == '__main__':
	
	res_path = sys.argv[1]
	emolist_pathes = sys.argv[2:]

	lines = filter_lines(res_path, emolist_pathes)
	output(lines, res_path, emolist_pathes)




