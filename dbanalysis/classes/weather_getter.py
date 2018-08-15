#class to get the weather details
import mysql.connector
import pandas as pd

class weather_getter():
   
    def __init__(self):
        db_connection = mysql.connector.connect(user='dublinbus', password='Ucd4dogs!',
                                  host='127.0.0.1',
                                 database='researchpracticum')
        self.weather_5days=pd.read_sql('select date, rain, temp, vappr, rhum, msl from dublinBus_weatherforecast', con=db_connection)

    
    def get_weather(self):
        df_weather=self.weather_5days
        #print(df_weather)
        df_weather['date']=pd.to_datetime(df_weather['date'])
        #cols=['weather_date', 'rain', 'temp', 'vappr', 'rhum', 'msl']
        #i=0
        #df_weather=pd.DataFrame(columns=cols)
        #for weather in self.weather_5days:
        #    df_temp=pd.DataFrame(columns=cols)
        #    df_date={'date':weather.weather_date}
        #    df_date=pd.to_datetime(df_date['date'])
        #    df_temp.loc[i]= [df_date, weather.rain, weather.temp, weather.vappr, weather.rhum, weather.msl]
        #    df_weather=df_weather.append(df_temp, ignore_index=True)
        df_weather.index=df_weather['date']
        df=df_weather.resample('1H').pad()
        df['day'] = df['date'].dt.dayofweek
        df['date'] = pd.to_datetime(df.index)
        df['hour'] = df['date'].dt.hour
        #print(df_resampled_data)
        #print(df_weather.shape)
        #print(df_resampled_data.shape)
        return df
