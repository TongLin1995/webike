class Parameter:

    def __init__(self, length, min_value, min_number_values_over_limit):
        # Length of array of data
        self.length = length
        # Value of the parameter used to consider as part of trip
        self.min_value = min_value
        # Minimum number of values over the limit to consider as part of trip
        self.min_number_values_over_limit = min_number_values_over_limit
        # Array with the last n points
        self.data = []
        # Array with the last n averages
        self.averages = []
        # Average of the current data
        self.average = 0
        # Variance of the current data
        self.st_dev = 0
        # Number of values over the limit
        self.values_over_limit = 0

    def update_averages(self):
        # self.averages.append(self.average)
        # self.validate_length(self.averages)
        return

    def calculate_average(self):
        values = [i.value for i in self.data]
        total_sum = sum(values)
        self.average = total_sum / self.length
        self.update_averages()

    def add_data(self, new_value):
        self.data.append(new_value)
        self.validate_length_data()
        self.calculate_average()
        self.calculate_st_dev()

    def validate_length_data(self):
        if len(self.data) > self.length:
            deleted_value = self.data.pop(0).value
            self.update_values_over_limit(deleted_value)
        else:
            self.values_over_limit = 0
            for i in self.data:
                if i.value > self.min_value:
                    self.values_over_limit += 1

    def calculate_st_dev(self):
        # data_array = np.array(self.data)
        # self.st_dev = np.std(data_array)
        return

    def max_limit_reached(self):
        return self.values_over_limit > self.min_number_values_over_limit

    def get_min_time_over_limit(self):
        for i in self.data:
            if i.value > self.min_value:
                return i.time

    def get_max_time_over_limit(self):
        for i in reversed(self.data):
            if i.value > self.min_value:
                return i.time

    def update_values_over_limit(self, deleted_value):
        if deleted_value > self.min_value > self.data[-1].value:
            self.values_over_limit -= 1
        elif deleted_value < self.min_value < self.data[-1].value:
            self.values_over_limit += 1