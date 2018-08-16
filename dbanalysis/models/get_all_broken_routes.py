"""
Scripts finds all models that weren't constructed during the first model building process.
Finds the closest existing model to them on a route. Calculates a multiplier based on the ratio of distance
for the existing stop link, versus that of the missing one. Opens the existing model, adds this distance multiplier,
to its object. Saves as a new model.

"""
import os
from subprocess import call
all_models = set(os.listdir('/data/neural_models3'))
import json
routes = json.loads(open('/home/student/dbanalysis/dbanalysis/resources/trimmed_routes.json','r').read())
to_write = []
for r in routes:

    for v_num, variation in enumerate(routes[r]):
        out = []
        for i in range(1,len(variation)-1):
            
            stopA = str(variation[i])
            stopB = str(variation[i+1])
            if stopA+'_'+stopB+'.bin' not in all_models:
              out.append([stopA,stopB])
        if len(out) > 0:
            to_write.append([r,v_num,out])
            print([r,v_num,out])
import pickle
with open('/home/student/dbanalysis/dbanalysis/models/missing_models.bin','wb') as handle:
    pickle.dump(to_write,handle,protocol=pickle.HIGHEST_PROTOCOL)
call(['mkdir','/data/extra_neural_models3'])
from dbanalysis import stop_tools
#its too late now to use the data frames. Going to copy the model and the multiplier
stop_getter = stop_tools.stop_getter()
for array in to_write:

    missing = array[2]
    r = array[0]
    v_num = array[1]
    route_array = routes[r][v_num]
    for pair in missing:
        stopA = pair[0]
        stopB = pair[1]
        best_pair = None
        from math import inf
        closest_index = inf
        found = False
        actual_index = route_array.index(int(stopA))
        for i in range(1,len(route_array)-1):
        
            if str(route_array[i])+'_'+str(route_array[i+1]) + '.bin' in all_models:
                if abs(actual_index - i) < closest_index:
                    found = True
                    closest_index = i
                    best_pair = [route_array[i],route_array[i+1]]

        if found:
            try:
                with open('/data/neural_models3/'+str(best_pair[0])+'_'+str(best_pair[1])+'.bin','rb') as handle:
                    d = pickle.load(handle)
                handle.close()
            except:
                with open('/data/extra_neural_models3/'+str(best_pair[0])+'_'+str(best_pair[1])+'.bin','rb') as handle:
                    d = pickle.load(handle)
                handle.close()
           
 
            model_distance = stop_getter.get_stop_distance(str(best_pair[0]),str(best_pair[1]))
            actual_distance = stop_getter.get_stop_distance(str(stopA),str(stopB))
            d['multiplier'] = actual_distance / model_distance
            with open('/data/extra_neural_models3/'+str(stopA)+'_'+str(stopB)+'.bin','wb') as handle:
                pickle.dump(d,handle,protocol=pickle.HIGHEST_PROTOCOL)
            all_models.add(str(stopA)+'_'+str(stopB)+'.bin')
            handle.close()
            print('model imputed')

    
    
