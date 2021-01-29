# Quantum-Multicast
UCLCDTDQT Group Project on multicast quantum communication.

## Usage

### Graph Class

`utils/graph.py` Defines a basic graph, with nodes and weighted edges. Edges are assumed to be undirected but are stored as two directed edges, with weights defaulting to one.

Examples are given in `utils/graphlibrary.py`.

### Network cration

Given a graph a (bipartite) network can be created using the `create_bipartite_network` function in `utils/bipartite_network.py`.
This will craete a channel for each directed edge in the graph, with an associated source for each.

## Development

### Poetry
Poetry is a really nice python dependency manager. It lets you keep track of versions and easily update, unlike pip. 
You can get it with `pip install poetry` then set up by running `poetry install` from within the directory. It will create a virtual environment and install consistent versions of things.

## Resources

### Overleaf
Our shared overleaf page is https://www.overleaf.com/9113389971gxfgtgbsyyxq.

## Simulators

### NetSquid 
You'll need to make an account at https://netsquid.org/ to access the documentation. Take a look at the tutorials section and the API Reference for NetSquid.
There is also a [whitepaper](http://arxiv.org/abs/1411.4028)


### SeQUeNCe (Not used)
You can see the repo here: https://github.com/sequence-toolbox/SeQUeNCe The bit we'd have to update is `src/entanglement_management/generation.py` and it's dependencies. There are usage examples but they're not very well documented.
