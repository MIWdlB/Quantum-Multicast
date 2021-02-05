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
                data = {field.strip(): np.array([], dtype=np.float32) for field in fields}
            
            elif index % 2 == 0:
                temp += line
            elif index % 2 == 1:
                temp += line
                for field, item in zip(fields, temp):
                    if item == "nan":
                        item = 0
                    item = float(item)
                    data[field.strip()] = np.append(data[field.strip()], item)
                temp = []

        print([key for key in data])
        print({i: j for i, j in zip(data["edge length"], data["mean_fidelity"])})
    return data

def plot_these(data: dict, x_axis: str, y_axis:str) -> None:
    x = data[x_axis]
    y = data[y_axis]

    assert len(x) == len(y)

    num_edges = data["number of edges"][0]
    fig = plt.figure()
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8]) # main axes
    ax.plot(x, y)
    title = f"edge:{num_edges} {x_axis} {y_axis}.jpg"
    ax.set_title(title)
    ax.set_xlabel(x_axis)
    ax.set_ylabel(y_axis)
    ax.set_xticks([0,1,2,3,4])
    ax.set_yticks([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    plt.show()
    plt.savefig(fname=f"data-{title}")

if __name__=="__main__":
    data = get_data()
    plot_these(data, "edge length", "mean_fidelity")
