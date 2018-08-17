import unittest
"""
Tests for stop finder, stop getter, and route selector
"""

class test(unittest.TestCase):
    

    def test_model_coverage(self):
        """
        Tests that there are models for every stop link
        So we have all of the models
        """
        print('testing model coverage')
        
        import os
        import json
        fails=0
        total = 0
        routes = json.loads(open('/home/student/db/resources/trimmed_routes.json','r').read())
        route = routes['15']
        
        
        for route in routes:
            for v_num,v in enumerate(routes[route]):
                failed_on_variation = False
                for i in range(1, len(v) -1 ):
                    total += 1
                    if not os.path.exists('/data/neural_models3/'+str(v[i])+'_'+str(v[i+1])+'.bin'):
                        fails+=1
                        failed_on_variation = True

                if failed_on_variation:
                    print(route,v_num)
                    f=open('failed_routes_log.log','a')
                    f.write(str(route)+'_'+str(v_num)+'\n')
                    f.close()

        print(total,fails)
        input()
        self.assertEqual(fails==0,True)        

    def test_build_network(self):
        """
        Tests that the network object can be built from scratch. Takes forever.
        """

        from dbanalysis.network import simple_network4
        import pickle
        import time
        t1 = time.time()
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
        end_time = time.time() - t1
        import datetime
        dt = datetime.datetime.now()
        f=open('report.txt','a')
        f.write('*******Test report for ' + str(dt) + '*******\n')
        f.write('Network object constructed and all timetables generated in ' + str(end_time) + 'seconds\n')
        f.close()
def main():
    unittest.main()

if __name__ == "__main__":
    main()
        
