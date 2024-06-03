import pandas as pd

class Loader:

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path, header=None)
        self.shape()


    def shape(self):
        self.rows, self.columns = self.df.shape


    def get_shape(self):
        return self.rows, self.columns