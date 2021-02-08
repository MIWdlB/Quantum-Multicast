"""Plot out data from datafiles."""
import csv
import os
import re
from typing import Dict, List
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint as print
from datetime import date

#Bipartite////multipartite funcs

import numpy as np 
import matplotlib.pyplot as plt



def analytic_data(network:str):
    #Prob of successful generation vs distance
    L0 = - 2 / np.log(0.1)         #attenuation length TODO does this need to changed.
    pL = 0.2                          #prob loss on entering channel
    d= np.linspace(0.1,2.5,100)
    pg = (1 - pL ) *np.exp( - d / L0)        #overall prob of successful generation of 1 link
    ps = 1                         # prob of successful LOCC 


    #wait times bipartite
    link1waitbp = (1 /(pg*ps))
    r1bp = 1/ link1waitbp

    link2waitbp = (3 /(2*pg*ps))
    r2bp = 1/ link2waitbp

    link4waitbp = ( 25 /( 12 * pg * ps))
    r4bp = 1/ link4waitbp

    #plot
    rates = [(d, r1bp,1), (d, r2bp,2), (d, r4bp,4)]

    ###wait time for three - ghz state
    Wait3GHZ = (3 /(2*pg))
    rate3GHZ = 1/ Wait3GHZ

    if network == "bipartite":
        return rates
    elif network == "multipartite":
        return [(d, rate3GHZ,2)]

    # for r in rates: 
    #     plt.plot(d,r[0], label = r[1])
    # plt.ylabel("Entanglement Rate (Hz)")
    # plt.xlabel("Link Length (km)")
    # plt.title("Entanglement rate over link length")
    # plt.legend()
    # plt.show()


    # plt.plot(d, rate3GHZ, label=("3-partite GHZ state"))
    # plt.plot(d, r2bp, label=("2 bipartite links"))
    # plt.ylabel("Entanglement Rate (Hz)")
    # plt.xlabel("Link Length (km)")
    # plt.title("Entanglement Rate over link length")
    # plt.legend()
    # plt.show()

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
                    elif item == '':
                        item = None
                    elif item is not None:
                        item = float(item)
                    data[field.strip()] = np.append(data[field.strip()], item)
                temp = []

    return data

def get_all_data() -> Dict:
    """Get all the data from all files."""

    folders = os.listdir("data/")

    folder_times = ["22:09", "11:43:48"]

    #folders = [f for f in folders if any([time in f for time in folder_times])]
    #folder = [folders[-1]]

    data = {}

    pattern = re.compile(pattern='nodes:(\d)')

    files = []
    for folder in folders:
        files += [folder + "/" + file for file in os.listdir("data/" + folder)]
    print(files)

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

        # def find_confidence_interval(min_time,mean_time,time_std,sample_size):
        #     delta_t = time_std*1.960/np.sqrt(sample_size) #95% confidence interval

        #     upper_lim = min_time/(mean_time-delta_t) #
        #     for i, l in enumerate(upper_lim):
        #         upper_lim[i] = l if (mean_time[i] - delta_t[i] >= 0) else float('inf')

        #     lower_lim = min_time/(mean_time+delta_t) 
        #     rate_interval = [lower_lim,upper_lim]
        #     return rate_interval
        
        # for num_nodes in data:
        #     for type in data[num_nodes]:
        #         set = data[num_nodes][type]
        #         data[num_nodes][type]["rate std"] = find_confidence_interval(set["min time"], set["mean time"], set["time std"], 10000)

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
    type=type.lower()
    if type in ["bipartite", "comparison"]:
        networks.append("bipartite")
    if type in ["multipartite", "comparison"]:
        networks.append("multipartite")
    
    if not networks:
        raise ValueError("'type' must be 'bipartite', 'multipartite' or 'comparison'")
    
    for network in networks:

        # for dataset in analytic_data(network):
        #     x, y, num = dataset     
        #     if num in num_nodes:       
        #         plt.plot(x, y, label=f"Analytic {network} {num} nodes")

        for num in num_nodes:
            # The data keys use 
            #import pdb; pdb.set_trace()
            x = data[num][network]['edge length']

            if measure == "fidelity":
                datakey = "mean fidelity"
                stdkey = "fidelity std"
                ylabel = "Fidelity"
            elif measure == "rate":
                datakey = "entanglement rate"
                stdkey = "time std"
                ylabel = "Entanglement Rate [Hz]"
            elif measure == "time":
                datakey = "mean time"
                stdkey = "time std"
                ylabel = "Mean Time To Success [ns]"

            else:
                raise ValueError("'measure' must be 'fidelity' or 'rate'")

            y = data[num][network][datakey]
            std = data[num][network][stdkey]


            upper = []
            lower = []
            for yi, stdi in zip(y,std):
                u = yi + stdi if (yi is not None and stdi is not None) else None
                l = yi - stdi if (yi is not None and stdi is not None) else None

                upper.append(u)
                lower.append(l)

            #import pdb; pdb.set_trace()
            plt.plot(x, y, label=f"Simulated {network} {num} nodes")
            if measure in ["time","fidelity"]:
                plt.fill_between(x, lower, upper,alpha=0.5)

            print(f"Simulated {network} {num} nodes")

    title = f"{type} {datakey}".title()
    plt.title(title)
    plt.xlabel("distance [km]")
    plt.ylabel(ylabel)
    #plt.yscale("log")
    #plt.xticks([0,1,2,3,4,5,6])
    #ax.set_yticks([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    plt.legend()
    plt.savefig(fname=f"data-{title}.jpg")
    plt.show()

if __name__=="__main__":
    data = get_all_data()
    #plot_these(data, type="comparison", num_nodes=[2,4], measure="rate")
    plot_these(data, type="bipartite", num_nodes=[1,2], measure="time")


