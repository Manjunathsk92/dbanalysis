import json
routes = json.loads(open('/home/student/dbanalysis/dbanalysis/resources/trimmed_routes.json','r').read())
graph = {}
weights = {}
from math import inf
for route in routes:

    for v in routes[route]:

        variation = v[1:]
        for i in range(len(variation)-1):

            stopA = str(variation[i])
            stopB = str(variation[i+1])
            if stopA not in graph:
                graph[stopA] = set()
            graph[stopA].add(tuple((stopB,route)))

            if stopB not in weights:
                weights[stopB] = {}
            weights[stopB][route] = [inf,inf,False]

import pickle
with open('graphobject.bin','wb') as handle:
    pickle.dump(graph,handle,protocol=pickle.HIGHEST_PROTOCOL)
handle.close()
with open('weightsobject.bin','wb') as handle:
    pickle.dump(weights,handle,protocol=pickle.HIGHEST_PROTOCOL)
        
