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
        from dbanalysis.classes import time_tabler_refac2 as time_tabler
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
        from math import inf
        with open('/home/student/dbanalysis/dbanalysis/resources/transfers.bin','rb') as handle:
            transfers = pickle.load(handle)
        handle.close()
        for n in self.nodes:
            for foot_link in self.nodes[n].foot_links:
                time = self.nodes[n].foot_links[foot_link]
                if foot_link not in self.weights:
                    self.weights[foot_link] = {}
                self.weights[foot_link]['w'] = [inf,inf,inf,inf,False]
                if n not in self.graph:
                    self.graph[n] = set()
                self.graph[n].add(tuple((foot_link,'w',time)))
                 
        for stop in transfers:
            if stop not in self.graph:
                self.graph[stop] = set()
                
                for stop2 in transfers[stop]:
                    
                    
                    self.graph[stop].add(tuple((stop2,'w',transfers[stop][stop2])))
                    if stop2 not in self.weights:
                        self.weights[stop2] = {}
                    self.weights[stop2]['w'] = [inf,inf,inf,inf,False]
                    
                        
         
    def prepare_dijkstra(self):
        """
        Ready graph to run dijkstra
        """
        self.graph_lock = False
        from math import inf
        import pickle
        #load a graph object
        with open('/home/student/db/network/graphobject.bin','rb') as handle:
            self.graph = pickle.load(handle)
        handle.close()
        #load the graph weights
        with open('/home/student/db/network/weightsobject.bin','rb') as handle:
            self.weights = pickle.load(handle)
        handle.close()
        #most of the following code is deprecated since we switched to using the graph object.
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
        #for every step in the route, predict and update the dataframe
        for i in range(0, len(pattern) -1):
            
            stopA = str(pattern[i])
            stopB = str(pattern[i+1])
            #predictions are automatically stored in stop time tables
            matrix = self.nodes[stopA].predict_multiple(matrix,stopB)
        
        del(matrix)

    def generate_time_tables(self):
        """
        Create all time tables for time dependant aspects of the graph.
        """
        from dbanalysis.classes import weather_getter
        self.total_routes = 0
        self.failed_routes = 0
        # grab a five day weather forecast
        w_getter = weather_getter.weather_getter()
        weather = w_getter.get_weather()
        import datetime
        #get current datetime
        dt = datetime.datetime.now()
        count = 0
        # for every variation in every route, 
        for route in self.routes:
            if len(self.routes[route]) < 1:
                continue            
            times = self.time_tabler.get_dep_times_five_days(route,dt)
            # get a timetable describing every scheduled departure time for the first stop on that route
            # over the next five days
            if len(times) > len(self.routes[route]):
                continue
            for variation in times:
                self.total_routes +=1
                #if not self.selector.get_unavailable(route,int(variation)):
                try:    
                    count +=1
                    X=times[variation]
                    
                    #merge with weather data to add weather features.
                    #X['matrix'] = pd.merge(X['matrix'],weather[['day','hour','rain','temp']],on = ['day','hour'])
                    X['matrix']['rain']=0.08
                    X['matrix']['temp']=10.0
                    X['matrix']['vappr']=10.0
                    
                    
                    
                    self.run_route(X['matrix'],X['pattern'])
           
                #unfortunately, the routes in 'routes' and the routes in the time tabler differ slightly
                #the time table routes include a few variation we haven't managed to model.
                #these will break.
                #Unfortuntely, there wasn't time to properly address this problem.
                except Exception as e:
                    print(e)
                    self.failed_routes +=1
         
        
    def quick_predict(self,day,route,v_num,stopA,stopB,time):
        """
        Look up a prediction from a to b
        """
        # get the next departure at A        
        
        arr = self.routes[route][v_num][1:]
        
        start = arr.index(int(stopA))
        end = arr.index(int(stopB)) - 1
        
        link = str(arr[start+1])
        # look up the first arrival for a on this route that exceeds or equals the given time
        
        next_stop = str(arr[start+1])
        response = self.next_stop_route(day,time,str(stopA),str(next_stop),route)
        
        if response is None:
            return None
        departure_time = response[0]
        
        # Cycle through the route looking up the departure and arrival times for each stop segment
        #unfortunately this can still break occasionally, as we haven't properly sorted routes and variations
        # In addition, there might not be a next bus. In that case we return None and it is hanled by the
        # Django app.
        time = departure_time
        try: 
            for i in range(start,end):
             
                resp = self.next_stop_route(day,time,str(arr[i]),str(arr[i+1]),route)
            
            
                time = resp[1]
            return departure_time,resp[1]
           
        except Exception as e:
            print(str(e))
            
            return None
    def get_next_stop(self,stopA,stopB,day,time):
        """
        Get first time and route from stopA to stopB for given day and arrival time at bus stop.
        Method is redundant and should be deleted.
        """
        return self.nodes[stopA].timetable.get_next_departure(day,stopB,time)
    def get_get_next_departure_route(self,day,stopA,link,route,time):
        """
        Does the same, but only considers the next route
        """
        return self.nodes[stopA].timetable.get_next_route(day,link,route,time)
    
    def dijkstra(self,day,current_time,origin_lat,origin_lon,end_lat,end_lon,text_response=True):
        """
        Run all components of dijsktra's alogirthm on time dependant(ish) graph.
        """
        print('loading')
        #while self.graph_lock:
            #block if/while routefinding algorithm is already running. Not too sure how django works in relation to this.
        #    pass
        import copy
        #make copies of the graph and weight objects
        graph = copy.deepcopy(self.graph)
        weights = copy.deepcopy(self.weights)
        #graph lock is probably no longer necessary
        self.graph_lock = True
        #add user location and destination to the graph`
        graph,weights,finish_stops = self.add_user_nodes(origin_lat,origin_lon,end_lat,end_lon,current_time,graph,weights)
        #solve the graph
        solved,graph,weights,back_links = self.main_dijkstra(day,current_time,graph,weights,finish_stops)
        if not solved:
            #if no solution, will be handled as an error by Django app
            return None
        else:
            #walk back the route fastest route, creating a response object
            response,stop_markers = self.walk_back_dijkstra(origin_lat,origin_lon,end_lat,\
                                end_lon,current_time,graph,weights,back_links)
            #clean up the graph. Actually no longer necessary
            tear_down = Thread(target=self.tear_down_dijkstra)
            #tear_down.start()
            if text_response:
                #get a text response.
                text = self.get_directions(response)
                return {'data':response,'text':text,'stop_markers':stop_markers}
            else:
                return {'data':response}

    def get_directions(self,resp):
        """
        Create readable text version of dijkstra response.
        Code is unnecessarily complex. Basically just iterates through the response,
        Recording in text every time the route is switched (e.g from 'walking' to '15A')
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
        """
        Get the full route shape to be displayed by the frontend.
        Basically just cycles through the response, looking up the required shapes.
        """
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
        
    def main_dijkstra(self,day,start_time,graph,weights,finish_stops,time_weight=1,transfer_weight=4000,walking_weight=1,max_bus_wait=6000000000):
        """
        Actual implementation of dijkstra's algorithm on time dependant(ish) graph
        This is... legitimately... a disaster.
        In this implementation, every 'routeid' between stops essentially becomes its own edge and also its own node.
        A 'stop' becomes a point where a bunch of these nodes have connecting edges, and the time cost for them is 0
        Though there is a 'transfer' cost instead.
        In addition, this version basically optimizes for 'least transfers', and only uses 'time' as a tie breaker,
        when deciding what to pull out of the heap first.
        """
        
        import heapq
        from math import inf
        to_visit = []
        back_links = {}
        solved = False
        # the heap is sorted by the number of switches made, and the arrival time
        #in the heap, field 1 is the total weight
        #field 2 is the current time
        #field 3 is the number of transfers
        #field four is the amount of walking done
        #field five is the name of the node
        #field 6 is the route/travel method
        heapq.heappush(to_visit,[0,start_time,0,0,'begin','t-na'])
        while len(to_visit) > 0:
            #assign named variables to various attributes of this node
            w = heapq.heappop(to_visit)
            weight = w[0]
            current_time = w[1]
            transfers = w[2]
            walking_sections = w[3]
            current_node = w[4]
            current_route = w[5]
            
            if current_route[0] != 't': 
                ws = weights[current_node][current_route]
                visited = ws[4]
            else:
                visited = False
            if current_node == 'end':
                print('solved with',transfers,'transfers')
                print(weight,current_time,transfers,walking_sections)
                
                solved=True
                weights['end']['w'] = [weight,current_time,transfers,walking_sections,True] 
                break
            if visited or current_node not in graph:
                continue
                
            elif current_route[0]!= 't':
                weights[current_node][current_route][4] = True
             
            links = graph[current_node]
            if current_route[0] != 't':
                #push a transfer for this stop
                new_weight = ((current_time - start_time)*time_weight) + (transfers+1 * transfer_weight) + (walking_sections * walking_weight)
                heapq.heappush(to_visit,[new_weight,current_time,transfers+1,walking_sections,current_node,'t'+current_route])
            elif current_route [0] == 't':
                cant_take = current_route[1:]
            for link in links:
                link_name = link[0]
                walking = walking_sections
                number = transfers
                route = link[1]
                time = current_time
                if weights[link_name][route][4] or route == cant_take:
                    continue
                elif route == current_route or current_route[0] == 't':
                    if route == 'w':
                        time = current_time + link[2] + 5
                        if link[2] < 0:
                            pass
                        walking += link[2]
                    else:
                        time = self.next_stop_route(day,current_time,current_node,link_name,route)
                        if time is None:
                            continue
                        
                        elif time[1] - current_time > max_bus_wait:
                            continue
                        else:
                            time = time[1]
                            if time < current_time:
                                pass 
                else:
                    continue
                # here we need a proper formula to balance time,transfers, and walking sections      
                new_weight = ((time - start_time) * time_weight) + (number * transfer_weight) + (walking * walking_weight)
                
                if new_weight < weights[link_name][route][0] and new_weight > weight:
                    # here we need a proper formula for balancing walking sections, time travelled, and number of transfer
                    weights[link_name][route] = [new_weight,time,number,walking_sections,False] 
                 
                      
                    heapq.heappush(to_visit,[new_weight,time,number,walking,link_name,route])
                    route_to_write = current_route
                    if current_route[0] == 't':
                        route_to_write = current_route[1:]
                    if link_name and link_name not in back_links and link_name != current_node:
                        back_links[link_name] = {}
                        back_links[link_name] = {route:[current_node,weight,current_time,route_to_write]}
                    else:
                        back_links[link_name][route] = [current_node,weight,current_time,route_to_write]
        return solved,graph,weights,back_links

    def walk_back_dijkstra(self,origin_lat,origin_lon,end_lat,end_lon,start_time,graph,weights,back_links):
        """
        Create a response object from solved graph
        """
        transfer_weight = weights['end']['w'][0]
        time_weight = weights['end']['w'][1]
        
        current_node = 'end'
        stop_markers = []
        output = [{'id':'end','route':'walking',\
                'data':{'lat':end_lat,'lon':end_lon,\
                        'name':'destination'},'time':time_weight}]
        stop_markers.append(output[0])
        current_route = 'walking'
        print(transfer_weight)
        min_time_weight = time_weight
        min_transfer_weight = transfer_weight
        print(transfer_weight)
        previous_node = 'end'
        path = set()
        min_transfer_weight = inf
        for r in back_links[current_node]:
            if back_links[current_node][r][1] < min_transfer_weight:
                min_transfer_weight = back_links[current_node][r][1]
                r_name = r
        while transfer_weight > 0:
            #input()
            #print(current_node)
           
            link = back_links[current_node][r_name]
            #print(link)
                 
            stop_id = link[0]
            #print(current_node,stop_id)
            
           
            min_transfer_weight = link[1]
                    
            min_time_weight = link[2]
            new_curnode = stop_id
            route = r_name
            if route == 'w':
                route = 'walking'
            transfer_weight = min_transfer_weight
            time_weight = min_time_weight
            r_name = link[3]
            path.add(tuple((new_curnode,r_name)))
            if new_curnode != 'begin':
                output.append({'data':self.stops_dict[new_curnode],\
                'id':new_curnode,\
                'route':route,\
                'time':time_weight})
            else:  
                output.append({'id':'begin','data':\
                {'lat':origin_lat, 'lon':origin_lon,'stop_name':'origin'},\
                'route':'walking',\
                'time':start_time})
                break
            if route != current_route:
                current_route = route
                stop_markers.append(output[-1])
            
            previous_node = current_node
            current_node = new_curnode 
        if output[-1] != stop_markers[-1]:
            stop_markers.append(output[-1])
        return output,stop_markers
    def add_user_nodes(self,origin_lat,origin_lon,end_lat,end_lon,start_time,graph,weights):
        """
        Temporarily add the user's origin and destination as dummy nodes on the graph.
        """
        from math import inf
        self.closest_stops_to_origin = [stop for stop in\
                                self.stop_finder.find_closest_stops(origin_lat,origin_lon)\
                                if stop['stop_id'] in self.nodes]
        origin_stops = {}
        for stop in self.closest_stops_to_origin:
            origin_stops[stop['stop_id']] = stop['distance'] / 5
        
        self.closest_stops_to_destination = [stop for stop in\
                                    self.stop_finder.find_closest_stops(end_lat,end_lon)\
                                    if stop['stop_id'] in self.nodes]
        finish_stops = set()
        for stop in self.closest_stops_to_destination:
            finish_stops.add(stop['stop_id'])
            graph[stop['stop_id']].add(tuple(('end','w',stop['distance']/5)))
        weights['end'] = {'w':[inf,inf,inf,inf,False]}       
        weights['begin'] = {'w':[0,0,0,0,False]} 
        
        origin = dummy()
        origin.switch_weight = start_time
        origin.foot_links = origin_stops
        origin.all_links = [stop for stop in origin_stops]
       
        graph['begin'] = set()
        for stop in origin_stops:
            graph['begin'].add(tuple((stop,'w',origin_stops[stop])))
            weights[stop]['w'] = [inf,inf,inf,inf,False]
        return graph,weights,finish_stops
    
    def next_stop_route(self,day,time,stopA,stopB,route):
        return self.nodes[stopA].timetable.get_next(day,stopB,time,route)  
    
    def tear_down_dijkstra(self):
        """
        Run as thread. Resets the graph so dijkstra can be run again..
        Now redundant in this version of the network.
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
        # look up the time tables, and concatenate them
        timetables = self.nodes[str(stop)].timetable.data[day]
        to_concat = []
        for link in timetables:
            for route in timetables[link]:
                to_concat.append(timetables[link][route])
        
        if len(to_concat) == 0:
            
            return []
        
            
        timetables = np.concatenate(to_concat,axis=0)
        
        seconds = (dt - dt.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        #sort the time tables by arrival time
        timetables = timetables[timetables[:,0].argsort()]
        
        index = np.searchsorted(timetables[0:,0],seconds)
        # if there's no timetables information after the given time, return nothing
        if index > timetables.shape[0]:
            return []
        else:
            #pack the time table information into a response that Django can JSON serialize
            response = []
            
            for i in range(index,timetables.shape[0]):
                s = int(timetables[i,0]) % 86400
                
                response.append({'arrive':str(datetime.timedelta(seconds=s)),\
                                'route':timetables[i,2]})
            return response

class dummy():
    """
    Dummy node for user location and destination
    No longer used
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
    import pickle
    """
    Lots of code for testing the network. :)
    """
    BUILD=False
    if BUILD:
    
        n = simple_network()
    #with open('/data/neuraldump.bin','wb') as handle:
    #    import pickle
    #    pickle.dump(n,handle,protocol=pickle.HIGHEST_PROTOCOL)  
    #handle.close()
    #n=simple_network()
    #import pickle
    
    #with open('simple_network_dump.bin','rb') as handle:
    #    n=pickle.load(handle)
    #handle.close()
    #import pickle
    #with open('/data/neuraldump.bin','rb') as handle:
    
    #handle.close()
    #n.generate_time_tables()
    #print(n.failed_routes,n.total_routes)
    #n=simple_network(build=True)
    #n.generate_time_tables()
    #with open('/data/dddump.bin','wb') as handle:
    #    pickle.dump(n,handle,protocol=pickle.HIGHEST_PROTOCOL) 
    
    #n.properly_add_foot_links()
    #with open('/data/dddump.bin','rb') as handle:
    #    n=pickle.load(handle)
        n.prepare_dijkstra()
        n.properly_add_foot_links()
    #handle.close()
    #with open('/data/done.bin','rb') as handle:
    #    n=pickle.load(handle)
    #handle.close()
        n.generate_time_tables()
        for node in n.nodes:
    
            n.nodes[node].timetable.concat_and_sort()
        with open('/data/done.bin','wb') as handle:
            pickle.dump(n,handle,protocol=pickle.HIGHEST_PROTOCOL)
    
    with open('/data/done.bin','rb') as handle:
        n=pickle.load(handle)
     
    handle.close()
    #n.prepare_dijkstra()
    #n.properly_add_foot_links()
    #resp=n.dijkstra(3,46000,53.2828,-6.3177,53.3660,-6.2045)
    
    import json
    routes = json.loads(open('/home/student/db/resources/trimmed_routes.json','r').read())
    r15 = n.routes['15'][1]
    a = str(r15[1])
    b= str(r15[-1])
    print(n.quick_predict(3,'15',1,a,b,12*3600))
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
