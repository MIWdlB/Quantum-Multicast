"""Plot out data from datafiles."""
import csv
import os
import re
from typing import Dict, List
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint as print
from datetime import date


def get_file_data(datafile) -> Dict:
    """Plots the data"""
    
    data = {}

    with open(datafile) as file:
        reader = csv.reader(file, delimiter=",")

        fields = []
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
                        item = None
                    else:
                        item = float(item)
                    data[field.strip()] = np.append(data[field.strip()], item)
                temp = []

    return data

def get_all_data() -> Dict:
    """Get all the data from all files."""

    files = os.listdir("data/")
    
    data = {}

    pattern = re.compile(pattern='nodes:(\d)')

    for file in files:
        num_nodes = pattern.search(file).groups()[0]
        num_nodes = int(num_nodes)

        data[num_nodes] = data.get(num_nodes, {})

        if "bipartite" in file:
            type = "bipartite"
        elif "multipartite" in file:
            type = "multipartite"
        else:
            raise NameError("Cannot parse network type from filename.")

        data[num_nodes][type] = get_file_data("data/" + file)

    return data


def plot_these(data: dict, type: str, num_nodes: List[int], measure: str) -> None:
    """Plot the data.
    
    Parameters
    ----------
    data : Dict
        A dict containg the data to be plotted.

    type : "bipartite", "multipartite", "comparison"
        The type of network to plot data for.

    num_nodes : List[int]
        A list of node quantities to plot data for.

    maesure : "fidelity" or "rate"
        The measure to plot data for.
    """
    networks = []
    #fig, ax = plt.subplots()
    #ax = fig.axes([0.1, 0.1, 0.8, 0.8]) # main axes

    if type in ["bipartite", "comparison"]:
        networks.append("bipartite")
    if type in ["multipartite", "comparison"]:
        networks.append("multipartite")
    
    if not networks:
        raise ValueError("'type' must be 'bipartite', 'multipartite' or 'comparison'")
    
    for network in networks:
        for num in num_nodes:
            # The data keys use 

            x = data[num][network]['edge length']

            if measure == "fidelity":
                datakey = "mean fidelity"
                stdkey = "fidelity std"
            elif measure == "rate":
                datakey = "entanglement rate"
                stdkey = "time std"
            else:
                raise ValueError("'measure' must be 'fidelity' or 'rate'")

            y = data[num][network][datakey]
            std = data[num][network][stdkey]

            plt.plot(x, y, label=f"{network} {num} nodes")

    title = f"{type} {datakey}".title()
    plt.title(title)
    plt.xlabel("distance")
    plt.ylabel(measure)
    #plt.xticks([0,1,2,3,4,5,6])
    #ax.set_yticks([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    plt.legend()
    plt.show()
    plt.savefig(fname=f"data-{title}.jpg")

if __name__=="__main__":
    data = get_all_data()
    plot_these(data, type="bipartite", num_nodes=[2,3,4,5], measure="rate")
