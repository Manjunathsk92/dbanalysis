import haversine
import time
from datetime import datetime
import pandas as pd
import mysql.connector
single_login_points = 10
points_per_km = 10
db_connection = mysql.connector.connect(user='dublinbus', password='Ucd4dogs!',
                                  host='127.0.0.1',
                                 database='researchpracticum')
df_all_users=pd.read_sql('select distinct user_id_id from dublinBus_userlocation', con=db_connection)
#print(df_all_users)
for user in df_all_users.itertuples():
    print("User id", user[1])
    user_id=user[1]
    total_distance=0
    df=pd.read_sql('select user_lat, user_lon, insert_timestamp from dublinBus_userlocation where user_id_id =%(user_id)s', con=db_connection, params={'user_id':user_id})
 #   print(df)
#df = get_user_data_from_data_base(user_id)
    df = df[['insert_timestamp','user_lat','user_lon']]
    current_time = None
    current_kms = 0
    total_points = 0
    for row in df.itertuples():
        #print("row0", row[0])
        #print("row1", row[1])
        #print("row2", row[2])
        #print("converting timestamp")
        datetime_string=str(row[1])
        time_string=datetime_string.split(' ')[1]
        time_split=time_string.split('.')[0]
        time_arr=time_split.split(':')
        time_of_day=(int(time_arr[0]) * 3600) + (int(time_arr[1]) * 60) + (int(time_arr[2]))
        
        if current_time is None:
            total_points += single_login_points
            current_location = (row[2],row[3])
            current_time = time_of_day
    
        elif time_of_day < current_time + 3600:
            # if more less than an hour since the user last checked in, award mileage points
            distance = haversine.haversine(current_location,(row[2],row[3]))
            total_distance+=distance
            total_points += int(points_per_km) * distance
            current_location = (row[2],row[3])
            current_time = time_of_day

        else:
            #if more than an hour, don't award mileage points as the user hasn't been on the bus in the interim
            total_points += single_login_points
            current_time = time_of_day
            current_location = (row[2],row[3])
    print("total points ",total_points)
    print("total distance ", total_distance)


    
         
