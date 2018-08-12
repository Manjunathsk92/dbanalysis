from_directory = '/data/recovered_models'
to_directory = '/data/neural_models'
import os
from subprocess import call
neural_models = os.listdir(to_directory)
recovered = os.listdir(from_directory)
for f_name in recovered:

    if f_name not in neural_models:
        
        call(['cp',from_directory+'/'+f_name,to_directory+'/'+f_name])
