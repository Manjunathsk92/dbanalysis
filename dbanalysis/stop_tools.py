"""
@diarmuidmorgan
Bunch of code for getting and prepping data about stops. Includes stop_finder and stop_getter classes.


"""
import haversine
import os
import pandas as pd
def b_dir():
    import os
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return BASE_DIR

def get_stop_link(stopA,stopB, src='file',merge_weather=False):
    
    """
    Almost redundant,or possibly still used by the Big Route Model. Use stop_tools.stop_data() instead
    Retrieves the data describing the link between two stops
    """
    import os
    import pandas as pd
    from dbanalysis import headers as hds
    if src== 'file':
        if not os.path.exists('/data/stops/'+str(stopA) +'/' + str(stopB) +'.csv'):
            print('Error - stop link data not on disk')
            return None
        else:
            df=pd.read_csv('/home/student/data/stops/'+str(stopA) +'/' + str(stopB) +'.csv', names=hds.get_stop_link_headers())
            df['stopA'] = stopA
            df['stopB'] = stopB
            len_df_1 = len(df)            
    elif src=='db':
        #insert method here for grabbing data from database
        pass
 
    if merge_weather:
        #merge data with weather data .csv
        weather = pd.read_csv('/home/student/data/cleanweather.csv')
        weather['date']=pd.to_datetime(weather['date'])
        weather['hour']=weather['date'].dt.hour
        weather['date']=weather['date'].dt.date
        df['dt']=pd.to_datetime(df['dayofservice'],format="%d-%b-%y %H:%M:%S")
        df['date']=df['dt'].dt.date
        df['hour']=df['actualtime_arr_from']//3600
        
        cols=['dayofservice', 'tripid', 'plannedtime_arr_from',
       'plannedtime_dep_from', 'actualtime_arr_from', 'actualtime_dep_from',
       'plannedtime_arr_to', 'actualtime_arr_to', 'routeid', 'stopA', 'stopB','hour', 'dewpt', 'msl', 'rain', 'rhum', 'temp', 'vappr',
       'wetb']
        a= pd.merge(df,weather,on=['date','hour'])[cols]
        len_df2 = len(a)
        print(len_df_1,len_df2)
        return a

    else:
        return df
    
class stop_getter():

    """
    Class for grabbing gtfs data about stops.
    Grabs their coordinates, the stops that they link to, the shape between them.
    Can calculate the real driving distance between stops based on the stop shapes.
    """

    def __init__(self):
        import pickle
        import json
        import haversine
        base_dir = b_dir() + '/dbanalysis/resources/'
        with open(base_dir+'trimmed_stops_shapes_map.pickle','rb') as handle:
            self.stops_map = pickle.load(handle)
        with open(base_dir+'new_stops_dict.bin','rb') as handle:
            self.stops_dict = pickle.load(handle)
    def get_stop_info(self,stop):
        """
        Return a stop's location, text description and the routes that it serves.
        """
        stop = str(stop)
        return self.stops_dict[stop]
    def get_stop_coords(self,stop):
        """
        Get the coordinates of a stop.
        """
        if stop in self.stops_dict:
           return {'lat':self.stops_dict[stop]['lat'],
                    'lon':self.stops_dict[stop]['lon']}

        else:
            return None

    def get_stop_links(self, stop):
        """
        Return all the stops that this stop links to. Not used.
        """
        if stop in self.stops_map:
            return [stop for stop in self.stops_map[stop]]
        else:
            return None

    def get_stop_distance(self,stop,link):
        """
        Calculate the distance for a stop link, either based on the coordiantes in its 'shape'
        Or failing that, just using the haversine distance between two points.
        """
        stop = str(stop)
        link = str(link)
        
        coords = self.get_shape(stop,link)
        if coords is not None:
            #if we have full shape coordinates for a the link, use these
          
            total_distance = 0
            for i in range(0, len(coords)-1):
                lat1 = coords[i]['lat']
                lon1=coords[i]['lon']
                lat2=coords[i+1]['lat']
                lon2=coords[i+1]['lon']
                total_distance += haversine.haversine((lat1,lon1),(lat2,lon2))
            return total_distance
        elif stop in self.stops_dict and link in self.stops_dict:
            #otherwise if we have the stop coordinates, use these
            a_data = self.stops_dict[stop]
            b_data = self.stops_dict[link]
            lat1=a_data['lat']
            long1 = a_data['lon']
            lat2=b_data['lat']
            long2 = b_data['lon']
            
            return haversine.haversine((lat1,long1),(lat2,long2))
        
        else:
            #otherwise just return nothing
            return None

    def get_shape(self,stopA,stopB):
        """
        Returns the shape of a stop link (a set of coordinates describing the route a bus travels
        between them).
        """
        stop = str(stopA)
        link = str(stopB)
        found_stops = True
        if stop in self.stops_map and link in self.stops_map[stop]:
          
            return [self.get_stop_coords(stop)]+self.stops_map[stop][link]\
                        + [self.get_stop_coords(link)]
        
        elif link in self.stops_map and stop in self.stops_map[link]:
            
            return list(reversed([self.get_stop_coords(link)] + self.stops_map[link][stop]\
                    + [self.get_stop_coords(stop)]))
             
        else:
            return None

    def get_shape_route(self,start_stop,end_stop,route_array):
        """
        Returns the entire shape of a route.
        """
        begin = route_array.index(int(start_stop))
        end = route_array.index(int(end_stop))
        output=[]
        distance = 0
        for i in range(begin,end):
            output += self.get_shape(str(route_array[i]),str(route_array[i+1]))
        for i in range(0,len(output)-1):
            distance += haversine.haversine((output[i]['lat'],output[i]['lon']),\
                                        (output[i+1]['lat'],output[i+1]['lon']))    
            
        return {'shape':output,'distance':distance}

    def routes_serving_stop(self,stop):
        """
        Returns all of the route variations that a stops serves.
        """
        return {'routes':self.stops_dict[str(stop)]['serves']}
    
class stop_finder():

    """
    Class for finding the closest stops to a given {lat,lng} location.
    Uses a pickle file of nested clusters and cluster centres.
    Should add method for calculating actual distance to closest stops with google distance matrix.
    """

    def __init__(self):
        import pickle
        with open(b_dir()+'/dbanalysis/resources/stop_clusters.pickle','rb') as handle:

            self.clusters = pickle.load(handle)
        import haversine
        from math import inf
        import json
        self.stops_dict = json.loads(open(b_dir()+'/dbanalysis/resources/stops_trimmed.json','rb').read())

    def find_closest_stops(self,lat,lon):
        """
        Recursively work through the clustered file until a group of stops close to the user is found.
        Should run in basically O(1) time as the nested clusters only go three or four deep.
        Distance only has to be calculated to 30 cluster centers.
        """
        from math import inf 
        clusters = self.clusters
        while True:
            min_distance=inf
            for cluster in clusters:
                # find the closest cluster centre to the given location.
                dist=haversine.haversine((lat,lon),(cluster['lat'],cluster['lon'])) 
                if dist< min_distance:
                    min_distance = dist
                    best_group = cluster
            
            # if we have reached the bottom, return the actual stops.
            if 'nodes' in best_group:
                return [{'stop_id':i,\
                'info':self.stops_dict[str(i)],\
                'distance':haversine.haversine((lat,lon),\
                 (self.stops_dict[str(i)]['lat'],\
                 self.stops_dict[str(i)]['lon']))}\
                 for i in best_group['nodes']]
            
            else:
                clusters = best_group['clusters']

    def rank_closest_stops(self,lat,lon):
        #never completed
        from operator import itemgetter
        cluster = self.find_closest_stops(lat,lon)
        cluster = sorted(cluster,key=itemgetter('distance'))
    
    def best_stop(self,lat,lon):
        #never used
        cluster = rank_closest_stops(lat,lon)
        return cluster[0]
        

#functions for retrieving and prepping data on a random stop

def random_stop_data():
    """
    Retrieves and preps the data on a random stop.

    Weather data seems to include NaN values.
    """
    a,fromstop,tostop=random_stop_file()
    if a is None:
        return None
    weather = pd.read_csv('/home/student/dbanalysis/dbanalysis/resources/cleanweather.csv')
    weather['dt']=pd.to_datetime(weather['date'])
    weather['hour']=weather['dt'].dt.hour
    weather['date']=weather['dt'].dt.date
    df=prep_test_stop(a,weather,fromstop,tostop)
    return df


def random_stop_file():
    """
    Returns a random stop link file name.
    """
    import random
    stop_dirs=os.listdir('/home/student/data/stops')
    stop = random.choice(stop_dirs)
    c=os.listdir('/home/student/data/stops/'+stop)
    for i in c:
        if i != 'orphans.csv':
            return '/home/student/data/stops/'+stop+'/'+i, stop, i.split('.')[0]
    return None,None,None

def stop_data(fromstop,tostop):
    """
    Retrieves data describing the chosen stop link.
    """
    import os
    weather = pd.read_csv('/home/student/dbanalysis/dbanalysis/resources/cleanweather.csv')
    weather['dt']=pd.to_datetime(weather['date'])
    weather['hour']=weather['dt'].dt.hour
    weather['date']=weather['dt'].dt.date
    if os.path.exists('/data/stops/'+fromstop+'/'+tostop+'.csv'):
        df=prep_test_stop('/data/stops/'+fromstop+'/'+tostop+'.csv',weather,fromstop,tostop)
        del weather
        return df
    else:
        return None

def prep_test_stop(filename,weather,fromstop,tostop):
    from dbanalysis import headers as hds
    s_getter = stop_getter()
    df=pd.read_csv(filename,names=hds.get_stop_link_headers())
    df['fromstop']=fromstop
    df['tostop']=tostop
    df['traveltime']=df['actualtime_arr_to']-df['actualtime_arr_from']
    df['distance'] = s_getter.get_stop_distance(fromstop,tostop)
    df['speed'] = df['distance'] / (df['traveltime']/3600)
   
    df['dt']=pd.to_datetime(df['dayofservice'],format= "%d-%b-%y %H:%M:%S")
    df['date']=df['dt'].dt.date
    df['day'] = df['dt'].dt.dayofweek 
    df['month'] = df['dt'].dt.month
    df['hour']=df['actualtime_arr_from']//3600
    df['year'] = df['dt'].dt.year
    weather.drop('dt', axis=1,inplace=True)
    df = pd.merge(df,weather, on=['date','hour'])
    del weather
    del s_getter
    return df.dropna()

def prep_test_stop_no_weather(filename,fromstop,tostop):
    from dbanalysis import headers as hds
    df['fromstop']=fromstop
    df['tostop']=tostop
    df['traveltime']=df['actualtime_arr_to']-df['actualtime_dep_from']
    df['dwelltime']=df['actualtime_dep_from']-df['actualtime_arr_from']
    df['distance'] = s_getter.get_stop_distance(fromstop,tostop)
    df['speed'] = df['distance'] / (df['traveltime']/3600)

    df['date']=pd.to_datetime(df['dayofservice'],format= "%d-%b-%y %H:%M:%S").dt.date
    df['hour']=df['actualtime_arr_from']//3600
    df['day'] = df['dt'].dt.dayofweek
    return df

#Method to get the travel time for missing link
#never used.
def get_missing_links_traveltime(prevstop, stop1, stop2, traveltime):
    if prevstop!='':
        previous_dist=stop_getter().get_stop_distance(prevstop, stop1)
        speed=previous_dist/traveltime
    else :
        # If traveltime for previous link is not available, calculate traveltime assuming a speed of 50km/hr.
        speed=0.0138
    current_link_distance=stop_getter().get_stop_distance(stop1, stop2)
    current_link_traveltime=current_link_distance/speed
    return current_link_traveltime







if __name__ == '__main__':
    b=stop_finder()
    print(b.find_closest_stops(53.3498,-6.2603))
    s=stop_getter()
    print(s.get_shape_route(6318,5190,[6318, 6319, 7246, 6320, 4594, 4595, 4596, 4563, 1218, 1270, 1272, 1273, 1274, 1275, 1276, 1277, 1219, 1220, 1221, 664, 665, 666, 667, 668, 614, 615, 616, 617, 618, 619, 675, 4415, 301, 4495, 5190]))
              
