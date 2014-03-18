# -*- coding: utf-8 -*-

mongo_addr = 'doraemon.iis.sinica.edu.tw'

## mongo collection name
co_emotions_name = 'emotions'
co_lexicon_name = 'lexicon'
co_patscore_name = 'patscore'

## names of functions
ps_function_name = 'ps_function'
smoothing_method_name = 'smoothing'

## functions
ps_function = 0
smoothing_method = 0

## utils
def transform_cfg(cfg, key_value='=', parameters=','): return parameters.join([ str(x)+key_value+str(cfg[x]) for x in cfg ])