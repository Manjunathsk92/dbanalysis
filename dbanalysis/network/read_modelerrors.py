import json
f = open('modelerrors.log','r')
errors = f.read()
f.close()
errors = errors.split('\n')[:-1]
full_set = set()
data = {}
for error in errors:
    
    item = json.loads(error)
    item = item['error']
    full_set.add((item[0],item[1]))
    if item[0] not in data:
        data[item[0]] = {}
    if item[1] not in data[item[0]]:
        data[item[0]][item[1]] = [item[2],item[3]]
print(full_set)
print(len(full_set))
import pickle
with open('/home/student/dbanalysis/dbanalysis/resources/new_stops_dict.bin','rb') as handle:
    stops = pickle.load(handle)
handle.close()
string = ''
for i in data:

    for z in data[i]:
        
        thing = data[i][z]
        
        string += 'Ids:' + str(i) + '_' + str(z) + ' '
        string += 'From :' + stops[i]['stop_name']
        string += ' To :' + stops[z]['stop_name']
        string += ' Max prediction : ' + str(data[i][z][0])
        string += ' Mean prediction : ' + str(data[i][z][1]) + '\n'

f = open('modelerrors.txt','w')
f.write(string)
f.close()  


        
