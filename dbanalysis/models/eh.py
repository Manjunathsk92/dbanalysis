import os
from subprocess import call
all_models = set(os.listdir('/data/neural_models'))
import json
routes = json.loads(open('/home/student/dbanalysis/dbanalysis/resources/trimmed_routes.json','r').read())
to_write = []
for r in routes:

    for v_num, variation in enumerate(routes[r]):

        for i in range(1,len(variation)-1):
            out = []
            stopA = str(variation[i])
            stopB = str(variation[i+1])
            if stopA+'_'+stopB+'.bin' not in all_models:
              out.append([stopA,stopB])
        if len(out) > 0:
            to_write.append([r,v_num,out])
            print([r,v_num,out])
