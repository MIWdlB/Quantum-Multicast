"""Plot out data from datafiles."""
import csv
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint as print

def get_data()->None:
    """Plots the data"""
    
    datafile = "statistics.csv"

    with open(datafile) as file:
        reader = csv.reader(file, delimiter=",")

        fields = []
        data = {}
        temp = []

        # Header has passed read main data.
        for index, line in enumerate(reader):
            # HOT GARBAGE GO TO BED
            if index == 0 or index == 1:
                fields += line
                data = {field.strip(): [] for field in fields}
            
            elif index % 2 == 0:
                temp += line
            elif index % 2 == 1:
                temp += line
                for field, item in zip(fields, temp):
                    data[field.strip()].append(item)
                temp = []
        
        print([key for key in data])

    return data

def plot_these(data: dict, x_axis: str, y_axis:str) -> None:
    x = data[x_axis]
    y = data[y_axis]

    assert len(x) == len(y)

    num_edges = data["number of edges"][0]

    plt.plot(x, y)
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.savefig(fname=f"data-{num_edges}-{x_axis}-{y_axis}")

if __name__=="__main__":
    data = get_data()
    plot_these(data, "edge length", "mean_fidelity")
