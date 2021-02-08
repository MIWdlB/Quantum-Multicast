# Quantum-Multicast
UCLCDTDQT Group Project on multicast quantum communication.

## Aim
To find, for a given soruce node, at what rate and fidelity GHZ states can be prepared by the source node such that consitiuent qubits are shared amoung all nodes.

## Usage

The current functionality of our package is called from `simulate.py`, which creates networks with a range of numbers of remote nodes, and begins a simulation for each number at various edge lengths.

Data from simulations is output to `data/` with filenames indicating the entanglement type, number of nodes and length range included.

### Network creation

Given a graph a `network` object can be created using the `create_network` function in `utils/create_network.py`.
This will create `node` objects foreach node and add a channel for each directed edge in the graph. Quantum sources are added to bipartite networks one per edge and in multipartite networks one per node. Nodes are also given `QuantumProcessor` objects with a number of memory slots equal to the number of directed edges to and from the node.

### Connections & Channels 
`connection`s are a network subcomponent which contains a `channel` for information. These can be classical only, quantum only or allow both forms of communication. Each `channel` has associated `ports` at each end, inputs of which are forwarded to memory locations of the recieving node's `QuantumProcessor`.

### Protocols

Protocols are sets of instructions run on a `node`. We define protocols an `InputProtocol` to be used in both bipartite and multipartite networks. This is assigned to the reciver nodes. The `OutputProtocol` is used as a base class to `BipartiteOutputProtocol` and `MultipartiteOutputProtocol`. These are assigned to the source node dependent on network type.

Source nodes will trigger a `qsource` associated with each connection to create Bell pairs. One of each of these pair will be stored in memory, the other will be send to the connected node.

### Programs

Programs are run on `QuantumProcessors` and use `Instruction`s to carry out quantum operations and measurements. We use the program `CreateGHZ` to turn n pairs of bipartite Bell states into an n+1 qubit GHZ state.

Note that we still need to communicate the results of measurements in this program to reciever nodes via a classical channel, to make corrections associated with the maesurement outcomes.

## Resources

### NetSquid 
You'll need to make an account at https://netsquid.org/ to access the documentation. Take a look at the tutorials section and the API Reference for NetSquid.
There is also a [whitepaper](http://arxiv.org/abs/1411.4028)
