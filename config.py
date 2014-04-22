# -*- coding: utf-8 -*-
import sys

#### define program names
ds_name = 'document_scoring'
ps_name = 'pattern_scoring'
ev_name = 'evaluation'

## mongo setting
mongo_addr = 'doraemon.iis.sinica.edu.tw'
db_name = 'LJ40K'

## mongo collection name
co_emotions_name = 'emotions'
co_docs_name = 'docs'
co_pats_name = 'pats'
co_lexicon_name = 'lexicon'
co_results_name = 'NewRes'
co_patsearch_name = 'pats_trim'

## default
co_patscore_prefix = 'patscore'
co_docscore_prefix = 'docscore'

## to be setup
co_patscore_name = ''
co_docscore_name = ''

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

overwirte = False
verbose = False

topk = 1

opt_fields = {
	ps_name: ['-p','-s','-v', '-o'],
	ds_name: ['-p','-d','-s','-g','-l','-v', '-o'],
	ev_name: ['-p','-d','-s','-g','-l','-v', '-o']
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

def print_confirm(confirm_msg, bar=40, halt=True):
	for msg in confirm_msg:
		if len(msg) == 3 and type(msg[2]) == dict:
			print >> sys.stderr, msg[0], ':', msg[1], msg[2][msg[1]]
		elif len(msg) == 3 and type(msg[2]) == str:
			print >> sys.stderr, msg[0], ':', msg[1], msg[2]
		else:
			print >> sys.stderr, msg[0], ':', msg[1]

	print >> sys.stderr, '='*bar

	if halt:
		print >> sys.stderr, 'press any key to start...', raw_input()	

def help(program, exit=1):

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
		'-o, --overwirte: overwirte the destination mongo database']

	params['-v'] = [
		'-v, --verbose: show debug message']

	opts = opt_fields[program]

	usage = 'usage: python '+program+'.py [options]\n' + '='*50 + '\n[options]'
	params_str = '\n'.join(['\n'.join(params[opt]) + '\n' for opt in opts])


	print >> sys.stderr, usage
	print >> sys.stderr, params_str

	if exit: sys.exit(exit)

