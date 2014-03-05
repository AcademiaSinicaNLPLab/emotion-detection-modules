# -*- coding: utf-8 -*-

### extract pattern according to differernt structure
import sys, os
# sys.path.append('/'.join([os.environ['PROJECT_HOME'],'pymodules']))

import color

from collections import defaultdict
from pprint import pprint

import pymongo, pickle
mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
db = mc['LJ40K']
co = db['patterns']

