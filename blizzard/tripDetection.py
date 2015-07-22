from math import pow, sqrt
from parameter import Parameter
from Data import Data
import trajectory

def calculate_module(data):
    sq_sum = 0
    for i in data:
        sq_sum += pow(i, 2)
    return sqrt(sq_sum)

class TripDetection:
    def __init__(self):
        # Parameters
        self.charging_current_limit = 5
        self.gyro_limit = 0.15
        self.min_number_of_values_over_limit = 25
        self.array_length = 90
        self.min_trip_length = 300 #s
        self.trip_started = False
        self.max_time_between_movement = 280 #s
        self.max_avg_speed = 30 #km/h

        # Declaring variables
        self.charging_currents = Parameter(self.array_length, self.charging_current_limit, self.min_number_of_values_over_limit)
        self.gyroscopes = Parameter(self.array_length, self.gyro_limit, self.min_number_of_values_over_limit)
        self.start_times = []
        self.end_times = []

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

    def detect_trips(self, dbc, imei, start_date, end_date):
        # Obtaining all the data from the DB
        query = "select * from imei{0} where stamp >= \"{1}\" and stamp <= \"{2}\" order by stamp".format(imei, start_date, end_date)
        for record in dbc.SQLSelectGenerator(query):
            # Setting the data required for the algorithm
            if record[self.charging_current_db] is not None:
                charging_current = Data(record[self.time_db], record[self.charging_current_db])
                self.charging_currents.add_data(charging_current)
            gyro_x = record[self.gyro_x_db]
            gyro_y = record[self.gyro_y_db]
            gyro_z = record[self.gyro_z_db]
            if gyro_x is not None and gyro_y is not None and gyro_z is not None:
                gyro_module = calculate_module([gyro_x, gyro_y, gyro_z])
                gyro = Data(record[self.time_db], gyro_module)
                self.gyroscopes.add_data(gyro)

            # If trip has not started we check current and
            if not self.trip_started:
                if not self.charging_currents.max_limit_reached() and self.gyroscopes.max_limit_reached():
                    print("trip started:", record[self.time_db])
                    self.start_trip(self.gyroscopes.get_min_time_over_limit())
            # Case when trip has started
            else:
                if self.charging_currents.max_limit_reached() or not self.gyroscopes.max_limit_reached():
                    print("trip ended:", record[self.time_db])
                    self.end_trip(record[self.time_db])
        self.validate_all_trips(dbc,imei)
        return self.start_times, self.end_times

    def validate_all_trips(self, dbc, imei):
        beta = 0.06
        for i, j in zip(self.start_times, self.end_times):
            time = (j - i).total_seconds()/3600
            _, _, _, _,distance, _, _ = trajectory.get_trajectory_information(dbc, imei, beta, [i], [j])
            if distance:
                speed = distance[0] / time
                if speed > self.max_avg_speed:
                    self.start_times.remove(i)
                    self.end_times.remove(j)

    def start_trip(self, start_time):
        self.trip_started = True
        self.tmp_start_time = start_time

    def end_trip(self, end_time):
        self.trip_started = False
        if self.validate_trip(end_time):
            # If there is at least one value saved, then check that trips do not overlap
            # If they overlap then join the trips together
            if len(self.end_times) > 0:
                if (self.tmp_start_time - self.end_times[-1]).total_seconds() > self.max_time_between_movement:
                    self.start_times.append(self.tmp_start_time)
                    self.end_times.append(end_time)
                else:
                    self.end_times[-1] = end_time
            else:
                self.start_times.append(self.tmp_start_time)
                self.end_times.append(end_time)
        self.tmp_start_time = 0

    def validate_trip(self, end_time):
        return (end_time - self.tmp_start_time).total_seconds() > self.min_trip_length
