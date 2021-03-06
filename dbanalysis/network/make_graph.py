"""
Script generates and saves a nested object describing every available route link in the dublin bus network.

Also generates a weights a 'weights' object, that stores the weights for every link.
"""

import json
routes = json.loads(open('/home/student/dbanalysis/dbanalysis/resources/trimmed_routes.json','r').read())
graph = {}
weights = {}
from math import inf
from dbanalysis import stop_tools
stop_getter = stop_tools.stop_getter()
for route in routes:

    for v in routes[route]:

        variation = v[1:]
        for i in range(len(variation)-1):

            stopA = str(variation[i])
            stopB = str(variation[i+1])
            if stopA not in graph:
                graph[stopA] = set()
            #every link/route pair is a tuple for the given stop
            graph[stopA].add(tuple((stopB,route)))
            #not included here, but walking nodes will also include the time taken to walk that distance
            if stopB not in graph:
                graph[stopB] = set()
            if stopB not in weights:
                weights[stopB] = {}
            #we have five fields here.
            #the first field is the total weight 
            #the second field is the number of transfers
            #the third feild is the amount of walking time
            #the fourth field is the total time taken
            #the last field represents whether this node has being visited or not
            weights[stopB][route] = [inf,inf,inf,inf,False]
        try:
            stopA = str(variation[-1])
            stopB = str(variation[-2])
            distance = stop_getter.get_stop_distance(stopB,stopA)
            weights[stopA]['w'] = [inf,inf,inf,inf,False]
            weights[stopB]['w'] = [inf,inf,inf,inf,False]
        
            if stopB not in graph:
                graph[stopB] = set()
                graph[stopB].add(tuple((stopA,'w',(distance/5) * 3600)))       
        except:
            print('why')
import pickle
with open('graphobject.bin','wb') as handle:
    pickle.dump(graph,handle,protocol=pickle.HIGHEST_PROTOCOL)
handle.close()
with open('weightsobject.bin','wb') as handle:
    pickle.dump(weights,handle,protocol=pickle.HIGHEST_PROTOCOL)
        
