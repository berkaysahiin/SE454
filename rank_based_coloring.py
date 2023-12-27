from mpi4py import MPI
import numpy as np
from enum import Enum

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
n = comm.Get_size()
                  #0 1 2 3 4 5 6 7  
G  =    np.array([[0,0,0,1,1,0,0,1], #0
                  [0,0,0,0,0,1,0,1], #1
                  [0,0,0,1,1,0,1,0], #2
                  [1,0,1,0,1,0,1,0], #3
                  [1,0,1,1,0,1,0,1], #4
                  [0,1,0,0,1,0,0,1], #5
                  [0,0,1,1,0,0,0,0], #6
                  [1,1,0,0,1,1,0,0]] #7
                  ,dtype=int)
           #0   1   2  3   4   5   6  7
children = [[3],[],[4],[6],[7],[1],[2],[5]]
           #0 1 2 3 4 5 6 7 
parents  = [0,5,6,0,2,7,3,4]

class NodeState(Enum):
    IDLE = 0
    COLORED = 1
    TERMINATE = 3

class Node:
    def __init__(self, rank, state=NodeState.IDLE):
        self.state = state
        self.rank = rank
        self.parent = parents[rank]
        self.childs = set(children[rank])
        self.neighbors = set(np.where(G[rank] == 1)[0])
        self.not_colored_neighbors = self.neighbors.copy()
        self.neighs_rcvd, self.rovers_rcvd = set(), set()
        self.round_rcvd = False
        self.color = -1
        self.banned_colors = set()
    
    def find_smallest_available_color(self):
        candidate_color = 0
        while candidate_color in self.banned_colors:
            candidate_color += 1
        return candidate_color
    
    def color_self(self, color):
        self.color = color
        self.state = NodeState.COLORED

class MessageType(Enum):
    ROUND = 0
    UPDATE = 1
    ACK = 2
    DISCARD = 3
    ROVER = 4
    TERMINATE = 5

class Message:
    def __init__(self, sender, type, data):
        self.sender = sender
        self.type = type
        self.data = data

class Alg:
    round_number = -1
    round_over = False

node = Node(rank)

#print(f'rank : {rank} -> {node.neighbors}')

while node.state != NodeState.TERMINATE:
    Alg.round_over = False
    node.neighs_rcvd.clear()
    node.rovers_rcvd.clear()
    node.round_rcvd = False

    if node.rank == 0: # root node, start next round
        Alg.round_number += 1
        round_msg = Message(sender=rank, type=MessageType.ROUND, data=Alg.round_number)
        comm.send(obj=round_msg, dest=0, tag=MessageType.ROUND.value)

        if node.state == NodeState.COLORED: # next round is the last round
            term_msg = Message(sender=rank, type=MessageType.TERMINATE, data=None)
            comm.send(obj=term_msg, dest=0, tag=MessageType.TERMINATE.value)



        #print(f'----------------Starting round {Alg.round_number}----------------')

    while not Alg.round_over:
        msg: Message = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)
        
        if msg.type == MessageType.ROUND:
            #print(f'Round recieved {node.rank}')
            Alg.round_number = msg.data
            round_msg = Message(sender=rank, type=MessageType.ROUND, data=msg.data)
            for child in node.childs:
                comm.send(obj=round_msg, dest=child, tag=MessageType.ROUND.value)

            discard_msg = Message(sender=rank, type=MessageType.DISCARD, data=None)
            if node.state == NodeState.COLORED:
                for neigh in node.neighbors:
                    comm.send(obj=discard_msg, dest=neigh, tag=MessageType.DISCARD.value)
            else:
                if not node.not_colored_neighbors or node.rank > max(node.not_colored_neighbors):
                    color = node.find_smallest_available_color()
                    node.color_self(color)
                    print(f"COLORING: rank: {rank}, color {color}", flush=True)
                    update_msg = Message(sender=rank, type=MessageType.UPDATE, data=node.color)
                    for neigh in node.not_colored_neighbors:
                        comm.send(obj=update_msg, dest=neigh, tag=MessageType.UPDATE.value)
                else:
                    for neigh in node.neighbors:
                        comm.send(obj=discard_msg, dest=neigh, tag=MessageType.DISCARD.value)
                
                node.round_rcvd = True

        elif msg.type == MessageType.UPDATE:
            node.neighs_rcvd.add(msg.sender)
            node.not_colored_neighbors.remove(msg.sender)
            node.banned_colors.add(msg.data)
            #print(f'UPDATE: rank: {node.rank}, colored neighbor: {msg.sender} with color: {msg.data}, sending ack', flush=True)

            ack_msg = Message(sender=rank, type=MessageType.ACK, data=None)
            comm.send(obj=ack_msg, dest=msg.sender, tag=MessageType.ACK.value)

        elif msg.type == MessageType.DISCARD:
            node.neighs_rcvd.add(msg.sender)

        elif msg.type == MessageType.ROVER:
            node.rovers_rcvd.add(msg.sender)
            #print(f'ROVER RECIEVED:  {node.rank} <----- {msg.sender}', flush=True)
        
        elif msg.type == MessageType.ACK:
            #print(f'ACK RECIEVED: rank: {node.rank}, sender: {msg.sender}')
            node.neighs_rcvd.add(msg.sender)
        
        elif msg.type == MessageType.TERMINATE:
            print(f'Recieved terminate msg {node.rank}')
            if node.childs:
                for child in node.childs:
                    term_msg = Message(sender=rank, type=MessageType.TERMINATE, data=None)
                    comm.send(obj=term_msg, dest=child, tag=MessageType.TERMINATE.value)

            node.state = NodeState.TERMINATE
            break

        if node.round_rcvd and node.neighbors.issubset(node.neighs_rcvd) and len(node.childs) == len(node.rovers_rcvd):
            rover_msg = Message(sender=rank, type=MessageType.ROVER, data=None)
            comm.send(obj=rover_msg, dest=node.parent, tag=MessageType.ROVER.value)
            Alg.round_over = True

print(f'Terminated {node.rank}')