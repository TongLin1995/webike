__author__ = 'irios'
from math import pow, sqrt
from Parameter import Parameter
from Data import Data
from trajectory import get_trajectory_information

def calculate_effective_magnitude(data):
    sq_sum = 0
    for i in data:
        sq_sum += pow(i, 2)
    return sqrt(sq_sum)

class TripDetection:
    def __init__(self):
        # Parameters
        self.CHARGING_CURRENT_LIMIT = 4.8
        self.GYRO_LIMIT = 0.09
        self.LIN_ACCEL_LIM = 1

        self.MIN_NUMBER_OF_VALUES_OVER_LIMIT = 4
        self.ARRAY_LENGTH = 12
        self.MIN_TRIP_LENGTH = 300 #s
        self.TRIP_STARTED = False
        self.MAX_TIME_BETWEEN_MOVEMENT = 280 #s
        self.MAX_AVG_SPEED = 30 #km/h

        # Declaring variables
        self.charging_currents = Parameter(self.ARRAY_LENGTH, self.CHARGING_CURRENT_LIMIT, self.MIN_NUMBER_OF_VALUES_OVER_LIMIT)
        self.gyroscopes = Parameter(self.ARRAY_LENGTH, self.GYRO_LIMIT, self.MIN_NUMBER_OF_VALUES_OVER_LIMIT)
        self.lin_accels = Parameter(self.ARRAY_LENGTH, self.LIN_ACCEL_LIM, self.MIN_NUMBER_OF_VALUES_OVER_LIMIT)
        self.start_times = []
        self.end_times = []
        self.distances = []

        # Declaring temporary variable for trips
        self.tmp_start_time = 0

        # Defining positions of variables in DB
        self.time_db = 0
        # latGPS_db = 3
        # lenGPS_db = 4
        self.charging_current_db = 26
        self.gyro_x_db = 13
        self.gyro_y_db = 14
        self.gyro_z_db = 15
        self.lin_accel_x_db = 19
        self.lin_accel_y_db = 20
        self.lin_accel_z_db = 21

    def detect_trips(self, dbc, imei, start_date, end_date):
        # Obtaining all the data from the DB
        query = "select * from imei{0} where stamp >= \"{1}\" and stamp <= \"{2}\" and gyrox <> 0 and gyroy <> 0 and gyroz <> 0 order by stamp".format(imei, start_date, end_date)
        for record in dbc.SQLSelectGenerator(query):

            # Setting the data required for the algorithm
            # Setting the charging current
            if record[self.charging_current_db] is not None:
                charging_current = Data(record[self.time_db], record[self.charging_current_db])
                self.charging_currents.add_data(charging_current)
            # Setting the gyroscope
            gyro_x = record[self.gyro_x_db]
            gyro_y = record[self.gyro_y_db]
            gyro_z = record[self.gyro_z_db]
            if gyro_x is not None and gyro_y is not None and gyro_z is not None:
                gyro_magnitude = calculate_effective_magnitude([gyro_x, gyro_y, gyro_z])
                gyro = Data(record[self.time_db], gyro_magnitude)
                self.gyroscopes.add_data(gyro)
            # Setting the linear acceleration
            lin_accel_x = record[self.lin_accel_x_db]
            lin_accel_y = record[self.lin_accel_y_db]
            lin_accel_z = record[self.lin_accel_z_db]
            if lin_accel_x is not None and lin_accel_y is not None and lin_accel_z is not None:
                lin_accel_magnitude = calculate_effective_magnitude([lin_accel_x, lin_accel_y, lin_accel_z])
                lin_accel = Data(record[self.time_db], lin_accel_magnitude)
                self.lin_accels.add_data(lin_accel)

            # If trip has not started we check the battery is not charging and gyroscope or
            # linear accelerometer have detected movement
            if not self.TRIP_STARTED:
                if not self.charging_currents.max_limit_reached() and (self.gyroscopes.max_limit_reached() or self.lin_accels.max_limit_reached()):
                    if self.gyroscopes.get_min_time_over_limit():
                        self.start_trip(self.gyroscopes.get_min_time_over_limit())
                    elif self.lin_accels.get_min_time_over_limit():
                        self.start_trip(self.lin_accels.get_min_time_over_limit())
            # Case when trip has started
            else:
                if self.charging_currents.max_limit_reached() or (not self.gyroscopes.max_limit_reached() and not self.lin_accels.max_limit_reached()):
                    self.end_trip(record[self.time_db])
        self.calculate_distances(dbc, imei)
        if len(self.start_times) > 1:
            self.merge_trips()
        self.validate_all_trips(dbc,imei)
        return self.start_times, self.end_times, self.distances

    def calculate_distances(self, dbc, imei):
        BETA = 0.06
        for i, j in zip(self.start_times, self.end_times):
            time = (j - i).total_seconds()/3600
            _, _, _, _,distance, _, _ = get_trajectory_information(dbc, imei, BETA, [i], [j])
            if distance:
                self.distances.append(distance[0])
            else:
                self.distances.append(0)

    def merge_trips(self):
        tmp_start_times = []
        tmp_end_times = []
        tmp_distances = []
        merged = False
        for i in range(len(self.start_times) - 1):
            if (self.start_times[i + 1] - self.end_times[i]).total_seconds() < self.MAX_TIME_BETWEEN_MOVEMENT:
                # Merging if the trips are close in time (limit defined previously)
                # If the previous record was not merged, just add it to the lists of data
                if not merged:
                    tmp_start_times.append(self.start_times[i])
                    tmp_end_times.append(self.end_times[i + 1])
                    tmp_distances.append(self.distances[i] + self.distances[i + 1])
                # If the previous record was merged, modify the last record of the new lists of data (end time and dist)
                else:
                    tmp_end_times[-1] = self.end_times[i + 1]
                    tmp_distances[-1] = tmp_distances[-1] + self.distances[i + 1]
                # Saving the state as merged
                merged = True
            else:
                if not merged:
                    tmp_start_times.append(self.start_times[i])
                    tmp_end_times.append(self.end_times[i])
                    tmp_distances.append(self.distances[i])
                # Saving the state as not merged
                merged = False
            if i == len(self.start_times) - 1 and not merged:
                # If it is the last element in the list and it was not merged, add it to the new list
                tmp_start_times.append(self.start_times[-1])
                tmp_end_times.append(self.end_times[-1])
                tmp_distances.append(self.distances[-1])
        # Replace the temporary data in the data of the object
        self.start_times = tmp_start_times
        self.end_times = tmp_end_times
        self.distances = tmp_distances

    # Validate that duration, avg speed and distance are within the limits
    def validate_all_trips(self, dbc, imei):
        tmp_start_times = []
        tmp_end_times = []
        tmp_distances = []
        for start_time, end_time, distance in zip(self.start_times, self.end_times, self.distances):
            time = (end_time - start_time).total_seconds()/3600
            speed = distance / time
            # In case when trip duration is longer than stablished AND avg speed and distances are over the limits
            # also, when distance is 0, the trip is saved because it means there is no GPS data available
            if ((distance > 0 and speed < self.MAX_AVG_SPEED) or distance == 0) and self.validate_trip_duration(start_time, end_time) and time < 2:
                tmp_distances.append(distance)
                tmp_start_times.append(start_time)
                tmp_end_times.append(end_time)
        # Replace the temporary data in the data of the object
        self.start_times = tmp_start_times
        self.end_times = tmp_end_times
        self.distances = tmp_distances

    def start_trip(self, start_time):
        self.TRIP_STARTED = True
        self.tmp_start_time = start_time

    def end_trip(self, end_time):
        self.TRIP_STARTED = False
        self.start_times.append(self.tmp_start_time)
        self.end_times.append(end_time)
        self.tmp_start_time = 0

    def validate_trip_duration(self, start_time, end_time):
        return (end_time - start_time).total_seconds() > self.MIN_TRIP_LENGTH