#!/usr/bin/python3

from which_pyqt import PYQT_VER
if PYQT_VER == 'PYQT5':
	from PyQt5.QtCore import QLineF, QPointF
elif PYQT_VER == 'PYQT4':
	from PyQt4.QtCore import QLineF, QPointF
else:
	raise Exception('Unsupported Version of PyQt: {}'.format(PYQT_VER))

import time
import numpy as np
from TSPClasses import *
import heapq
import itertools
import copy

class stateNode:

	def __init__(self, rcm, cost, partialPath, candidateCities, depth):

		self.depth = depth #depth of state
		self.cost = cost  #current cost in path
		self.partialPath = partialPath  #array of city ids already visited
		self.currCity = partialPath[-1] #current city is the last in partial path
		self.rcm = rcm #reduced cost matrix of prev state
		self.candidateCities = candidateCities #remaining cities available for branching
		self.metric = None #if PQ key is something other than cost, it is assigned in insert()

class stateHeap:

	def __init__(self):
		self.tree = []  #current stack of unevaluated states
		self.length = 0  #num of states in tree

	def insert(self, newStateNode, c_d=False, naiveEst=None):  #o(logn) complexity; tree structure allows for faster sifting

		newStateNode.metric = newStateNode.cost / newStateNode.depth

		# o(1) operations###
		self.tree.append(newStateNode)  # add to tree

		self.length += 1  # increase length

		index = self.length - 1  # index is last spot in tree

		go_up = True

		while go_up:  # will sift a maximum of logn times
			# evey operation within while loop is o(1)
			parent = self.tree[(index - 1) // 2]  # look at parent

			if index == 0:  # root has been reached; sifting is complete

				go_up = False

			elif parent.metric > newStateNode.metric:  # if parent has larger value, switch

				self.tree[(index)] = parent  # switch indices of parent and child

				self.tree[(index - 1) // 2] = newStateNode

				index = (index - 1) // 2  # update index to former parent position

			else:  # if parent isnt larger, work is complete

				go_up = False

	def deletemin(self):  # o(logn) worst case complexity shape
		# o(1) operations####
		index = 0
		root = self.tree[0]  # deletemin value
		lastNode = self.tree[self.length - 1]  # grab last value in tree
		self.tree[0] = lastNode  # replace root with last value

		go_down = True

		while go_down:

			if index * 2 + 1 >= self.length:  # if no children, work is done

				go_down = False

			else:  # if children exist
				childLeft = self.tree[index * 2 + 1]  # set left child

				if index * 2 + 2 >= self.length:  # no right child; only check left

					if lastNode.metric > childLeft.metric:  # if child is less, switch

						self.tree[index * 2 + 1] = lastNode
						self.tree[index] = childLeft

						index = index * 2 + 1

					else:

						go_down = False

				else:  # else both children exist

					childRight = self.tree[index * 2 + 2]  # set right child

					if lastNode.metric == childRight.metric and lastNode.metric == childLeft.metric:  # if all equal, do nothing

						go_down = False

					elif lastNode.metric > childRight.metric and childLeft.metric >= childRight.metric:  # if right child is smallest of three, swap upper and right

						self.tree[index * 2 + 2] = lastNode
						self.tree[index] = childRight

						index = index * 2 + 2

					elif lastNode.metric > childLeft.metric:  # if upper is greater than left, switch upper node with left child

						self.tree[index * 2 + 1] = lastNode
						self.tree[index] = childLeft

						index = index * 2 + 1

					else:  # if upper node is smallest of three, work is done
						go_down = False

		self.length -= 1  # update tree size
		self.tree.pop()  # remove last branch (where the sifting node formerly was)

		return root

	def peekQueue(self): #debugging only, can technically be O(n!) if all potential states are on the queue

		pathArray = []
		costArray = []

		for i in self.tree:

			pathArray.append(i.partialPath)
			costArray.append(i.cost)

		return pathArray, costArray

def getPath(pathIndices, cities): #maps city indices to the actual objects in _scenario.getCities()
	##this is O(n), as it will only be called when a leaf is encountered

	pathArray = []

	for i in pathIndices:
		pathArray.append(cities[i])

	return pathArray

def reduceCostMatrix(rcm, path, n, prevCost=0): #O(n^2) operation that is used to estimate cost of unvisited cities

	outbound, inbound = path #rows=inbound, cols=outbound
	bound = 0

	if (inbound, outbound) in rcm: #retreive edge cost, set reverse edge to inf

		edgeCost = rcm[(inbound, outbound)]
		rcm[(outbound, inbound)] = np.Inf

	for inboundEntry in range(n): #set all row entries to infinite

		rcm[(inbound, inboundEntry)] = np.Inf

	for outboundEntry in range(n): #set all column entries to infinite

		rcm[(outboundEntry, outbound)] = np.Inf

	for row in range(n):  # ITERATE THRU ROWS####

		rowMin = np.Inf #curr minimum is infinite

		for entry in range(n): #find min in row

			currEntry = rcm[(row, entry)]

			if currEntry < rowMin: #update rowMin when necessary
				rowMin = currEntry

		if rowMin < np.Inf: #if min < Inf, edit entries

			bound += rowMin #update total bound

			for entry in range(n): #subtract min from all entries

				rcm[(row, entry)] = rcm[(row, entry)] - rowMin

	for col in range(n):  # ITERATE THRU COLS####

		colMin = np.Inf

		for entry in range(n): #find min in column

			currEntry = rcm[(entry, col)]

			if currEntry > colMin:
				colMin = currEntry #update min when applicable

		if colMin < np.Inf: #if row isnt all Infs,

			bound += colMin #update bound,

			for entry in range(n): #and subtract column entries

				rcm[(entry, col)] = rcm[(entry, col)] - colMin

	bound = edgeCost + bound + prevCost #lowerbound = edgeCost(i,j) + addedEstimate + prevStateEstimate

	return rcm, bound

def initCostMatrix(cities): #O(n^2) to build initial cost matrix

	n = len(cities)
	costMatrix = {}

	for inbound in range(n): #set inbound city
		currEndCity = cities[inbound]

		for outbound in range(n): #take first outbound city
			currStartCity = cities[outbound]

			if currStartCity == currEndCity: #if they are equal, set to Inf
				costMatrix[(inbound, outbound)] = np.Inf

			else: #otherwise, find cost
				costMatrix[(inbound, outbound)] = currStartCity.costTo(currEndCity)

	return costMatrix

class TSPSolver:
	def __init__( self, gui_view ):
		self._scenario = None

	def setupWithScenario( self, scenario ):
		self._scenario = scenario

	def defaultRandomTour( self, time_allowance=60.0 ):
		results = {}
		cities = self._scenario.getCities()
		ncities = len(cities)
		foundTour = False
		count = 0
		bssf = None
		start_time = time.time()
		while not foundTour and time.time()-start_time < time_allowance:
			# create a random permutation
			perm = np.random.permutation( ncities )
			route = []
			# Now build the route using the random permutation
			for i in range( ncities ):
				route.append( cities[ perm[i] ] )
			bssf = TSPSolution(route)
			count += 1
			if bssf.cost < np.inf:
				# Found a valid route
				foundTour = True
		end_time = time.time()
		results['cost'] = bssf.cost if foundTour else math.inf
		results['time'] = end_time - start_time
		results['count'] = count
		results['soln'] = bssf
		results['max'] = None
		results['total'] = None
		results['pruned'] = None
		return results


	def greedy( self,time_allowance=60.0 ): #overall, an O(n^2n!) time complexity, only O(n) space complexity (if a path is reset, so is the stored optPath)

		start_time = time.time() #O(1) operations
		results = {}
		cities = self._scenario.getCities()
		n = len(cities)
		cost = 0
		availableCities = copy.deepcopy(cities) #make copy of cities to modify available cities at each iteration
		startCity = availableCities.pop(0) #pop first entry, set as start city
		currCity = startCity
		optPath = [startCity] #init optimal path
		pathFound = False
		timeOut = False
		tryCount = 0

		while not pathFound and not timeOut: #this is, again, technically O(n!), given no sparsity limit. in practice given the edge density, this is almost always one iteration

			tryCount += 1 #if new starting point, add try

			while len(availableCities) > 0: #n^2 complexity inner loop; a path will be n long, evaluate n potential steps each time
				if time.time() - start_time > time_allowance:

					timeOut = True
					break

				minEdge = np.Inf #init minEdge to inf

				for edge in range(len(availableCities)): #O(n) loop, check all possible next cities

					currEdge = currCity.costTo(availableCities[edge]) #get edge cost

					if currEdge < minEdge: #update when necessary

						minEdge = currEdge
						destCityIndex = edge
						destCity = availableCities[edge]

				if minEdge == np.Inf:

					break #break out of inner loop if can't move forward

				else: #if edge exists,

					availableCities.pop(destCityIndex) #remove from available
					cost += minEdge #update cost
					optPath.append(destCity) #update optimal path
					currCity = destCity

			if currCity.costTo(startCity) != np.Inf and len(availableCities) == 0: #if final edge in cycle exists,

				bssf = TSPSolution(optPath) #O(n)
				pathFound = True #exit outer loop

			startCityIndex = np.random.choice(np.arange(0,n)) #take a random city to restart greedy
			availableCities = copy.deepcopy(cities) #make new copy of available cities
			startCity = availableCities.pop(startCityIndex)
			optPath = [startCity] #re-init optPath

		end_time = time.time()

		results['cost'] = bssf.cost if pathFound else np.Inf
		results['time'] = end_time - start_time
		results['count'] = tryCount
		results['soln'] = bssf if pathFound else None
		results['max'] = None #these metrics are not needed, no states exist
		results['total'] = None
		results['pruned'] = None

		return results

	def branchAndBound( self, time_allowance=60.0 ): #TOTAL ALGORITHM TIME COMPLEXITY => O(n^4n!) [reduced from O(n^2 + n^3logn + n^4n!logn)]; SPACE COMPEXITY => O(n^3n!) at max queue size
		###all inits have constant-time and constant-storage complexity
		timeOut = False #init all reporting variables here###
		start_time = time.time()
		results = {}
		totSolutions = 0
		maxQueueSize = 0
		prunedStates = 0

		cities = self._scenario.getCities() #array of all city objects
		n = len(cities) #problem size
		naiveEst = n * 785
		bssf = TSPSolver.greedy(self)['soln'] #init greedy bssf; much higher variance than random heuristic, but can be exceptionally faster
		remainingCities = cities[1:] #the rest of the cities are candidates for next path
		pathQueue = stateHeap() #create PQ object
		initialCostMatrix = initCostMatrix(cities) #init the zero-state cost matrix; space cost of O(n^2)
		initialCostMatrixCopy = copy.deepcopy(initialCostMatrix)

		totStates = n - 1 #init total states with zero-state branch (n-1)

		for firstEdge in range(1,n): #O(n^3logn), init queue with all possible starting edges; space complexity is O(1), immediately sending stateNode() objs to queue, rcms dont change size (insert() takes up no space)

			initialCostMatrix = copy.deepcopy(initialCostMatrixCopy) #create deepcopy of initial CM
			partialPath = [0, firstEdge]
			rcm, currCost = reduceCostMatrix(initialCostMatrix, partialPath, n) #time/space of n^2; nxn matrix, evaluates all entries

			candidateCities = remainingCities[:firstEdge-1] + remainingCities[firstEdge:] #remove current first edge from remaining cities

			if currCost < bssf.cost: #if eligible,
				pathQueue.insert(stateNode(rcm, currCost, partialPath, candidateCities, depth=1), c_d=True, naiveEst=naiveEst) #create new state

		while pathQueue.length > 0 and not timeOut: #quit if optimal is found, or if time limit is reached
			#pathQueue can *technically* see n*n! total state objects (n! possible solutions, n intermediate states), and 1 is evaluated per loop; so n*n! potential loops
			#the loop through children to find eligible extended paths is potentially O(n^3), making this routing O(n^4*n!*logn)
			#while this is technically worse than a brute force O(n!), we use these child loops to significantly prune branches
			#(empirically much faster than O(n!)

			currState = pathQueue.deletemin() #GET NEXT STATE FROM QUEUE (deletemin() is a O(logn) procedure)

			if pathQueue.length > maxQueueSize: #update maxQueue if necessary

				maxQueueSize = pathQueue.length

			if currState.cost > bssf.cost: #if currState cost < bssf, skip it (can happen if bssf has been updated since last eval)

				prunedStates += 1
				continue

			currStateRcmCopy = copy.deepcopy(currState.rcm) #create deepcopy of rcm,
			currRemainingCities = copy.deepcopy(currState.candidateCities) #and the state's candidate cities

			if len(currRemainingCities) == 0: #WHEN ALL CITIES ARE IN PATH, LEAF HAS BEEN ENCOUNTERED

				fullPath = getPath(currState.partialPath, cities)#get list of city objects, O(n)
				newSolution = TSPSolution(fullPath) #create solution object, O(n)
				totSolutions += 1
				if newSolution.cost < bssf.cost: #if better than bssf,
					print("NEW BSSF:---")
					totSolutions += 1
					bssf = newSolution # assign to bssf
					print(bssf.cost)


			for nextCityIndex in range(len(currRemainingCities)): #EVALUATE ALL CHILDREN STATES, O(n^3) loop; maximum of n descendants, each has rcm
				#constant time space complexity, iteration values are replaced each time, stored value is sent to PQ
				totStates += 1 #total states counter
				nextCity = currRemainingCities[nextCityIndex]
				currStateRcm = copy.deepcopy(currStateRcmCopy) #keep deep copy of parent rcm
				partialPath = currState.partialPath + [nextCity._index] #append the next city to the partial path
				rcm, currCost = reduceCostMatrix(currStateRcm,[currState.currCity, nextCity._index], n, currState.cost) #evaulate current path, O(n^2)

				if currCost < bssf.cost: #only add to queue if partial path is a candidate (< bssf)

					candidateCities = currRemainingCities[:nextCityIndex] + currRemainingCities[nextCityIndex+1:] #remove curr child from list of parent branches
					pathQueue.insert(stateNode(rcm, currCost, partialPath, candidateCities, depth=len(partialPath)-1), c_d=True, naiveEst=naiveEst)
					#^insert candidate state into PQ; takes c_d, naiveEst parameters for different priority approaches, logn insert
				else: #if not eligible, dont add to queue, tick the prunedStates
					prunedStates += 1

				if time.time() - start_time > time_allowance: #if time allowance is reached, quit loop
					timeOut = True

		results['time'] = time.time() - start_time #return all solutions/reporting metrics
		results['count'] = totSolutions
		results['cost'] = bssf.cost
		results['soln'] = bssf
		results['max'] = maxQueueSize
		results['total'] = totStates
		results['pruned'] = prunedStates


		return results

	def fancy( self,time_allowance=60.0 ):
		# use greedy algorithm to get initial solution
		bssf = self.greedy(time_allowance)
		# if the greedy algorithm didn't find a solution (unlikely) return
		if bssf['soln'] is None:
			return bssf

		# get the list of cities
		cities = self._scenario._cities
		# start the counter for number of times two cities weren't swapped
		num_skipped = 0
		# start the variable storing the source city index
		source_city_index = 0
		# calculate how many cities in the route can possibly be switched at a time
		total_possible_switches = len(cities) * (len(cities) - 1)

		# start the timer
		start_time = time.time()

		# iterate source city until swap options are exhausted or time runs out
		while num_skipped < total_possible_switches and time.time() - start_time < time_allowance:
			# iterate through destination cities
			for dest_city_index in range(len(cities)):
				# check if the destination and source city are the same
				# if they are, skip to next destination city
				if source_city_index == dest_city_index:
					continue
				# copy the list of cities from the bssf
				solution_route_copy = bssf['soln'].route.copy()
				# swap the nodes in the source and destination indexes
				solution_route_copy[source_city_index], solution_route_copy[dest_city_index] = solution_route_copy[
																								   dest_city_index], \
																							   solution_route_copy[
																								   source_city_index]
				# construct a new solution using this route
				new_solution = TSPSolution(solution_route_copy)
				# check if the newly created solution is an improvement
				if new_solution.cost < bssf['cost']:
					# set the cost of the new best solution
					bssf['cost'] = new_solution.cost
					# set the new best solution
					bssf['soln'] = new_solution
					# increase the number of solutions found
					bssf['count'] += 1
					# reset the number of skipped comparisons
					num_skipped = 0
				else:
					# this solution was not better, and it will be recorded as a skip
					num_skipped += 1
			# increment the source city index in a way where it will always loop
			# through the possible cities
			source_city_index += 1
			source_city_index %= len(cities)

		# loop end - end timer
		end_time = time.time()

		# update output with correct time
		bssf['time'] = end_time - start_time
		# return solution
		return bssf
		



