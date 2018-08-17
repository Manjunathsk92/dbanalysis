"""
@diarmuidmorgan

Updated stop class to use MLPRegressor and scaling instead of linear models.
Acts as a holder for timetables and models. Has a method for predicting.
However, in our app, the models are never stored by network after time tables are generated.
Essentially this class is only used as a holder for it's timetable, after the models have being built.


"""
import pickle
from dbanalysis.classes.time_tabler_refac2 import stop_time_table
import copy
import pandas as pd
from sklearn.neural_network import MLPRegressor as mlp
from sklearn.neural_network import MLPRegressor as mlp
from sklearn.preprocessing import MinMaxScaler as mms
from sklearn.preprocessing import StandardScaler as ss
class stop():

    def __init__(self,stop_id,stop_info,write_errors=False):
        import os
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.stop_id = str(stop_id)
        self.stop_info = stop_info
        self.write_errors = True
        self.lat = stop_info['lat']
        self.lon = stop_info['lon']
        self.timetable = stop_time_table()
        self.links = set()
        self.Y_scalers = {}
        self.X_scalers = {}
        
        self.use_multipliers = {}
        self.multipliers = {}
        self.link_distances = {}
        self.foot_links = {}
        self.models = {}
    def add_link(self,link,distance):
        """
        Method to add a link. Loads both the link information and the models
        """
        
        if link not in self.links:
            try:
                with open(self.BASE_DIR+'/resources/models/neural_models3/'+self.stop_id+'_'+str(link)+'.bin','rb') as handle:
                    d = pickle.load(handle)
                handle.close()
                if 'multiplier' in d:
                    self.use_multipliers[str(link)] = True
                    self.multipliers[str(link)] = d['multiplier']
                else:
                    self.use_multipliers[str(link)] = False    
                self.models[str(link)] = d['model']
                self.Y_scalers[str(link)] = d['Y_scaler']
                self.X_scalers[str(link)] = d['X_scaler']
                del(d)
                self.links.add(str(link))
                self.link_distances[link] = distance
                return True
            except Exception as e:
                print(e) 
                print('no model for',self.stop_id,link)
                return False
        else:
            return True

    def predict_multiple(self,df,link):
        """
        Predicts travel time from this stop to its link.
        """
        features = ['rain','temp','hour','day']
        df['hour'] = df['actualtime_arr_to'] //3600
        df['actualtime_arr_from'] = df['actualtime_arr_to'] 
        X = self.X_scalers[link].transform(df[features])
        traveltime = self.models[link].predict(X)
        traveltime = self.Y_scalers[link].inverse_transform(traveltime)
        #if this model needs a multiplier, use it
        if self.use_multipliers[str(link)]:
            traveltime = traveltime * self.multipliers[str(link)]
        a=0
        if traveltime.min() <= 0:
            #should ideally just correct the inaccurate predictions, but this is going to have to suffice instead.
            print('number of predicts:',len(traveltime))
            #print('hours:',df['hour'].unique())
            print('number of negatives:', len(traveltime[traveltime < 0]))
            #print('mean traveltime:',traveltime.mean())
            #print('percent lees than zero:',len(traveltime[traveltime <0]) / (len(traveltime) + 1))
            if self.write_errors:
                #record this error in the log
                data = {'error':[self.stop_id, link,traveltime.min(),traveltime.mean()]}
                f=open('modelerrors.log','a')
                import json
                string = json.dumps(data)
                f.write(string + '\n')
                f.close()
             
            #print ( len(traveltime[traveltime < 0]))
            #correcting any negative predictions. Ideally replace with a non negative mean value.
            #Othersie, we use the distance and get the time using a speed of 30 miles an hour
            if len(traveltime[traveltime > 0]) > 0:
                
                m = traveltime[traveltime > 0].mean()
                traveltime[traveltime < 0] = m
            else:
                
                
                a = (self.link_distances[link] / 30) * 3600
                print(a)
                traveltime[traveltime < 0] = a  
        else:
            pass
        if max(traveltime) > 500:
            #print(traveltime.max(),traveltime.mean())
            #print('Obscene prediction for',self.stop_id,link)
            #input()
            print(self.link_distances[str(link)] / (traveltime.mean()/3600),traveltime.mean())
            data = {'error':[self.stop_id, link,traveltime.max(),traveltime.mean()]}
            f=open('modelerrors.log','a')
            import json
            string = json.dumps(data)
            #record this error in the log. We never found a way to fix the bad predictions
            f.write(string + '\n')
            f.close()
                
        df['actualtime_arr_to'] = df['actualtime_arr_from'] + traveltime
        del(traveltime)
        del(X)
        self.add_to_time_table(link,df[['day','actualtime_arr_from','actualtime_arr_to','routeid']])
        return df 
         
            
    def add_to_time_table(self,link,df):
        """
        Add data frame to this stop's time table
        """
        self.timetable.add_times(df,link)        
    
    def single_predict(self,row,link):
        """
        Method unused
        """
        features = ['rain','temp','vappr','hour','hour2','hour3','hour4','day','day2','day3','day4']
        row['hour'] = row['actualtime_arr_to'] //3600
        for i in range(2,5):
            row['hour'+str(i)] = row['hour'] ** i
        row['actualtime_arr_from'] = row['actualtime_arr_to']
        traveltime = self.models[str(link)].predict(row[features])
        row['actualtime_arr_to'] = row['actualtime_arr_from'] + traveltime
        row['hour'] = row['actualtime_arr_to'] // 3600
        return row, traveltime 
            
    def dump_time_tables(self):
        """
        Right now time tables are dumped en masse. To be implemented at a later data.
        """

        import pickle
        with open('/home/data/timetables/'+str(self.stop_id)+'.bin','wb') as handle:
            pickle.dump(self.timetable,handle,protocol = pickle.HIGHEST_PROTOCOL)

    def get_foot_links(self):
        """
        Super inefficient method. Finds the closest five stops to this stop and adds them as footlinks.
        The closesness of every stop was calculated in the stop_foot_distance.pickle.
        This method slows down networking building significantly, but we don't have time to change it.
        """
        import pickle
        import os
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(BASE_DIR+'/resources/stop_foot_distance.pickle','rb') as handle:
            foot_stops = pickle.load(handle)
        for x in foot_stops[str(self.stop_id)]:
            
            self.foot_links[x[0]] = (x[1]/5)*3600
    
        del(foot_stops)
