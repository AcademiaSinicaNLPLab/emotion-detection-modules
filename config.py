# -*- coding: utf-8 -*-

mongo_addr = 'doraemon.iis.sinica.edu.tw'

## mongo collection name
co_emotions_name = 'emotions'
co_lexicon_name = 'lexicon'
co_patscore_name = 'patscore_test'

## names of functions
ps_function_name = 'ps_function'
ds_function_name = 'ds_function'
sig_function_name = 'ds_function'
smoothing_name = 'smoothing'

## functions
ps_function_type = 1
ds_function_type = 1
sig_function_type = 0
smoothing_type = 0
# epsilon = 0.5

## utils
def transform_cfg(cfg, key_value='=', parameters=','): 
	return parameters.join([ str(x)+key_value+str(cfg[x]) for x in sorted( cfg.keys() ) ])	}
