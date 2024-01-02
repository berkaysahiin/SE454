# SE454 Distributed Computing Project

## Rank-Based Graph Coloring Algorithm

### Overview

This project implements a distributed computing algorithm for rank-based graph coloring using the MPI (Message Passing Interface) library. The algorithm is designed to color nodes in a distributed graph while efficiently communicating with neighboring nodes.

### Files

- **rank_based_coloring.py**: The main Python script implementing the rank-based coloring algorithm using MPI.

### How to Run

1. Ensure you have MPI installed on your system.
2. Execute the script using the following command:
   ```bash
   mpiexec -n <num_processes> python rank_based_coloring.py

## Algorithm Execution Loop
Each round is started by the root node, and node with highest local degree color itself.

## Termination Condition
This algorithm assumes that the root node is the lowest ranked node, thus terminates when the root node is colored.

## Input Graph
The input graph is represented as an adjacency matrix (G), and the tree structure is defined by parent-child relationships to construct a MST.

## Output
The script outputs the termination details, including the rank of the node and its assigned color, to an "output.log" file.

## Logging
The script utilizes a custom logging module (MPILogFile) to log output details.

### Important Note
This script is configured for a specific input graph and tree structure. Modify the G, children, and parents arrays according to your specific use case.
