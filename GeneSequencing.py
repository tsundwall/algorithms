#!/usr/bin/python3

from PyQt5.QtCore import QLineF, QPointF

import math
import time
import random
import numpy as np

def evaluate(matrix, indices, loc): #an o(1) operation that returns the cost of an adjacent cell
	indexr, indexc = indices

	if loc == "up": #depending on the loc that is passed in, func will return the respective cell value

		return matrix[(indexr - 1, indexc)]

	elif loc == "left":

		return matrix[(indexr, indexc - 1)]

	elif loc == "diag":

		return matrix[(indexr - 1, indexc - 1)]

	else:

		return "invalid direction"

def diff(str1, str2, i, j, cost_tuple): #evaluates two string positions for a match, o(1)

	match_cost, match_conflict = cost_tuple #unpacks costs of match/non match

	if str1[i] == str2[j]:
		return match_cost

	else:
		return match_conflict

def backtrack(str1, str2, rlength, clength, prevMat, costMat): #an O(n) operation to backtrack through matrix

	alignArr = [] #init alignment array

	start = (rlength, clength) #start at solution cell
	prev = prevMat[start] #init first prev cell

	pointerExists = True

	while pointerExists: #while we are able to backtrack (a prev exists); this is at O(n), since there will be n pointers,
		# and n positions to evaluate
		#everything inside is o(1) since dicts use hashing
		if start[0] != prev[0]:

			if start[1] != prev[1]:

				if costMat[start] - costMat[prev] == -3: #if score is -3, keep

					alignArr.append("keep")

				else:

					alignArr.append("replace") #ow replace

			else:

				alignArr.append("delete")

		else:

			alignArr.append("insert")

		if prev in prevMat: #if previous exists

			start = prev #assign it as the new start
			prev = prevMat[prev] #and find new prev

		else:

			pointerExists = False #otherwise exit w base case

	return alignArr #return array of action strings

def alignSeq(str1, str2, alignArr, cost):  #align the sequences based on alignment array; O(n)

	actionIndex = 0 #init index of change in sequence

	for action in reversed(alignArr): #look through reversed list (O(n)), n times (this is O(2n)) since we reverse the list just once

		if action == "insert": #if insert, insert dash into current index and shift everything right

			str1 = str1[:actionIndex] + "-" + str1[actionIndex:]

		elif action == "delete": #if delete, add dash after current str index

			str2 = str2[:actionIndex] + "-" + str2[actionIndex:]
		#keep/sub actions have no alignment updates necessary
		actionIndex += 1

	return str1, str2, cost #return the aligned strings and pass through the cost since this is what the align() method returns
#to the GUI

def wrapper(str1, str2, align_length, banded=False): #wrapper function for edit distance algo;
	#either an O(nm) or O(kn) algorithm (not banded and banded), where k is the band width

	if len(str1) < align_length: #if sequence is less than the align length, a_l is just the
		#length of the sequence (need a distinct row and column length, which is what maps to
		#m and n in our complexity analysis)
		align_lengthr = len(str1)
	else:
		align_lengthr = align_length

	if len(str2) < align_length:
		align_lengthc = len(str2)
	else:
		align_lengthc = align_length #if they are both large sequences, m=n
	#below inits are o(1)
	costMat = {} #init dict that will store keys as tuples
	prevMat = {} #init dict that will store keys and vals as tuples (backpointers)

	MATCH_COST = -3 #init cost constants
	CONFLICT_COST = 1
	INDEL_COST = 5

	COST_PROFILE = (MATCH_COST, CONFLICT_COST) #cost profile for diff function
	BAND_WIDTH = 7 #this is our fixed k value

	BAND_BUFFER = int((BAND_WIDTH - 1) / 2) #compute buffers; (k/2)-1 entries on either side of diagonal

	directions = ["left", "up", "diag"]  #comparisons ordered by priority

	if banded:
		if align_lengthr != align_lengthc: #if sequences unequal in length (geeneralize)
			return "No Alignment Possible", "No Alignment Possible", math.inf #assume no alignment

		init_length = int(BAND_BUFFER + 1)  # the number of outer entries that are in band

		for r in range(init_length): #init entries in row 0 and column 0 (up to where band exists)
			costMat[(r, 0)] = r * INDEL_COST

		for c in range(init_length):
			costMat[(0, c)] = c * INDEL_COST

		for c in range(1, align_lengthc + 1): #for each column, O(n), evaluate cells within band
			#set band range of column based on current column
			band_range = range(np.maximum(0, c-BAND_BUFFER), np.minimum(c+BAND_BUFFER+1, align_lengthc+1))

			for r in band_range: #this loop will be of size O(k), since only k cells will be evaluated (as defined by range above)
				minCost = np.Inf
				minPrev = None
				#prioritize if statements by left, up, diag
				if (r, c - 1) in costMat: #first must check if lookup key exists in matrix;
					#if not, the lookup is outside of the band, by definition; the following lookups are all o(1)
					cost = evaluate(costMat, (r, c), "left") + INDEL_COST

					if cost < minCost:
						minCost = cost
						minPrev = "left" #because we checked left first, another lookup would have to beat
						#it outright to overwrite these values (this is the first tiebreaker)

				if (r - 1, c) in costMat:

					cost = evaluate(costMat, (r, c), "up") + INDEL_COST

					if cost < minCost:
						minCost = cost
						minPrev = "up"

				if (r - 1, c - 1) in costMat:

					diffscore = diff(str1, str2, r - 1, c - 1, COST_PROFILE)
					cost = evaluate(costMat, (r, c), "diag") + diffscore


					if cost < minCost:
						minCost = cost
						minPrev = "diag"

				if minPrev == "left": #based on minPrev value (best option), set cell value and pointer

					costMat[(r, c)] = minCost
					prevMat[(r, c)] = (r, c - 1)

				elif minPrev == "up":

					costMat[(r, c)] = minCost
					prevMat[(r, c)] = (r - 1, c)

				else:

					costMat[(r, c)] = minCost
					prevMat[(r, c)] = (r - 1, c - 1)

	else: #unbanded, o(mn) algorithm

		for r in range(align_lengthr + 1): #set values of (n,0) and (0,n) entries; these are
			#equivalent to indels, so each increases by indel cost. both are O(n) and O(m) operations
			costMat[(r, 0)] = r * INDEL_COST

		for c in range(align_lengthc + 1):
			costMat[(0, c)] = c * INDEL_COST

		for c in range(1, align_lengthc + 1): #evaluate table by columns, up to align_length entry;
			#this is our "squared" loop, looking at m columns, each of with has n rows => O(mn); all other
			#operations within loops are o(1)
			for r in range(1, align_lengthr + 1):
				#evalute each cell;
				minCost = np.Inf #init a minimum cost and a NULL back pointer
				minPrev = None

				for direction in directions: #o(3) operation looping through the three potential pivots

					if direction == "diag": #if diagonal,

						diffscore = diff(str1, str2, r - 1, c - 1, COST_PROFILE) #get the diff() value,
						cost = evaluate(costMat, (r, c), direction) + diffscore #and sum with cost of diag entry

					else:

						cost = evaluate(costMat, (r, c), direction) + INDEL_COST #if not diag, take prev cost (either left or up) and add 5

					if cost < minCost: #for each iter, if cost is lower than before,
						minCost = cost #set the min cost and direction
						minPrev = direction
				#once true min has been found, set costmatrix and prevmatrix values based on the direction of the min
				if minPrev == "left": #all o(1)

					costMat[(r, c)] = minCost
					prevMat[(r, c)] = (r, c - 1) #left pointer

				elif minPrev == "up":
					costMat[(r, c)] = minCost
					prevMat[(r, c)] = (r - 1, c) #up pointer

				else:

					costMat[(r, c)] = minCost
					prevMat[(r, c)] = (r - 1, c - 1) #diag pointer


	alignArr = backtrack(str1, str2, align_lengthr, align_lengthc, prevMat, costMat)
	return alignSeq(str1, str2, alignArr, costMat[(r, c)])

class GeneSequencing:

	def __init__( self ):
		pass
	
# This is the method called by the GUI.  _seq1_ and _seq2_ are two sequences to be aligned, _banded_ is a boolean that tells
# you whether you should compute a banded alignment or full alignment, and _align_length_ tells you 
# how many base pairs to use in computing the alignment

	def align( self, seq1, seq2, banded, align_length):

		self.banded = banded
		self.MaxCharactersToAlign = align_length
		#run edit distance algo, return sequences and score
		alignment1, alignment2, score = wrapper(seq1, seq2, banded = self.banded, align_length = self.MaxCharactersToAlign) #O(mn) or O(kn)
		#all O(1) below
		alignment1 = alignment1[:100] #truncate alignments
		alignment2 = alignment2[:100]
		print(score)
		print("1")
		print(alignment1)
		print("2")
		print(alignment2)
		return {'align_cost':score, 'seqi_first100':alignment1, 'seqj_first100':alignment2}


