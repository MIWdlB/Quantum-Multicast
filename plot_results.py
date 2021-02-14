"""Plot out data from datafiles."""
import argparse
import csv
import os
import re
from datetime import date
from pathlib import Path
from pprint import pprint as print
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np


def parseargs() -> None:
    """Parse args for plotter."""
    parser = argparse.ArgumentParser(description="Plot data from network simulations.")
    parser.add_argument(
        "type",
        type=str,
        choices=["bipartite", "multipartite", "both", "bi", "multi"],
        help="The type of network to plot data for. bipartite, multipartite or both.",
    )
    parser.add_argument(
        "measure",
        type=str,
        choices=["rate", "fidelity", "time"],
        help="Which measure to plot data for: 'rate' of entanglement, 'fidelity' or 'time' between successes.",
    )
    parser.add_argument(
        "--filenames",
        "-f",
        type=List[str],
        default="last",
        required=False,
        help="A list of names or patterns defining which subdirectories of 'data' to obtain data for. If not provided the most recent dataset will be used.",
    )
    parser.add_argument(
        "--link_numbers",
        "-l",
        type=List[int],
        help="A list of integers giving the number of links to plot data for.",
    )
    parser.add_argument(
        "--plot_analytic",
        "-a",
        type=bool,
        defualt=False,
        help="Whether to overlay plots of analytic model predictions or not.",
    )
    return parser.parse_args()


def analytic_data(network: str) -> None:
    """Define plottable datasets for the analytic model of each network type.
    
    Parameters
    ----------
    network : "bipartite", "multipartite"
    """
    # Prob of successful generation vs distance
    L0 = -2 / np.log(0.1)  # attenuation length TODO does this need to changed.
    pL = 0.2  # prob loss on entering channel
    d = np.linspace(0.1, 2.5, 100)
    pg = (1 - pL) * np.exp(-d / L0)  # overall prob of successful generation of 1 link
    ps = 1  # prob of successful LOCC

    # wait times bipartite
    link1waitbp = 1 / (pg * ps)
    r1bp = 1 / link1waitbp

    link2waitbp = 3 / (2 * pg * ps)
    r2bp = 1 / link2waitbp

    link4waitbp = 25 / (12 * pg * ps)
    r4bp = 1 / link4waitbp

    # plot
    rates = [(d, r1bp, 1), (d, r2bp, 2), (d, r4bp, 4)]

    ###wait time for three - ghz state
    Wait3GHZ = 3 / (2 * pg)
    rate3GHZ = 1 / Wait3GHZ

    if network == "bipartite":
        return rates
    elif network == "multipartite":
        return [(d, rate3GHZ, 2)]


def get_file_data(datafile: Path) -> Dict:
    """Extract data from CSV file.
    
    Parameters
    ----------
    datafile : Path
        Path to the file to extract data from.
    """

    data = {}
    with open(datafile) as file:
        reader = csv.reader(file, delimiter=",")

        fields = []
        temp = []

        # Header has passed read main data.
        for index, line in enumerate(reader):
            if index == 0 or index == 1:
                fields += line
                data = {
                    field.strip(): np.array([], dtype=np.float32) for field in fields
                }
            elif index % 2 == 0:
                temp += line
            elif index % 2 == 1:
                temp += line
                for field, item in zip(fields, temp):
                    if item == "nan":
                        item = None
                    elif item == "":
                        item = None
                    elif item is not None:
                        item = float(item)
                    data[field.strip()] = np.append(data[field.strip()], item)
                temp = []

    return data


def get_all_data(folder_names: str) -> Dict:
    """Get all the data from all files.
    
    Parameters
    ----------
    folder_names : str
        The names or partial names of folders to extract data from.
    """
    folders = os.listdir("data/")
    folders.sort()

    if folder_names == "last" or "last" in folder_names:
        folders = [folders[-1]]
    elif folder_names:
        folders = [f for f in folders if any([time in f for time in folder_names])]

    data = {}

    files = []
    for folder in folders:
        files += [folder + "/" + file for file in os.listdir("data/" + folder)]

    for file in files:
        pattern = re.compile(pattern="nodes:(\d)")
        num_nodes = pattern.search(file).groups()[0]
        num_nodes = int(num_nodes)

        if "bipartite" in file:
            type = "bipartite"
        elif "multipartite" in file:
            type = "multipartite"
        else:
            raise NameError("Cannot parse network type from filename.")

        data[num_nodes] = data.get(num_nodes, {})
        data[num_nodes][type] = data[num_nodes].get(type, {})

        if "noise" in file:
            pattern = re.compile(pattern="noise:(\d+)")
            noise_rate = pattern.search(file).groups()[0]
            noise_rate = float(noise_rate)
            data[num_nodes][type][noise_rate] = get_file_data("data/" + file)
        else:
            data[num_nodes][type][1e7] = get_file_data("data/" + file)

    return data


def plot_these(
    data: dict,
    type: str,
    plot_analytic: bool,
    num_nodes: List[int],
    measure: str,
    noise_rates: List[float] = [1e7],
) -> None:
    """Plot the data.

    Parameters
    ----------
    data : Dict
        A dict containg the data to be plotted.

    type : "bipartite", "multipartite", "both"
        The type of network to plot data for.

    plot_analytic : bool
        Whether or not to overlay plots of analytic models.

    num_nodes : List[int]
        A list of node quantities to plot data for.

    maesure : "fidelity", "rate", "time" or "noise"
        The measure to plot data for.

    noise_rate : List[float], default 1e7
        The noise rate to plot data for.

    """
    networks = []
    type = type.lower()
    if type in ["bipartite", "both"]:
        networks.append("bipartite")
    if type in ["multipartite", "both"]:
        networks.append("multipartite")

    if not networks:
        raise ValueError("'type' must be 'bipartite', 'multipartite' or 'both'")

    for network in networks:

        if plot_analytic:
            for dataset in analytic_data(network):
                x, y, num = dataset
                if num in num_nodes:
                    label = "Analytic"
                    if len(network) != 1:
                        label += f" {network}"
                    if len(num_nodes) != 1:
                        label += f", links={num}"

                    plt.plot(x, y, label=label)

        for num in num_nodes:
            for noise_rate in noise_rates:
                dataset = data[num][network][noise_rate]
                # The data keys use
                # import pdb; pdb.set_trace()
                x = dataset["edge length"]

                if measure == "fidelity":
                    datakey = "mean fidelity"
                    stdkey = "fidelity std"
                    ylabel = "Fidelity"
                elif measure == "rate":
                    datakey = "entanglement rate"
                    stdkey = "time std"
                    ylabel = "Entanglement Rate"
                elif measure == "time":
                    datakey = "mean time"
                    stdkey = "time std"
                    ylabel = "Mean Time To Success [ns]"

                else:
                    raise ValueError("'measure' must be 'fidelity' or 'rate'")

                y = dataset[datakey]
                std = dataset[stdkey]

                upper = []
                lower = []
                for yi, stdi in zip(y, std):
                    u = yi + stdi if (yi is not None and stdi is not None) else None
                    l = yi - stdi if (yi is not None and stdi is not None) else None

                    upper.append(u)
                    lower.append(l)

                # import pdb; pdb.set_trace()
                label = ""
                if len(networks) != 1:
                    label += f"{network} "
                if len(num_nodes) != 1:
                    label += f"links={num} "
                if len(noise_rates) != 1:
                    label += f"gamma={int(noise_rate):.0e}"
                plt.plot(x, y, label=label)
                if measure in ["time"]:
                    plt.fill_between(x, lower, upper, alpha=0.5)

    title = f"{type} {datakey}: "
    if len(num_nodes) == 1:
        title += f"{num} Links "
    if len(noise_rates) == 1:
        title += f"gamma={int(noise_rate):.0e} "
    title = title.title()
    print(title)
    plt.title(title)
    plt.xlabel("Distance [km]")
    plt.ylabel(ylabel)
    # plt.yscale("log")
    # plt.xticks([0,1,2,3,4,5,6])
    # ax.set_yticks([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    plt.legend()
    folder = "results-plots/"
    plt.savefig(fname=folder + f"data-{title}.jpg")
    plt.show()


if __name__ == "__main__":
    args = parseargs()
    data = get_all_data(folder_names=args.filenames)
    plot_these(
        data,
        type=args.type,
        plot_analytic=args.plot_analytic,
        num_nodes=args.link_numbers,
        measure=args.measure,
    )
