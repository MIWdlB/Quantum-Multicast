# Quantum-Multicast
UCLCDTDQT Group Project on multicast quantum communication.

## Aim
To find, for a given soruce node, at what rate and fidelity GHZ states can be prepared by the source node such that consitiuent qubits are shared amoung all nodes.

## Usage

The current functionality of our package is called from `bipartite.py`, which creates a network from a sample graph and shares bipartite quantum entanglements from the source node. 

### Graph Class

`utils/graph.py` Defines a basic graph, with nodes and weighted edges. Edges are assumed to be undirected but are stored as two directed edges, with weights defaulting to one.

Examples are given in `utils/graphlibrary.py`.

### Network creation

Given a graph a `network` object can be created using the `create_bipartite_network` function in `utils/bipartite_network.py`.
This will create `node` objects foreach node and add a channel for each directed edge in the graph, with an associated source for each outward edge. Nodes are also given `QuantumProcessor` objects with a number of memory slots equal to the number of directed edges to and from the node.

### Connections & Channels 
`connection`s are a network subcomponent which contains a `channel` for information. These can be classical only, quantum only or allow both forms of communication. Each `channel` has associated `ports` at each end, inputs of which are forwarded to memory locations of the recieving node's `QuantumProcessor`.

### Protocols

Protocols are sets of instructions run on a `node`. We have one protocol `BipartiteProtocol` which handles both the case in which a node is a source and when it is a reciever.

Source nodes will trigger a `qsource` associated with each connection to create Bell pairs. One of each of these pair will be stored in memory, the other will be send to the connected node.

### Programs

Programs are run on `QuantumProcessors` and use `Instruction`s to carry out quantum operations and measurements. We use the program `CreateGHZ` to turn n pairs of bipartite Bell states into an n+1 qubit GHZ state.

Note that we still need to communicate the results of measurements in this program to reciever nodes via a classical channel, to make corrections associated with the maesurement outcomes.

## Resources

### NetSquid 
You'll need to make an account at https://netsquid.org/ to access the documentation. Take a look at the tutorials section and the API Reference for NetSquid.
There is also a [whitepaper](http://arxiv.org/abs/1411.4028)
