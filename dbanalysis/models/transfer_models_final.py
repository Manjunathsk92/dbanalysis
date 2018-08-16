"""
Transfers models into the right directory, if they're not there already
"""

from_directory = '/data/extra_neural_models3'
to_directory = '/data/neural_models3'
import os
from subprocess import call
neural_models = os.listdir(to_directory)
recovered = os.listdir(from_directory)
for f_name in recovered:

    if f_name not in neural_models:
        import pickle
        with open(from_directory+'/'+f_name,'rb') as handle:
            d = pickle.load(handle)
        handle.close()
        if 'multiplier' in d:
            print(d)
        
            call(['cp',from_directory+'/'+f_name,to_directory+'/'+f_name])
