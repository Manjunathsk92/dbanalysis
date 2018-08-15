import unittest
"""
Tests for stop finder, stop getter, and route selector
"""
class test(unittest.TestCase):
    import pickle
    def test_stop_finder(self):
        """
        Check that the stop finder returns clusters of nearest stops
        """
        import pickle
        from dbanalysis.stop_tools import stop_finder
        stop_finder = stop_finder()
        with open('/home/student/dbanalysis/dbanalysis/resources/new_stops_dict.bin', 'rb') as handle:
            stops = pickle.load(handle)
        handle.close()
        
        for i in range(100):
            
            s = stops.popitem()
            s= s[1]
            response = stop_finder.find_closest_stops(s['lon'],s['lat'])
            
            self.assertEqual(isinstance(response,list), True)
            for i in response:
                self.assertEqual('stop_id' in i,True)
                self.assertEqual('info' in i,True)
                self.assertEqual('lat' in i['info'],True)
                self.assertEqual('lon' in i['info'],True)

    def test_stop_getter(self):
        """
        Checks that the stop getter can return the shapes and get the distances between randomly popped stops
        """
        from dbanalysis.stop_tools import stop_getter
        import pickle
        s_getter = stop_getter()
        with open('/home/student/dbanalysis/dbanalysis/resources/new_stops_dict.bin','rb') as handle:
            stops = pickle.load(handle)
        handle.close()
        import json
        routes = json.loads(open('/home/student/dbanalysis/dbanalysis/resources/trimmed_routes.json','r').read())
        for i in range(20):
            r = routes.popitem()
            a = r[1]
            for v in a:
                arr = v[1:]
                stopA = arr[0]
                stopB = arr[-1]
                resp3 = s_getter.get_shape_route(stopA,stopB,arr)
                self.assertEqual('shape' in resp3,True)
                self.assertEqual('distance' in resp3,True)
                self.assertEqual(isinstance(resp3['distance'],int) or isinstance(resp3['distance'],float),True)
                self.assertEqual(isinstance(resp3['shape'],list),True)            
                for i in range(0, len(arr) -1):
                    resp = s_getter.get_stop_distance(arr[i],arr[i+1])
                    self.assertEqual(isinstance(resp,int) or isinstance(resp,float), True)
                    resp2 = s_getter.get_shape(arr[i],arr[i+1])
                    self.assertEqual(isinstance(resp2,list),True)
                    for i in resp2:
                        self.assertEqual(isinstance(i,dict),True)

    def test_route_selector(self):
        """
        Checks that the route_selector (used by django app), is returning routes, stops and variations as required
        Doesn't test that the routes are valid, but they must be as it's all based off the ones we saved.
        
      

        """
        from dbanalysis.classes import route_selector
        selector = route_selector.selector()
        all_routes = selector.return_all_routes()
        self.assertEqual(isinstance(all_routes,dict),True)
        self.assertEqual(len(all_routes['routes']) > 100,True)
        for r in all_routes['routes']:
            self.assertEqual(isinstance(r,str),True)
            self.assertEqual(isinstance(selector.return_variations(r),dict),True)
            for i in range(len(selector.return_variations(r)[r])):
                self.assertEqual(isinstance(selector.stops_in_route(r,i),list),True)    
                self.assertEqual(selector.get_unavailable(r,i) is True or selector.get_unavailable(r,i) is False,True)

        for pair in selector.unavailable_routes:
            self.assertEqual(selector.get_unavailable(pair[0],pair[1]),True) 
    
    def test_build_network(self):
        """
        Tests that the network object can be built from scratch. Takes forever.
        """
        return None
        from dbanalysis.network import simple_network4
        import pickle
        
        n = simple_network4.simple_network()
        
        n.prepare_dijkstra()
        n.properly_add_foot_links()
        n.generate_time_tables()
        for node in n.nodes:

            n.nodes[node].timetable.concat_and_sort()
        with open('/data/done2.bin','wb') as handle:
            pickle.dump(n,handle,protocol=pickle.HIGHEST_PROTOCOL)
        for node in n.nodes:
            self.assertEqual(len(n.nodes[node].timetable.data) > 0, True)
        del(n)
    def test_route_finder(self):
        
        """ 
        Tests that the route finder can find routes between random coordinates within dublin city.
        Takes forever to load the full network pickle.
        Currently, some routes seem to be unsolvable
        """
        return None
        import pickle
        from dbanalysis.network import simple_network4
        with open('/data/done2.bin','rb') as handle:
            n=pickle.load(handle)
        max_lat = 53.5
        import random
        import time
        import datetime
        min_lat = 53.1
        max_lon = -6.4
        min_lon = -6.2
        failed = 0
        for i in range(10):
            #feed 10 random sets of coordinates within dublin and test that the route finder can solve them
            #unfortunately. there's no way to really test the quality of the route
            o_lat = random.uniform(min_lat,max_lat)
            o_lon = random.uniform(max_lon,min_lon)
            o_lon = o_lon * -1
            d_lat = random.uniform(min_lat,max_lat)
            d_lon = -1 * random.uniform(max_lon,min_lon)
            dt = datetime.datetime.now()
            day = float(dt.weekday())
            start_time = random.uniform(9.0,23.0)
            begin_time = time.time()
            response = n.dijkstra(day,start_time,o_lat,o_lon,d_lat,d_lon)
            if not isinstance(response,dict):
                failed +=1
        self.assertEqual(failed/10 < 0.2,True)
        del(n)
    def check_predictions(self):
        """
        This is going to be hard because, rightly, some routes will break - 
        -there won't be valid predictions for those routes at the given time/.

        What we do here is we test every route variation. If there is a response, we validate 
        that the arrival time is greater than the departure time.

        If the response is None, then we add a failure.

        At the end, we validate that the percentage of failures is less than some given number (10%)

        """
        return None
        from dbanalysis.classes import route_selector
        selector = route_selector.selector
        # need to find a way to do this for more routes, and if the response isn't none, then compare 
        import pickle
        from dbanalysis.network import simple_network4
        with open('/data/done2.bin','rb') as handle:
            n=pickle.load(handle)
        import json
        with open('/home/student/db/resources/trimmed_routes.json','r') as handle:
            routes = json.loads(handle.read())
        handle.close()
        failed = 0
        total = 0
        for route in routes:
            for v_num,variation in enumerate(routes[route]):
                arr = variation[1:]
            
                stopA = str(arr[0])
                stopB = str(arr[-1])
                import datetime
                dt = datetime.datetime.now()
                day = dt.weekday()
                time = random.uniform(36000,72000)
                total += 1
                response=n.quick_predict(day,route,v_num,stopA,stopB,time)
                self.assertEqual(isinstance(response,np.ndarray) or response is None,True)
                if response is None:
            
                    failed +=1
                    continue
                dep=response[0]
                end = response[1]
                self.assertEqual(dep < end,True)   
        self.assertEqual(failed/total < 0.2,True)
        del(n)
    def test_timetables(self):
        """
        Check that every stop in the network has some kind of time table, that there's data in it,
        And that that data is sorted. Should also test cycling through routes and checking that the time tables are aligned properly
        e.g the actualtime_arr_to for stopA, will be the actualtime_arr_from for stopB

        As it's possible that some stops still don't have time tables, we validate that we reach an acceptable number,
        e.g 90% of stops have time tables. This is done by counting the total successes, over the full total.

        At the end of the tests we validate that this number is greater than 90%
        """
        return None
        import pickle
        import numpy as np
        from dbanalysis.network import simple_network4
        with open('/data/done2.bin','rb') as handle:
            n=pickle.load(handle)
        all_time_tables = 0
        with_data = 0 
        for node in n.nodes:
            self.assertEqual(hasattr(n.nodes[node],'timetable'),True)
            self.assertEqual(hasattr(n.nodes[node].timetable, 'data'),True)
            for day in n.nodes[node].timetable.data:

                for link in n.nodes[node].timetable.data[day]:

                    for route in n.nodes[node].timetable.data[day][link]:

                        self.assertEqual(isinstance(n.nodes[node].timetable.data[day][link][route],np.ndarray),True)      
                        # check that the time tables are in order
                        previous = 0
                        for row in n.nodes[node].timetable.data[day][link][route]:
                            self.assertEqual(row[0] < row[1],True)
                            self.assertEqual(row[0] >= previous,True)
                            previous = row[0]

                        #test retrieving time tables
                import datetime
                dt = datetime.datetime.now()
                all_time_tables +=1
                timetable = n.get_stop_time_table(node,dt)
                if len(timetable) > 0:
                    with_data +=1
       
                self.assertEqual(isinstance(timetable,list),True)
        self.assertEqual(with_data / all_time_tables > 0.9,True)
        del(n)
    def test_time_table_alignment(self):
        """
        test that routes can be reliably traversed using the time tables, and that they are properly aligned.
        Found a big problem here regarding route variations.
        """
        
        from dbanalysis.classes import route_selector
        selector = route_selector.selector
        # need to find a way to do this for more routes, and if the response isn't none, then compare
        import pickle
        import random
        from dbanalysis.network import simple_network4
        with open('/data/done2.bin','rb') as handle:
            n=pickle.load(handle)
        print(n)
        handle.close()
        import json
        with open('/home/student/db/resources/trimmed_routes.json','r') as handle:
            routes = json.loads(handle.read())
        handle.close()
        import datetime
        dt = datetime.datetime.now()
        day = int(dt.weekday())
        time = 36000
        fails = 0
        total = 0
        broken = 0
        for i in range(100):
            
            rs = [i for i in routes.keys()]
            route = random.choice(rs)
            
            try:
                variation = random.randint(0,len(routes[route])-1)
                total += 1
            except:
                continue
            array = routes[route][variation][1:]
            current_time = 0.0
            for i in range(0, len(array) -1):
                
                import numpy as np
                response=n.next_stop_route(day,current_time,str(array[i]),str(array[i+1]),route)
               
                if response is None:
                    fails+=1
                    break
                elif response[0] == 'broken':
                    broken += 1
                    continue
                self.assertEqual(response[0] <= response[1],True)
                self.assertEqual(response[1] > current_time, True)
                current_time = response[1]
        print('total failures',fails)
        print('total',total)
        print('total broken',broken)
        self.assertEqual(fails/total < 0.3,True) 
def main():
    unittest.main()

if __name__ == "__main__":
    main()
        
