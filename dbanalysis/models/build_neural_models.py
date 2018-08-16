"""
@diarmuidmorgan
Script used to build all linear models, and modelling missing or low scoring stop links based on the last available good data frame.
"""

import copy
from sklearn.neural_network import MLPRegressor as mlp
from sklearn.preprocessing import MinMaxScaler as mms
from sklearn.preprocessing import StandardScaler as ss    
    

def model_stop(df):
    #create a model from a dataframe  
    
    #df = pd.get_dummies(df,columns=['day'])
    #features = ['day_'+str(i) for i in range(0,7)]
    #for f in features:
    #    if f not in df.columns:
    #        df[f] = 0i
    df = df[df['traveltime'] > 0]
    X = df[df['traveltime'] < df['traveltime'].quantile(0.95)]
    X = df[df['traveltime'] > df['traveltime'].quantile(0.05)]
    features = ['rain','temp','hour','day']
    scaler_X = ss()
    X = scaler_X.fit_transform(df[features])
    scaler_Y = ss()
   
    Y_real = df['traveltime']
    Y = scaler_Y.fit_transform(df['traveltime'].values.reshape(-1,1))
    
    model = mlp().fit(X,Y)
    return model,X,features,scaler_X,scaler_Y,Y_real 


def model_route(route,variation,v_num):
    """
    Attempts to create models for every stop link in a route
    """
    good_data_frame = None
    good_distance = None
    global real_stops
    r_stops = []
    s_getter = stop_tools.stop_getter()
    for i in range(1, len(variation) - 1):
        print(route,i)
        stopA = str(variation[i])
        stopB = str(variation[i+1])
        if model_exists(stopA,stopB):
            if stopA in real_stops and stopB in real_stops[stopA]:
                rs = real_stops[stopA][stopB]
                good_data_frame = [rs[0],rs[1]]
                good_distance = s_getter.get_stop_distance(rs[0],rs[1])
                r_stops = [rs[0],rs[1]]
            else:
                good_data_frame = [stopA,stopB]
                good_distance = s_getter.get_stop_distance(stopA,stopB)
                r_stops = [stopA,stopB]
        else:
            
            df = stop_tools.stop_data(stopA,stopB)
            fail = False
            if df is None:
                fail = True
            elif df.shape[0] < 100:
                fail = True
            else:
                model,X,features,X_scaler,Y_scaler,Y_real = model_stop(df)
                if not validate_model(model,X,features,Y_scaler,Y_real):
                    fail = True
            
            if not fail:
                with open('/data/neural_models3/'+str(stopA)+'_'+str(stopB)+'.bin', 'wb') as handle:
                    d={'model':model,'X_scaler':X_scaler,'Y_scaler':Y_scaler}
                    pickle.dump(d,handle,protocol = pickle.HIGHEST_PROTOCOL)
                good_data_frame = [stopA,stopB]
                good_distance = s_getter.get_stop_distance(stopA,stopB)
                r_stops = [stopA,stopB]
                #if stopA not in real_stops:
                #    real_stops[stopA] = {}
                #if stopB not in real_stops[stopA]:
                #    real_stops[stopA][stopB] = r_stops
            else:
                #return to these routes earlier
                if good_data_frame is None:
                    return False
                else:
                    distance = s_getter.get_stop_distance(stopA,stopB)
                    # god dam error here, or not really tbh
                    if stopA not in real_stops:
                        real_stops[stopA] = {}
                    if stopB not in real_stops[stopA]:
                        real_stops[stopA][stopB] = r_stops
                        
                    df = stop_tools.stop_data(good_data_frame[0],good_data_frame[1])
                    df['traveltime'] = df['traveltime'] * (distance / good_distance)
                    model,X,features,X_scaler,Y_scaler,Y_real = model_stop(df)
                    with open('/data/neural_models3/'+str(stopA)+'_'+str(stopB) + '.bin','wb') as handle:
                        d={'model':model,'X_scaler':X_scaler,'Y_scaler':Y_scaler}
                        pickle.dump(d,handle,protocol = pickle.HIGHEST_PROTOCOL)
                    
            
    return True        
def validate_model(model,X,features,Y_scaler,Y_real):
    """
    Validates a model. Rejects those that give negative predictions, or overly large scores.
    Noticed a risk of neural models 'not reaching conversion' during the modelling process, which
    can lead to terrible results. This is a crude fix, of course.
    """
    preds = model.predict(X)
    preds = Y_scaler.inverse_transform(preds)
    if preds.min() < 0:
        return False
    elif metrics.r2_score(Y_real,preds) < 0:
        return False
    
    elif preds.max() > preds.mean() * 4 and preds.mean() > 600 :
        return False    
    else:
        return True

def write_error(error):
    """
    Writes an error (a route hasn't been modelled at all)
    """
    f = open('/data/neural_models3/errorlog.log','a')
    f.write(error)
    f.close()
    

def model_exists(stopA,stopB):
    """
    Checks if the model for a stop segment already exists.
    """
    model_dir = '/data/neural_models3'
    if os.path.exists(model_dir+'/'+str(stopA)+'_'+str(stopB)+'.bin'):
        return True
    else:
        return False

def stop_link_has_data(stopA,stopB):
    df = stop_tools.stop_data(str(stopA),str(stopB))


model_dir = '/data/neural_models3/'
import pickle
import os
from dbanalysis import stop_tools
from subprocess import call
call(['mkdir','/data/neural_models3'])
call(['touch',model_dir+'errorlog.log'])


import json
from sklearn import metrics
from sklearn.linear_model import LinearRegression as lr
import copy
import pandas as pd
real_stops = {}
fake_models = {}
count = 0
routes = json.loads(open('/home/student/dbanalysis/dbanalysis/resources/trimmed_routes.json','r').read())
for route in routes:
    
    for v_num,variation in enumerate(routes[route]):
        count +=1 
        print(route,v_num)
        print(count,'/',468,'\n\n')
        a=model_route(route,variation,v_num)
        if a == False:
            write_error('too few stops for ' + str(route) + '_' + str(v_num) + '\n')
        try:
            pass
        except:
            write_error('failed for ' + str(route) + '_' + str(v_num) + '\n')      
      


