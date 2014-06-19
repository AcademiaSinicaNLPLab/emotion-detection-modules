# -*- coding: utf-8 -*-
import sys
sys.path.append('pymodules')
import color

####  ----------------------------------- must-do ----------------------------------- ####

mongo_addr = 'doraemon.iis.sinica.edu.tw'
# mongo_addr = 'wolverine.iis.sinica.edu.tw'
db_name = 'LJ40K'
# db_name = 'NTCIR'

# category = 'polarity' ## target to be categorized. e.g., emotion, polarity
category = 'emotion' ## target to be categorized. e.g., emotion, polarity
corpus_root = '/corpus/NTCIR'
####  ----------------------------------- must-do ----------------------------------- ####

#### define program names
ds_name = 'document_scoring'
# ps_name = 'pattern_scoring'
ev_name = 'evaluation'
genSVM_name = 'toSVM'
runSVM_name = 'run_svm'

# -------------------------------------------- paths -------------------------------------------- #
# libsvm abs path
libsvm_path  = '/tools/libsvm'
libsvm_program = {
	'train':'svm-train',
	'test': 'svm-predict',
	'check': 'tools/checkdata.py',
}
# relative file pathes for train, test, model and out
svm_file_root = 'tmp'

# -------------------------------------------- mongodb -------------------------------------------- #
## mongo collection setting
keywordFeat_name = 'keyword_feature'
keywordEmotionFeat_name = 'keyword_emotion_feature'
keywordPositionFeat_name = 'keyword_position_feature'
keywordEmotionPositionFeat_name = 'keyword_emotion_position_feature'

patternFeat_name = 'pattern_feature'
patternEmotionFeat_name = 'pattern_emotion_feature'
patternPositionFeat_name = 'pattern_position_feature'
patternEmotionPositionFeat_name = 'pattern_emotion_position_feature'

## mongo collection name
co_emotions_name = 'emotions'
co_category_name = category

co_docs_name = 'docs'
co_sents_name = 'sents'
co_deps_name = 'deps'
co_pats_name = 'pats'

co_lexicon_name = 'lexicon.nested'
co_results_name = 'NewRes'
co_patsearch_name = 'pats_trim'
co_feature_setting_name = 'features.settings'

## total count
co_lexicon_pattern_tc_name = 'lexicon.pattern_total_count'
co_lexicon_keyword_tc_name = 'lexicon.keyword_total_count'

co_svm_out_name  = 'svm.out'	# (svm) .out.txt
co_svm_gold_name = 'svm.gold'	# (svm) .gold
co_svm_eval_name = 'svm.eval'	# (svm) evalutation results

## default
co_patscore_prefix = 'patscore'
co_docscore_prefix = 'docscore'

## to be setup
# co_patscore_name = co_patscore_prefix
# co_docscore_name = ''
# ------------------------------------------ (end) mongodb ------------------------------------------ #

## names of functions
ps_function_name = 'ps_function'
ds_function_name = 'ds_function'
sig_function_name = 'sig_function'
smoothing_name = 'smoothing'
limit_name = 'limit'

## default values
ps_function_type = 0
ds_function_type = 0
sig_function_type = 0
smoothing_type = 0
## minimum occurrence of a pattern
min_count = 0

###################################
### document feature extraction ###
begPercentage = 20
midPercentage = 60
endPercentage = 20
countingUnitType = 0
featureValueType = ''
minCount = 4
cutoffPercentage = 100
###################################
### document feature extraction ###
keyword_type = 'basic' 
lemma = False
###################################


overwrite = False
verbose = False
debug = False
topk = 1


delta_d = 356.10659375

### latest version: support automatically insert addon option names
### i.e, config.py doesn't care about neither the addon opts nor the description
### e.g., in runSVM_name, addon is a list of length 3, which looks like [ ('--setting', [...]), ('--list', [...]), ('--param', [...]) ]
###       and the program will incorporate missing opts and yield: ['-v', '-o', '--setting', '--list', '--param']
opt_fields = {
	# ps_name: 	['-p','-s','-v', '-o'],
	ds_name: 	['-p','-d','-s','-g','-l','-v', '-o'],
	ev_name: 	['-p','-d','-s','-g','-l','-v', '-o'],
	
	keywordFeat_name:	['-k','--lemma','-v'],
	keywordEmotionFeat_name:	['-k','--lemma','-v'],
	keywordPositionFeat_name:	['-b','-m','-e','-k','--lemma','-v'],
	keywordEmotionPositionFeat_name:	['-b','-m','-e','-k','--lemma','-v'],

	patternFeat_name:	['-l','-v'],
	patternEmotionFeat_name:	['-f','-v'],
	patternPositionFeat_name:	['-b','-m','-e','-l','-v'],
	patternEmotionPositionFeat_name:	['-b','-m','-e','-f','-v'],

	genSVM_name:['-v', '-o'],
	runSVM_name:['-v', '-o'],

	'default': ['-v', '-o']
}
_abbr = {
	'p': 'ps_function',
	'd': 'ds_function',
	'g': 'sig_function',
	's': 'smoothing',
	'l': 'limit'
}

## fields="p,d,g,s,l" or fields="-p,-d,-g,-s,-l" or fields=['-p','-s','-v']
def getOpts(fields="-p,-d,-g,-s,-l", key_value='', full=False):

	if type(fields) == str:
		fields_to_transform = [x.strip().replace('-','') for x in fields.split(',')]
	else:
		fields_to_transform = [x.strip().replace('-','') for x in fields]

	cfgShort, cfgFull = {}, {}

	if 'p' in fields_to_transform:
		cfgFull[ _abbr['p'] ] = ps_function_type
		cfgShort['p'] = ps_function_type

	if 'd' in fields_to_transform:
		cfgFull[ _abbr['d'] ] = ds_function_type
		cfgShort['d'] = ds_function_type

	if 'g' in fields_to_transform:
		cfgFull[ _abbr['g'] ] = sig_function_type
		cfgShort['g'] = sig_function_type

	if 's' in fields_to_transform:
		cfgFull[ _abbr['s'] ] = smoothing_type
		cfgShort['s'] = smoothing_type

	if 'l' in fields_to_transform:
		cfgFull[ _abbr['l'] ] = min_count
		cfgShort['l'] = min_count

	cfg = cfgShort if not full else cfgFull

	return [str(x)+key_value+str(cfg[x]) for x in sorted(cfg.keys())]

color_for = {
	bool:
	{
		False: 'r',
		True: 'g'
	},
	str:
	{

	},
	list:
	{

	},
	dict:
	{

	}
}


def print_confirm(confirm_msg, bar=40, halt=True):
	for msg in confirm_msg:
		msg = list(msg)
		if len(msg) > 1:
			for i in range(len(msg)-1):
				if type(msg[i+1]) == bool:
					if msg[i+1] == False:
						msg[i+1] = color.render(str(msg[i+1]), color_for[bool][False])
					else:
						msg[i+1] = color.render(str(msg[i+1]),color_for[bool][True])

		if len(msg) == 3 and type(msg[2]) == dict:
			print >> sys.stderr, msg[0], ':', msg[1], msg[2][msg[1]]
		elif len(msg) == 3 and type(msg[2]) == str:
			print >> sys.stderr, msg[0], ':', msg[1], msg[2]
		elif len(msg) == 2:
			print >> sys.stderr, msg[0], ':', msg[1]
		else:
			print >> sys.stderr, msg

	print >> sys.stderr, '='*bar

	if halt:
		print >> sys.stderr, 'press any key to start...', raw_input()	

def help(program, args=[], addon=[], exit=1):

	params = {}
	record = ['p','d','g','s','l'] # record the option of ps_function, ds_function, sig_function, smoothing and limit

	params['-p'] = [
		'-p, --ps_function: pattern scoring function',
		'                 0: (default) no distribution information, only consider occurrence portion',
		'                 1: combine occurrence with distribution information using standard deviation scaling [2014.03.18]',
		'                 2: average occurrence with weight [2014.04.09]']

	params['-d'] = [
		'-d, --ds_function: document scoring function',
		'                 0: (default) arithmetic mean',
		'                 1: geometric mean']

	params['-g'] = [
		'-g, --sig_function: significance function',
		'                 0: (default) sf = 1, i.e., remain origin pattern score',
		'                 1: sf = ( pattern length )',
		'                 2: sf = ( 1/sentence length )',
		'                 3: sf = ( pattern length/sentence length )']

	params['-s'] = [
		'-s, --smoothing: smoothing method',
		'                 0: (default) no smoothig',
		'                 1: awesome smoothing (+0.25)']

	params['-l'] = [
		'-l, --limit: minimum occurrence of a pattern',
		'              	  0: (default) collect all patterns',
		'                 n: at least occurs < n > times for each pattern']

	params['-o'] = [
		'-o, --overwrite: overwrite the destination file (or mongo database)']

	params['-v'] = [
		'-v, --verbose: show debug message']

	#########################################################################################################
	## document feature extraction
	
	params['-b'] = [
		'-b, --begPercentage: percentage of beginning section']
	
	params['-m'] = [
		'-m, --midPercentage: percentage of middle section']
	
	params['-e'] = [
		'-e, --endPercentage: percentage of ending section']
	
	params['-c'] = [
		'-c, --countingUnitType: counting unit for document segmentation',
		'                 0: number of words',
		'                 1: number of sentences (not implemented yet)']
	
	# params['-f'] = [
	# 	'-f, --featureValueType: feature value computation',
	# 	'                 0: pattern scores (patscore_p2_s0)', 
	# 	'                 1: accumulated threshold by 0.68 (1 standard diviation) using pattern scores',
	# 	'                 2: accumulated threshold by 0.68 (1 standard diviation) using pattern occurrence',
	# 	'                 3: same as type 2 but ignore those with total occurrence < 4 (1, 2, 3)']

	#########################################################################################################
	
	opts = opt_fields['default'] if program not in opt_fields else opt_fields[program]

	## add all self-defined option description
	# addon_opt: --setting
	# addon_description: ['--setting: specify a setting ID (e.g., 537086fcd4388c7e81676914)', ... ]
	for addon_opt, addon_description in addon:  
		params[ addon_opt ] = addon_description
		if addon_opt not in opts:
			opts.append( addon_opt )

	usage = ['\nusage:']
	usage += [program+'.py'] 
	usage += args
	usage += ['[-, -- options]\n']
	# usage += []
	print ' '.join(usage) + '='*50 + '\n[-, -- options]'

	# usage = '\nusage: python '+program+' '.join(args)+' [options]\n'
	params_str = '\n'.join(['\n'.join(params[opt]) + '\n' for opt in opts])


	# print >> sys.stderr, usage
	print >> sys.stderr, params_str

	if exit: sys.exit(exit)

