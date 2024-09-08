import pandas as pd

df = pd.read_csv("stop_times.csv")
result = pd.DataFrame()

for _, trip_df in df.groupby('trip_id', sort=False):  # type: str, pd.DataFrame
    trip_df = trip_df.sort_values('stop_sequence')
    trip_df['arrival_time'] = pd.to_timedelta(trip_df['arrival_time'])
    trip_df['departure_time'] = pd.to_timedelta(trip_df['departure_time'])

    trip_df['prev_arrival_time'] = trip_df['arrival_time'].shift()
    trip_df['prev_stop_id'] = trip_df['stop_id'].shift()

    #trip_df['RoadSegment'] = trip_df['prev_stop_id'].str.cat(trip_df['stop_id'], sep='-')
    trip_df['RoadSegmentOrigin'] = trip_df['prev_stop_id']
    trip_df['RoadSegmentDest'] = trip_df['stop_id']
    trip_df['planned_duration'] = trip_df['departure_time'] - trip_df['prev_arrival_time']

    trip_df = trip_df.dropna(subset=['planned_duration'])
    trip_df['planned_duration'] = (
        trip_df['planned_duration']
        .apply(lambda x: x.total_seconds())
        .astype(int)
    )

    result = pd.concat(
        [result, trip_df[['RoadSegmentOrigin', 'RoadSegmentDest', 'trip_id', 'planned_duration']]],
        sort=False,
        ignore_index=True,
    )

result.to_csv("PortoBusRoadSegments.csv", header=True, index=False)
