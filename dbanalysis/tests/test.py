import unittest
"""
Tests for stop finder, stop getter, and route selector
"""
class test(unittest.TestCase):
    import pickle
    def test_stop_finder(self):
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

    def test_shape_getter(self):
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
def main():
    unittest.main()

if __name__ == "__main__":
    main()
        
        
