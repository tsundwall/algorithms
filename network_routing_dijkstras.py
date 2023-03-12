#!/usr/bin/python3


from CS312Graph import *
import time
import numpy as np


class Node:

    def __init__(self, key, dist, prev=None):
        self.key = key #stores node_id value
        self.dist = dist  # current distance from source node
        self.prev = prev  # key of prev node

class Heap:

    def __init__(self):
        self.tree = []  # H list; current stack of unvisited nodes
        self.length = 0 #num of nodes in tree
        self.keys = {} #keys pointing to tree position
        self.keyPrev = {} #static-length list containing current prev values; will be used to find source from dest
        self.keyDist = {}

    def insert(self, new): #o(logn) complexity
        #o(1) operations###
        self.tree.append(new) #add to tree
        self.keys[new.key] = self.length #add to dictionary

        self.length += 1 #increase H length

        index = self.length - 1 #index is end of list

        go_up = True

        while go_up: # will sift a maximum of logn times
            #evey operation within while loop is o(1)
            parent = self.tree[(index -1) // 2] #look at parent

            if index == 0:  # root has been reached; sifting is complete

                go_up = False

            elif parent.dist > new.dist: #if parent has larger value, switch

                self.tree[(index -1)] = parent #switch indices of parent and child
                self.tree[(index -1) // 2] = new

                self.keys[parent.key] = index #switch values in dictionary
                self.keys[new.key] = (index -1) // 2

                index = (index - 1) // 2 #update index to former parent position

            else: #if parent isnt larger, work is complete

                go_up = False

    def deletemin(self): #o(logn) worst case complexity shape
        #o(1) operations####
        index = 0
        root = self.tree[0] #deletemin value
        lastNode = self.tree[self.length - 1] #grab last value in tree
        self.tree[0] = lastNode  # replace root with last value
        self.keys[lastNode.key] = index  #set key of new root value to 0

        del self.keys[root.key] #remove key (no longer in tree)

        go_down = True

        while go_down: #maximum logn sifts **typically more sifts than isert since a low value was placed in index 0
            #all o(1) operations within while loop####
            if index * 2 + 1 >= self.length:  # if no children, work is done

                go_down = False

            else: #if children exist
                childLeft = self.tree[index * 2 + 1] #set left child

                if index * 2 + 2 >= self.length: # no right child; only check left


                    if lastNode.dist > childLeft.dist: #if child is less, switch

                        self.tree[index * 2 + 1] = lastNode
                        self.tree[index] = childLeft

                        self.keys[lastNode.key] = index * 2 + 1
                        self.keys[childLeft.key] = index
                        index = index * 2 + 1

                    else:

                        go_down = False

                else: #else both children exist

                    childRight = self.tree[index * 2 + 2] #set right child

                    if lastNode.dist == childRight.dist and lastNode.dist == childLeft.dist: #if all equal, do nothing

                        go_down = False

                    elif lastNode.dist > childRight.dist and childLeft.dist >= childRight.dist: #if right child is smallest of three, swap upper and right

                        self.tree[index * 2 + 2] = lastNode
                        self.tree[index] = childRight

                        self.keys[lastNode.key] = index * 2 + 2
                        self.keys[childRight.key] = index
                        index = index * 2 + 2

                    elif lastNode.dist > childLeft.dist: #if upper is greater than left, switch upper node with left child

                            self.tree[index * 2 + 1] = lastNode
                            self.tree[index] = childLeft

                            self.keys[lastNode.key] = index * 2 + 1
                            self.keys[childLeft.key] = index
                            index = index * 2 + 1

                    else: #if upper node is smallest of three, work is done
                        go_down = False

        self.length -= 1 #update tree size
        self.tree.pop() #remove last branch (where the sifting node formerly was)

        return root

    def makequeue(self, firstNode): #this method is o(1); the actual "makequeue" operation is a loop of inserts (see the Dijkstra implementation)

        self.length += 1

        self.keys[firstNode.key] = 0 #init distance of source node to 0
        self.tree.append(firstNode) #add to tree (now of length 1)

        return self

    def decreasekey(self, key):  #o(logn) complexity
        #o(n) operations below
        index = self.keys[key] #find the location of the node in question in the tree

        decreasedNode = self.tree[index] #get node in question

        go_up = True

        while go_up: #another set of sifts; this one is upward and is again maximum logn loops
            #o(c1) operations within loop, no added complexity
            parent = self.tree[(index - 1) // 2] #get its parent

            if index == 0:  # root has been reached, work is done

                go_up = False

            elif parent.dist > decreasedNode.dist: #if parent is greater, sift changed node up

                self.tree[index] = parent #update indices in tree
                self.tree[(index - 1) // 2] = decreasedNode

                self.keys[parent.key] = index #update key values
                self.keys[decreasedNode.key] = (index - 1) // 2

                index = (index - 1) // 2

            else: #if parent is smaller, work is done

                go_up = False

    def search(self, key): #o(1) because we are accessing key value in dict rather than looping through a list structure

        if self.keys.get(key) == None:
            return None

        else:

            return self.tree[self.keys[key]]

    def peek(self): #for debugging purposes only, o(n)

        print("Peek:")
        for node in self.tree:
            print(str(node.key) + " " + str(node.dist) + " " + str(node.prev))
        print(self.keys)
        print("\n")

class NetworkRoutingSolver:

    def __init__( self):
        pass

    def initializeNetwork( self, network ):
        assert( type(network) == CS312Graph )
        self.network = network


    def getShortestPath( self, destIndex, keyPrev): #maximum o(n) operation; need to iteratively look through prev values until source is reached
        #o(1) operations####
        self.dest = destIndex

        path_edges = []
        total_length = 0
        sourceReached = False

        destNode = self.network.nodes[self.dest] #init dest node
        destNodePrev = keyPrev[destNode.node_id]

        if destNodePrev is None: #return infinite cost if no path exists
            return {'cost': np.Inf, 'path': path_edges}

        srcNode = self.network.nodes[destNodePrev]

        while not sourceReached: #o(n) operation

            for potEdges in range(len(srcNode.neighbors)): #o(3) edges -> o(1)

                currEdge = srcNode.neighbors[potEdges] #evaluate current edge

                if currEdge.dest.node_id == destNode.node_id: #if other node in edge equals the prev node, we found the right one

                    total_length += currEdge.length #update total length
                    path_edges.append((currEdge.src.loc, currEdge.dest.loc, '{:.0f}'.format(currEdge.length))) #add edge to gui
                    destNode = self.network.nodes[currEdge.src.node_id] #update new dest node to old source node (we are moving backwards)
                    destNodePrev = keyPrev[destNode.node_id] #get key of prev node

                    if destNodePrev is None: #if no prev node exists

                        if destNode.node_id == self.source: #and the dets node is the source, we are done
                            sourceReached = True

                        else:
                            return {'cost': np.Inf, 'path': []} #otherwise, no path exists, return inf length

                    else:
                        srcNode = self.network.nodes[destNodePrev] #if prev node exists, set new source node


        return {'cost': total_length, 'path': path_edges} #return length and edges

    def computeShortestPaths( self, srcIndex, use_heap=False ): #dijkstras implementation

        self.source = srcIndex
        t1 = time.time()

        nodesList = self.network.nodes #store list of network.node objects

        if use_heap: #if using heap, execute the below clause; loop through n nodes, each of which has at least one o(logn) operation; o(nlogn) total
            #o(1) operations####
            sourceNode = Node(self.source, 0) #init node object for source node

            heap = Heap() #create our heap

            heap.makequeue(sourceNode) #init heap with source node with dist 0

            heap.keyPrev[self.source] = None #null prev val
            heap.keyDist[self.source] = 0 #distance 0 for source node

            counter = 0

            for node in nodesList: #effectively makequeue with insert(); insert will be O(1) here since no sifting will occur (all inf); o(n) in total

                counter += 1

                if counter - 1 == srcIndex: #skip source node (already used to init Heap())

                    continue

                else:
                    heapNode = Node(node.node_id, np.Inf) #create node object with default dist and prev
                    heap.insert(heapNode) #o(1) insert
                    heap.keyPrev[node.node_id] = None #init keyPrev list to match keys to prev values
                    heap.keyDist[node.node_id] = np.Inf

            uCounter = 0

            while heap.length > 0: #continue until heap is empty (all nodes visited); o(n) since we will evaluate each node once

                uCounter += 1

                u = heap.deletemin() #o(logn)
                edges = nodesList[u.key].neighbors


                for edge in edges: #3 edges, fixed, o(1)

                    vdist = heap.keyDist[edge.dest.node_id] #find neighbor in heap


                    if vdist > u.dist + edge.length: #if new distance will be shorter, update
                        #o(1) operations###
                        v = heap.search(edge.dest.node_id) #o(1)
                        v.dist = u.dist + edge.length
                        heap.keyDist[v.key] = v.dist
                        v.prev = u
                        heap.keyPrev[v.key] = u.key

                        heap.decreasekey(v.key) #o(logn)


            t2 = time.time()
            return (t2 - t1), heap.keyPrev

        else: #array structure-- still n loops, but each loop has a o(n) deletemin() operation-- total of o(n^2)

            #o(1) inits####
            keyArray = []
            distArray = {} #key-distance dictionary; fixed length
            prevArray = {} #key-prev dictionary; fixed length
            H = [] #heap array, stores unevaluated keys; algorithm runs until this returns to empty

            for each in range(len(nodesList)): #analagous to insert(), o(n)
                #o(1) operations in loop####
                node = nodesList[each] #find node in list
                keyArray.append(node.node_id)
                distArray[node.node_id] = np.Inf #set default dist value
                prevArray[node.node_id] = None #set null prev value
                H.append(node.node_id) #add node id to H

            distArray[srcIndex] = 0 #source dist to 0

            while len(H) > 0: #while H not empty set; o(n) total loops explicitly
                min = np.Inf #init minimum dist in H to Inf
                uKey = H[0] #init uKey on each iter; if below loop never enters, all remaining nodes are infinity, take 0 index
                for deleteMin in H: #effectively deletemin; o(n) operation
                    currMin = distArray[deleteMin] #eval current node
                    if currMin < min: #if its the min up to this point
                        min = currMin #update min
                        uKey = deleteMin #update min key

                u = nodesList[uKey] #since nodesList is sorted by key, use uKey to find u (node object of u)
                udist = distArray[uKey] #get current distance to u
                H.remove(uKey) #remove u from stack

                for edge in u.neighbors: #o(3), evaluate each edge from u

                    vKey = edge.dest.node_id
                    vdist = distArray[vKey] #find v's distance
                    edgeLength = edge.length #set edge length

                    if vdist > udist + edgeLength: #if total distance through u is better, update

                        distArray[vKey] = udist + edgeLength #update dictionaries, equivalent to decreasekey o(1)
                        prevArray[vKey] = uKey

            t2 = time.time()

            return (t2-t1), prevArray

