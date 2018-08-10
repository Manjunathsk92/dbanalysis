import haversine
single_login_points = 10
boints_per_km = 10
df = get_user_data_from_data_base(user_id)
df = df[['timestamp','lat','lon']]
current_time = None
current_kms = 0
total_points = 0
for row in df.itertuples():
    
    if current_time is None:
        total_points += single_login_points
        current_location = (row[1],row[2])
        current_time = row[0]
    
    elif row[0] < current_time + 3600:
        # if more less than an hour since the user last checked in, award mileage points
        distance = haversine.haversine(current_location,(row[1],row[2])
        total_points += int(points_per_km) * distance
        current_location = (row[1],row[2])
        current_time = row[0]

    else:
        #if more than an hour, don't award mileage points as the user hasn't been on the bus in the interim
        total_points += single_login_points
        current_time = row[0]
        current_location = (row[1],row[2])


    
         
