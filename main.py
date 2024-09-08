import pandas as pd
import time


def getrouteinfo(origin_coord, destination_coord, target_speed_kph, acceleration, deceleration):
    # importing googlemaps module
    import googlemaps

    # Requires API key
    gmaps = googlemaps.Client(key="YOURMAPSAPIKEYHERE")

    # Get distance from google maps
    travelmode = "driving"
    my_dist = gmaps.distance_matrix(origin_coord, destination_coord, travelmode, units="metric")["rows"][0]["elements"][
        0]
    my_dist = my_dist["distance"]["value"]
    googlemaps_routelink = "https://www.google.com/maps/dir/?api=1&origin=" + str(origin_coord).replace(" ",
                                                                                                        "") + "&destination=" + str(
    destination_coord).replace(" ", "") + "&travelmode=" + travelmode



    # Steady state speed
    target_speed_kph = target_speed_kph
    # Convert target speed in km/h to m/s
    target_speed_mps = target_speed_kph / 3.6

    # Acceleration and deceleration in m/s
    acceleration = acceleration
    deceleration = deceleration

    # Calculate acceleration phase
    accel_speed_mps = 0
    accel_travel_dist = 0
    accel_travel_time = 0
    while accel_speed_mps < target_speed_mps:
        accel_speed_mps = accel_speed_mps + acceleration
        accel_travel_dist = accel_travel_dist + accel_speed_mps
        accel_travel_time += 1

    # Calculate deceleration phase
    decel_speed_mps = target_speed_mps
    decel_travel_dist = 0
    decel_travel_time = 0
    while decel_speed_mps > 0:
        decel_speed_mps = decel_speed_mps - deceleration
        decel_travel_dist = decel_travel_dist + decel_speed_mps
        decel_travel_time += 1

    accel_decel_dist = accel_travel_dist + decel_travel_dist
    steadystate_dist = my_dist - accel_decel_dist
    if accel_decel_dist < my_dist:
        steadystate_dist = steadystate_dist
        steadystate_time = steadystate_dist / target_speed_mps
    else:
        steadystate_dist = 0
        steadystate_time = 0

    total_time = accel_travel_time + steadystate_time + decel_travel_time

    accel_speed_kph = round(accel_speed_mps * 3.6, 1)
    accel_travel_dist = round(accel_travel_dist)
    accel_travel_time = round(accel_travel_time)
    decel_speed_kph = round(decel_speed_mps * 3.6, 1)
    decel_travel_dist = round(decel_travel_dist)
    decel_travel_time = round(decel_travel_time)
    steadystate_dist = round(steadystate_dist)
    steadystate_time = round(steadystate_time)
    total_time = round(total_time)

    return (accel_speed_kph,
            accel_travel_dist,
            accel_travel_time,
            decel_speed_kph,
            decel_travel_dist,
            decel_travel_time,
            steadystate_dist,
            steadystate_time,
            total_time,
            googlemaps_routelink)

        #print("Accel phase target speed:", accel_speed_kph, "km/h")
        #print("Accel phase distance:", accel_travel_dist, "m")
        #print("Accel phase timing:", accel_travel_time, "secs")
        #print("Decel phase target speed:", decel_speed_kph, "km/h")
        #print("Decel phase distance:", decel_travel_dist, "m")
        #print("Decel phase timing:", decel_travel_time, "secs")
        #print("Steady state distance:", steadystate_dist, "m")
        #print("Steady state timing:", steadystate_time, "secs")
        #print("Total time:", total_time, "secs")


def getstopscoordinates(df_stops, stop_id):
    df_stop_id = df_stops.loc[df_stops["stop_id"] == stop_id]
    stop_id_lat = str(df_stop_id["stop_lat"].values[0])
    stop_id_lon = str(df_stop_id["stop_lon"].values[0])
    stop_id_coord = stop_id_lat + "," + stop_id_lon
    return stop_id_coord



# Speed Profile
steadystate_speed = 50
acceleration = 0.74
deceleration = 0.74

# Number of lines to read from Road Segments .csv file
increment = 100

# Load bus road segments
BusRoadSegments = "PortoBusRoadSegments.csv"
#df_RoadSegments = pd.read_csv(BusRoadSegments, nrows=10)
df_RoadSegments_Original = pd.read_csv(BusRoadSegments)

# Load bus stops info and organize
stops_file = "stops.txt"
df_Stops = pd.read_csv(stops_file)
# Concatenate latitude and longitude of each bus stop
df_Stops["stop_lat_long"] = df_Stops[["stop_lat", "stop_lon"]].apply(lambda x: ','.join(map(str, x)), axis=1)

# Read number of lines in df_RoadSegments
number_RoadSegments = len(df_RoadSegments_Original.index)

# Run loop every 100 Road Segments
number_RoadSegment_Loops = round(number_RoadSegments/increment, 0)
i = 1028 #ainda não corri com 1028
start_index = 0

while i < number_RoadSegment_Loops:
    start_index = i*increment
    end_index = start_index + increment - 1
    df_RoadSegments = df_RoadSegments_Original.iloc[start_index:end_index]
    # Add origin bus stops coordinates to dataframe
    df_RoadSegments = df_RoadSegments.merge(df_Stops[["stop_id", "stop_lat_long"]], left_on=["RoadSegmentOrigin"],
                                            right_on=["stop_id"], how="left")
    df_RoadSegments.rename(columns={"stop_lat_long": "OriginCoordinates"}, inplace=True)

    # Add destination bus stops coordinates to dataframe
    df_RoadSegments = df_RoadSegments.merge(df_Stops[["stop_id", "stop_lat_long"]], left_on=["RoadSegmentDest"],
                                            right_on=["stop_id"], how="left")
    df_RoadSegments.rename(columns={"stop_lat_long": "DestCoordinates"}, inplace=True)

    # Add calculated time based on Google Maps distance and speed profile
    df_RoadSegments[["GmapsTime", "GmapsRouteLink"]] = df_RoadSegments.apply(
        lambda x: getrouteinfo(x["OriginCoordinates"], x["DestCoordinates"], steadystate_speed, acceleration,
                               deceleration)[8:10], result_type="expand", axis=1)

    # Calculate potential time lost in each road segment
    df_RoadSegments["PotentialTimeLost"] = df_RoadSegments["planned_duration"] - df_RoadSegments["GmapsTime"]

    # Organize the data
    # Create column to identify road segment between two bus stops A-B
    df_RoadSegments["BusStopRoadSegment"] = df_RoadSegments[["RoadSegmentOrigin", "RoadSegmentDest"]].apply(
        lambda x: '-'.join(map(str, x)), axis=1)
    # Create column to identify the Bus Line
    df_RoadSegments["BusLine"] = df_RoadSegments["trip_id"].str.extract("^([^_]*_[^_]*)_.")
    if i == 0:
        df_RoadSegments.to_csv("Testfile.csv", header=True, index=False)
    else:
        df_RoadSegments.to_csv("Testfile.csv", header=False, index=False, mode="a")

    i += 1
    print("Loop number:", i)
    print("Number of total loops:", number_RoadSegment_Loops)
    print("Number of loops to finish:", number_RoadSegment_Loops-i)
    time.sleep(0.5)


# Drop not needed columns

#print(df_RoadSegments.head())