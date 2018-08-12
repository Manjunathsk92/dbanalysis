"""
So due to a big error in the script, a ton of models got dumped in with the linear models in the linear model directory.
Now is an attempt to find them....

"""
from subprocess import call
call(['mkdir','/data/recovered_models'])

base = '/data/linear_models3'
import os
import pickle
to_check = os.listdir(base)
for f_name in to_check:
    with open(base + '/' + f_name,'rb') as handle:
        d = pickle.load(handle)
    handle.close()
    if isinstance(d,dict):
       
        
        if d['model'].__class__.__name__ == 'MLPRegressor':
            print(d['model'])
            call(['cp',base+'/'+f_name, '/data/recovered_models/'+f_name])
            
