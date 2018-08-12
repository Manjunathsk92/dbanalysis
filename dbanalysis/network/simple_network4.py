"""
@diarmuidmorgan
Network class (hopefully) used in final product.
Uses chained linear models.
Meant to serve as something like a singleton to the app.
Loads all of the required classes and tries to answer all app requests.
Includes working, fast, version of dijkstra

"""

import pandas as pd
from math import inf
from threading import Thread
class simple_network():
    """
    Simplified, faster, and more correct, version of the dublin bus network time dependant graph.
    """

    def __init__(self,build=True):
        """ 
        Gather all resources and set up the graph
        """
        import json
        self.routes = json.loads(open('/home/student/dbanalysis/dbanalysis/resources/trimmed_routes.json','r').read())       
        from dbanalysis.classes import neural_stop 
        from dbanalysis.stop_tools import stop_getter,stop_finder
        import pickle
        from dbanalysis.classes import route_selector
        from dbanalysis.classes import time_tabler_refac as time_tabler
        with open('/home/student/dbanalysis/dbanalysis/resources/new_stops_dict.bin','rb') as handle:
            self.stops_dict = pickle.load(handle)
        self.stop_getter = stop_getter()
        self.selector = route_selector.selector()
        self.stop_finder = stop_finder()
        self.time_tabler = time_tabler.time_tabler()
        #put unavailable_routes here
        self.unavailable_routes = []
        self.nodes = {}
        print(self.selector.unavailable_routes)
        if not build:
            return None
        count = 0
        import os
        all_models = set(os.listdir('/data/neural_models'))
        for route in self.routes:

            for v_num,variation in enumerate(self.routes[route]):

                #if self.selector.get_unavailable(route,v_num):
                #    print('unavailable',route,v_num)
                if 3 > 1000:
                    print('eh')   
                else:
                    for i in range(1, len(variation)-1):
                        stopA = str(variation[i])
                        stopB = str(variation[i+1])
                       
                            
                        distance = self.stop_getter.get_stop_distance(stopA,stopB)
                        if stopA not in self.nodes:
                        
                            stop_object = neural_stop.stop(stopA,self.stops_dict[stopA])
                            can=stop_object.add_link(stopB,distance)
                            if not can:
                                input('error')
                            stop_object.get_foot_links()
                            self.nodes[stopA] = stop_object
                            
                        else:
                            self.nodes[stopA].add_link(stopB,distance)
        print (count)
    def properly_add_foot_links(self):
        import pickle
        with open('/home/student/dbanalysis/dbanalysis/resources/transfers.bin','rb') as handle:
            transfers = pickle.load(handle)
        handle.close()
        for n in self.nodes:
            try:
                self.nodes[n].foot_links = {}
                self.nodes[n].serves = {i:[] for i in self.stops_dict[n]['serves']} 
                
            except:
                pass
        for stop in transfers:
            if stop in self.nodes:
                self.nodes[stop].foot_links = {}
                for stop2 in transfers[stop]:
                    
                    if stop2 in self.nodes:

                        self.nodes[stop].foot_links[stop2] = transfers[stop][stop2]
                        
         
    def prepare_dijkstra(self):
        """
        Ready graph to run dijkstra
        """
        self.graph_lock = False
        from math import inf
        for n in self.nodes:
            self.nodes[n].back_links = []
            self.nodes[n].switch_weight = inf
            self.nodes[n].weight = inf
            self.nodes[n].visited = False
            self.nodes[n].all_links = set()
            self.nodes[n].all_links = set(\
                            [i for i in self.nodes[n].links if i in self.nodes]\
                            + [i for i in self.nodes[n].foot_links if i in self.nodes])
    
    def run_route(self,matrix,pattern):
        """
        Runs all busses for a given day down their route pattern, saving time tables along the way.
        """
        
        #days = matrix['day']
        #matrix = pd.get_dummies(matrix,columns=['day'])
        #matrix['day'] = days
        matrix['actualtime_arr_to'] = matrix['actualtime_arr_from']
        
        #features = ['rain','temp','vappr','hour','hour2','hour3','hour4','day','day2','day3','day4']
        #count = 0
        #df = pd.DataFrame({'temp':[10],'vappr':[10],'rain':[0.08],'hour':[5],'day':[4]})
        #to_concat = []
        #import copy
        #for day in range(7):
        #    for hour in range(5,16):
        #        af = copy.deepcopy(df)
        #        af['day'] = day
                
        #        df['hour'] = hour
        #        to_concat.append(af)
        #matrix = pd.concat(to_concat,axis=0)
        #matrix['actualtime_arr_to'] = matrix['hour'] * 3600
        #matrix['actualtime_arr_from'] = matrix['hour'] * 3600 
        #matrix['routeid'] = '15'
        #for i in range(2,5):
        #    matrix['hour'+str(i)] = matrix['hour'] ** i
        #    matrix['day'+str(i)] = matrix['day'] ** i
        
        for i in range(0, len(pattern) -1):
            
            stopA = str(pattern[i])
            stopB = str(pattern[i+1])
            matrix = self.nodes[stopA].predict_multiple(matrix,stopB)
        
        del(matrix)

    def generate_time_tables(self):
        """
        Create all time tables for time dependant aspects of the graph.
        """
        from dbanalysis.classes import weather_getter
        self.total_routes = 0
        self.failed_routes = 0
        w_getter = weather_getter.weather_getter()
        weather = w_getter.get_weather()
        import datetime
        dt = datetime.datetime.now()
        count = 0
        for route in self.routes:
            if len(route) < 1:
                continue            
            times = self.time_tabler.get_dep_times_five_days(route,dt)
            
            for variation in times:
                self.total_routes +=1
                #if not self.selector.get_unavailable(route,int(variation)):
                try:    
                    count +=1
                    print(count,route+'_'+str(variation))
                    X=times[variation]
                    
                        # merge with weather data to add weather features.
                    #X['matrix'] = pd.merge(X['matrix'],weather[['day','hour','rain','temp','vappr']],on = ['day','hour'])
                    X['matrix']['rain']=0.08
                    X['matrix']['temp']=10.0
                    X['matrix']['vappr']=10.0
                    
                    
                    
                    self.run_route(X['matrix'],X['pattern'])
                    try:
                        pass
                    except Exception as e:
                        print(e)
                
                except Exception as e:
                    print(e)
                    self.failed_routes +=1
            try:
                pass    
            except Exception as e:
                
                print(e,'broken timetabler',route)
                pass
        
    def quick_predict(self,day,route,v_num,stopA,stopB,time):
        """
        Look up a prediction from a to b
        """
        # get the next departure at A        
        
        arr = self.routes[route][v_num][1:]
        start = arr.index(int(stopA))
        end = arr.index(int(stopB)) - 1
        link = str(arr[start+1])
        departure_time = self.nodes[str(stopA)].timetable.get_next_departure_route(day,link,time,route)[0]
        if departure_time is None:
            return None
        try:
            for i in range(start,end):
                resp = self.get_next_stop(str(arr[i]),str(arr[i]+1))
            
                resp = resp[0]
                if str(resp[2]) != route:
                    return None
            return resp[0],resp[1]    
        except:
            return None
    def get_next_stop(self,stopA,stopB,day,time):
        """
        Get first time and route from stopA to stopB for given day and arrival time at bus stop.
        """
        return self.nodes[stopA].timetable.get_next_departure(day,stopB,time)
    def get_get_next_departure_route(self,day,stopA,link,route,time):
        return self.nodes[stopA].timetable.get_next_route(day,link,route,time)
    
    def dijkstra(self,day,current_time,origin_lat,origin_lon,end_lat,end_lon,text_response=True):
        """
        Run all components of dijsktra's alogirthm on time dependant(ish) graph.
        """
        while self.graph_lock:
            #block if/while routefinding algorithm is already running. Not too sure how django works in relation to this.
            pass
        self.graph_lock = True
        self.add_user_nodes(origin_lat,origin_lon,end_lat,end_lon,current_time)
        solved = self.main_dijkstra(day,current_time)
        if not solved:
            return None
        else:
            response,stop_markers = self.walk_back_dijkstra(origin_lat,origin_lon,end_lat,end_lon,current_time)
            tear_down = Thread(target=self.tear_down_dijkstra)
            tear_down.start()
            if text_response:
                text = self.get_directions(response)
                return {'data':response,'text':text,'stop_markers':stop_markers}
            else:
                return {'data':response}

    def get_directions(self,resp):
        """
        Create readable text version of dijkstra response
        """
        text=[]
        current_route = 'walking'
        current_stop = resp[-1]
        time = current_stop['time']
        for i in range(len(resp)-2,-1,-1):
            if resp[i]['route'] != current_route or resp[i]['id'] == 'end':
                
                if current_route == 'walking' and resp[i]['id'] != 'end':
                       text.append('Walk from '+\
                                current_stop['data']['stop_name']\
                                + ' to '\
                                + resp[i]['data']['stop_name']\
                                +'.'+\
                                str((resp[i]['time']-time)//60)+\
                                ' minutes.')
                 
                elif resp[i]['id'] == 'end':
                    
                    text.append('Walk from '+ current_stop['data']['stop_name'] +\
                                 ' to destination. ' + str((resp[i]['time']-time)//60) + ' minutes.') 
                else:
                    text.append('Take the ' + current_route\
                                +' from '\
                                + current_stop['data']['stop_name']\
                                +' to '\
                                + resp[i]['data']['stop_name'] +'.'+\
                                str((resp[i]['time']-time)//60)+\
                                ' minutes.')

                current_route = resp[i]['route']
                current_stop = resp[i]
                time = current_stop['time']
        return text
    def dijkstra_shape(self,data):
        walking_bits = []
        bus_bits = []
        current_walking_bit = []
        current_bus_bit = []
        current_route = 'walking'
        for i in range(0,len(data)-1):
            if data[i]['route'] == 'walking':
                if current_route != 'walking':
                    current_route = 'walking'
                    bus_bits.append(current_bus_bit)
                    current_bus_bit = []
                shape = self.stop_getter.get_shape(data[i+1]['id'],data[i]['id'])       
                if shape is None:
                    current_walking_bit+=[{'lat':data[i]['data']['lat'],'lng':data[i]['data']['lon']},\
                                    {'lat':data[i+1]['data']['lat'],'lng':data[i+1]['data']['lon']}]
                else:
                    # this is blatantly wasteful here.
                    current_walking_bit += [{'lat':i['lat'],'lng':i['lon']} for i in list(reversed(shape))]
            else:
                
                if current_route == 'walking':
                    current_route = 'not walking'
                    walking_bits.append(current_walking_bit)
                    current_walking_bit = []
                try:
                    # again. Blatant waste
                    current_bus_bit += [{'lat':i['lat'],'lng':i['lon']} for i in\
                    list(reversed(self.stop_getter.get_shape(data[i+1]['id'],data[i]['id'])))]
                except:
                    pass
                    
        if current_bus_bit != []:
            bus_bits.append(current_bus_bit)
    
        elif current_walking_bit != []:
            i = len(data) - 1
            current_walking_bit.append({'lat':data[i]['data']['lat'],'lng':data[i]['data']['lon']})
            walking_bits.append(current_walking_bit)
        return {'bus':bus_bits,'walk':walking_bits}


        pass
        
    def main_dijkstra(self,day,current_time,walking_penalty=500,bus_penalty=500):
        """
        Actual implementation of dijkstra's algorithm on time dependant(ish) graph
        This is... legitimately... a disaster
        """
        
        import heapq
        from math import inf
        to_visit = []
        solved = False
        # the heap is sorted by the number of switches made, and the arrival time
        heapq.heappush(to_visit,[0,current_time,'begin','na'])
        while len(to_visit) > 0:
            x = heapq.heappop(to_visit)
            switch_number = x[0]
            current_time = x[1]
            current_node = x[2]
            print(current_node)
            current_route = x[3]
            if self.nodes[current_node].visited:
                continue
            self.nodes[current_node].visited = True
            self.nodes[current_node].weight = current_time
            if current_node == 'end':
                print(switch_number)
                solved = True
                break
            links = self.nodes[current_node].all_links
            
            for link in links:
                
                if self.nodes[link].visited:
                    continue

                

                if link in self.nodes[current_node].links:
                    resp = self.get_next_stop(current_node,link,day,current_time)
                    if resp is not None:
                        resp = resp[0] 
                        number = switch_number
                        if resp[2] != current_route:
                            number+=1
                        if number < self.nodes[link].switch_weight:
                            self.nodes[link].back_links.append([current_node,resp[2],resp[1],number])
                            heapq.heappush(to_visit,[number,resp[1],link,resp[2]])
                
                if link in self.nodes[current_node].foot_links:
                    time = self.nodes[current_node].foot_links[link] + current_time
                    number = switch_number
                    if current_route != 'w':
                        number += 1
                    if number < self.nodes[link].switch_weight:
                        self.nodes[link].back_links.append([current_node,'w',time,number])
                        heapq.heappush(to_visit,[number,time,link,'w'])
        return solved

    def walk_back_dijkstra(self,origin_lat,origin_lon,end_lat,end_lon,start_time):
        """
        Create a response object from solved graph
        """
        weight = self.nodes['end'].weight
        current_node = 'end'
        stop_markers = []
        output = [{'id':'end','route':'walking',\
                'data':{'lat':end_lat,'lon':end_lon,\
                        'name':'destination'},'time':weight}]
        stop_markers.append(output[0])
        current_route = 'walking'
        while weight > start_time:
        
            minweight = inf
          
              
            for link in self.nodes[current_node].back_links:
                stop_id = link[0]
                if self.nodes[stop_id].weight < minweight:
                    minweight = self.nodes[stop_id].weight
                    new_curnode = stop_id
                    route = link[1]
                    if route == 'w':
                        route = 'walking'
                    weight = minweight
             
            if new_curnode != 'begin':
                output.append({'data':self.stops_dict[new_curnode],\
                'id':new_curnode,\
                'route':route,\
                'time':weight})
            else:  
                output.append({'id':'begin','data':\
                {'lat':origin_lat, 'lon':origin_lon,'stop_name':'origin'},\
                'route':'walking',\
                'time':start_time})
            if route != current_route:
                current_route = route
                stop_markers.append(output[-1])
            current_node = new_curnode
            weight = minweight
        if output[-1] != stop_markers[-1]:
            stop_markers.append(output[-1])
        return output,stop_markers
    def add_user_nodes(self,origin_lat,origin_lon,end_lat,end_lon,start_time):
        """
        Temporarily add the user's origin and destination as dummy nodes on the graph.
        """
        self.closest_stops_to_origin = [stop for stop in\
                                self.stop_finder.find_closest_stops(origin_lat,origin_lon)\
                                if stop['stop_id'] in self.nodes]
        origin_stops = {}
        for stop in self.closest_stops_to_origin:
            origin_stops[stop['stop_id']] = stop['distance'] / 5
        
        self.closest_stops_to_destination = [stop for stop in\
                                    self.stop_finder.find_closest_stops(end_lat,end_lon)\
                                    if stop['stop_id'] in self.nodes]
        for stop in self.closest_stops_to_destination:
            self.nodes[stop['stop_id']].foot_links['end'] = stop['distance']/5
            self.nodes[stop['stop_id']].all_links.add('end')
        
        origin = dummy()
        origin.switch_weight = start_time
        origin.foot_links = origin_stops
        origin.all_links = [stop for stop in origin_stops]
        destination = dummy()
        destination.switch_weight = inf
        self.nodes['begin'] = origin
        self.nodes['end'] = destination
        
    def tear_down_dijkstra(self):
        """
        Run as thread. Resets the graph so dijkstra can be run again..
        """
        for node in self.nodes:
            self.nodes[node].back_links = []
            self.nodes[node].visited = False
            self.nodes[node].weight = inf
        for stop in self.closest_stops_to_destination:
            self.nodes[stop['stop_id']].foot_links.pop('end',None)
        del(self.nodes['end'])
        del(self.nodes['begin'])
        self.graph_lock = False
    def get_stop_time_table(self,stop,dt):
        """
        Concat link time tables,sort them, and pack them into dictionary objects.
        This code might be better placed inside the time table objects themselves?
        
        Returns times equal to or greater than the current time.
        """
        day = int(dt.weekday())
        import numpy as np
        import datetime
        timetables = self.nodes[str(stop)].timetable.data[day]
        timetables = np.concatenate([timetables[link] for link in timetables],axis=0)
        
        seconds = (dt - dt.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        timetables = timetables[timetables[:,0].argsort()]
        
        index = np.searchsorted(timetables[0:,0],seconds)
        if index > timetables.shape[0]:
            return None
        else:
            response = []
            
            for i in range(index,timetables.shape[0]):
                s = int(timetables[i,0]) % 86400
                
                response.append({'arrive':str(datetime.timedelta(seconds=s)),\
                                'route':timetables[i,2]})
            return response

class dummy():
    """
    Dummy node for user location and destination
    """
    
    def __init__(self):
        from math import inf
        self.weight = inf
        self.back_links = []
        self.foot_links = []
        self.all_links = []
        self.switch_weight = inf
        self.links = []
        self.visited = False                        

#import pickle
#n=simple_network()
#n.generate_time_tables()
#for node in n.nodes: 
#    try:          
#        n.nodes[node].timetable.concat_and_sort()
#    except:
#        pass
#import pickle
#with open('simple_network_concated','wb') as handle:
#    pickle.dump(n.nodes,handle,protocol=pickle.HIGHEST_PROTOCOL)
if __name__ == '__main__':
    #import pickle
    #n = simple_network()
    #with open('/data/neuraldump.bin','wb') as handle:
    #    import pickle
    #    pickle.dump(n,handle,protocol=pickle.HIGHEST_PROTOCOL)  
    #handle.close()
    #n=simple_network()
    #import pickle
    
    #with open('simple_network_dump.bin','rb') as handle:
    #    n=pickle.load(handle)
    #handle.close()
    import pickle
    #with open('/data/neuraldump.bin','rb') as handle:
    
    #handle.close()
    #n.generate_time_tables()
    #print(n.failed_routes,n.total_routes)
    n=simple_network(build=False)
    
    n.prepare_dijkstra()
    n.properly_add_foot_links()
    with open('/home/student/ResearchPracticum/django/dublinBus/static/neuraltimetabledump.bin','rb') as handle:
        n.nodes=pickle.load(handle)
    handle.close()


    n.prepare_dijkstra()
    n.properly_add_foot_links()
    print(n.dijkstra(6,54000,53.3786,-6.0570,53.3660,-6.2045))
    #import pickle
    #import pickle
    #with open('simple_network_dump.bin','rb') as handle:
    #   n= pickle.load(handle)
    #import datetime
    #from dbanalysis.classes import time_tabler_refac as time_tabler
    #for route in n.routes:
    #    for v_num,v in enumerate(n.routes[route]):
    #        can_run = True
    #        for i in range(1,len(v)-1):
    #            stopA = str(v[i])
    #            stopB = v[i+1]
    #            if (stopA not in n.nodes) or (stopB not in n.nodes[stopA].links):
    #                can_run = False
    #        if can_run:
    #            print(route,v_num)
    #            print(v)
    
    #n.generate_time_tables()        
    #with open('simple_network_with_tables.bin','wb') as handle:

    #    pickle.dump(n,handle,protocol=pickle.HIGHEST_PROTOCOL)
    #with open('simple_network_with_tables.bin','rb') as handle:
    #    n= pickle.load(handle)

    #for node in n.nodes:
    #    try:
    #        n.nodes[node].timetable.concat_and_sort()
            
            
    #    except Exception as e:
    #        print(e)
    #        pass
    #with open('timetables_dump.bin','wb') as handle:
    #    pickle.dump(n.nodes,handle,protocol=pickle.HIGHEST_PROTOCOL)
    #with open('simple_nAttributeError: Can't get attribute 'simple_network' on <module '__main__' from 'manage.py'>AttributeError: Can't get attribute 'simple_network' on <module '__main__' from 'manage.py'>ietwork_concated','wb') as handle:
    #    pickle.dump(n,handle,protocol=pickle.HIGHEST_PROTOCOL)             
   # import pickle
   # with open('simple_network_concated','rb') as handle:
   #     n = pickle.load(handle)
   # r15 = n.routes['15'][1]
   # a = r15[1]
   # b= r15[68]
   # print(n.quick_predict(5,'15',1,a,b,19*3600))
   # a = 15000000
    
    #for i in range (1,len(r15)-1):
        
    #    a=n.nodes[str(r15[i])].timetable.get_next_departure(4,str(r15[i+1]),a)[1]
    #    print(a) 
    
    #n.prepare_dijkstra()
    #import time
    #t1 = time.time()
    #resp=n.dijkstra(4,36000,53.3991,-6.2818,53.2944,-6.1339)
    #print(time.time()-t1)
    #input()
    #print(n.dijkstra_shape(resp['data']))
    #print(resp['stop_markers'])
    #import datetime
    #dt = datetime.datetime.now()
    #for node in n.nodes:

    #    input() 
    
#    print(n.get_stop_time_table(node,dt)) 
