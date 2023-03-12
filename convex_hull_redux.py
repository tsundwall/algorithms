from which_pyqt import PYQT_VER

if PYQT_VER == 'PYQT5':
    from PyQt5.QtCore import QLineF, QPointF, QObject
elif PYQT_VER == 'PYQT4':
    from PyQt4.QtCore import QLineF, QPointF, QObject
else:
    raise Exception('Unsupported Version of PyQt: {}'.format(PYQT_VER))

import numpy
import math
import time

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

PAUSE = 0.25

class Line: # class for hull points to be contained in hull linked list
    def __init__(self, value=None):
        self.value = value
        self.next = None
        self.prev = None

    def nextCW(self): #method form of returning next node
        return self.next

    def nextCCW(self): #method form of returning previous node
        return self.prev

    def jumpCW(self, steps): #returns the node a certain number of clockwise steps away from the given node

        curr = self

        for step in range(steps):

            curr = curr.next

        return curr

    def jumpCCW(self, steps): #same as previous method, but for CCW

        curr = self

        for step in range(steps):
            curr = curr.prev

        return curr

class Hull:
    def __init__(self):
        self.head = None
        self.tail = None
        self.length = 0

    def __iter__(self):
        hull = self.head
        while hull:
            yield hull
            hull = hull.next
            if hull == self.tail.next:
                break

    def getLength(self): #returns psuedo length of hull; stops count when it returns to head

        count = 0
        start = self.head.value
        curr = self.head.next
        while curr.value != start:
            count += 1
            curr = curr.next
        return count + 1

    def createHull(self, value): #inits the hull structure, sets value to head and tail
        new_hull = Line(value)
        new_hull.next = None
        new_hull.prev = None
        self.head = new_hull
        self.tail = new_hull
        self.length = 1

    def insertR(self, value): #inserts a new node at the front of the hull list
        new_hull = Line(value)
        self.head.prev = new_hull
        new_hull.next = self.head
        self.head = new_hull
        self.tail.next = self.head
        self.head.prev = self.tail
        self.length += 1

    def getLowestX(self): #method to find leftmost node of a hull
        k = self.getLength()
        curr = self.head
        lowest_x = curr.value.x()
        lowest_x_obj = curr
        curr_x = curr.value.x()
        for each in range(k-1):
            curr = curr.next
            curr_x = curr.value.x()

            if curr_x < lowest_x:
                lowest_x = curr_x
                lowest_x_obj = curr
        return lowest_x_obj

    def get(self, index): #returns node at a certain "index"

        curr = self.head

        for line in range(index):
            curr = curr.next

        return curr

    def peek(self): #prints each node in a hull

        curr = self.head

        for wholeList in range(self.getLength()):
            print(curr.value)
            curr = curr.next

def sortX(rawPoints): #sorts points by ascending x value for use in recursion
###this whole method is O(n); loops and sorts are each O(n)
    xlist = []

    for item in range(len(rawPoints)):

        xlist.append(rawPoints[item].x()) #create a list of x values

    order = numpy.argsort(xlist) #returns array of indices that state where a value would be in a sorted list

    pointsSorted = []

    for item in order: #append final list based on argsort list
        pointsSorted.append(rawPoints[item])

    pointsSortedX = pointsSorted

    return pointsSortedX

def sortCW(points=[], left=[], right=[]): #pass in an x assorted list
###this whole method is O(1); this method will only ever be called for hulls of length 3
    if len(left) == 0: #if a single set of points was passed in, just set value to that
        points = points

    else:
        points = left + right #combine lists if needed

    startPoint = points[len(points) - 1] #take furthest right point

    points = points[:len(points) - 1] #keep rest

    slopeArray = []

    for point in points: #iterate through each point, find slope relative to starting point
        relSlope = (point.y() - startPoint.y()) / (point.x() - startPoint.x())
        slopeArray.append(relSlope)

    pointPositions = numpy.argsort(slopeArray) #get sorted indices
    pointPositions = pointPositions[::-1] #reverse the list

    pointsNew = []

    pointsNew.append(startPoint)

    for point in pointPositions: #order the points
        pointsNew.append(points[point])

    return pointsNew

def connectCW(hull):#connect all points in hull object; will be called at the end of the algorithm
#the time complexity of this method is O(n)
    k = hull.getLength() #each of these calls is O(n)

    polygon = []

    for i in range(k): #O(n); create a line between each set of points in hull

        if i == (k - 1): #when the last node is reached, connect to head
            line = QLineF(hull.get(i).value, hull.get(0).value)
        else:
            line = QLineF(hull.get(i).value, hull.get(i+1).value)

        polygon.append(line)

    return polygon

class ConvexHullSolver(QObject):

    def __init__(self):
        super().__init__()
        self.pause = False

    def showTangent(self, line, color):
        self.view.addLines(line, color)
        if self.pause:
            time.sleep(PAUSE)

    def eraseTangent(self, line):
        self.view.clearLines(line)

    def blinkTangent(self, line, color):
        self.showTangent(line, color)
        self.eraseTangent(line)

    def showHull(self, polygon, color):
        self.view.addLines(polygon, color)
        if self.pause:
            time.sleep(PAUSE)

    def eraseHull(self, polygon):
        self.view.clearLines(polygon)

    def showText(self, text):
        self.view.displayStatusText(text)

    def compute_hull(self, points, pause, view):
        self.pause = pause
        self.view = view
        assert (type(points) == list and type(points[0]) == QPointF)

        t1 = time.time()

        points = sortX(points) #O(n)

        t2 = time.time()

        t3 = time.time()

        polygonPoints = solver(points)

        polygon = connectCW(polygonPoints) #connect all points, O(n)

        t4 = time.time()

        self.showHull(polygon, RED)
        self.showText('Time Elapsed (Convex Hull): {:3.3f} sec'.format(t4 - t3))

def solver(points):

    if len(points) == 1: #if the sublist is length 1, simply return the QPointF object

        return points[0]

    k = math.floor(len(points) / 2) #find halfway point of list; this splits into b=2 problems
    left = points[:k]
    right = points[k:]

    lefthull = solver(left) #DIVIDE AND CONQUER; run each half recursively, in the master theorem equation, this is an a = 2 branching factor
    righthull = solver(right)

    if (type(lefthull) == QPointF) and (type(righthull) == QPointF): #if both hulls are just point objects (aka each are size of 1), init a hull object
        hull = Hull()
        hull.createHull(lefthull)
        hull.insertR(righthull) #add the righthull to the head of the hull object

        return hull

    elif type(lefthull) == QPointF: #if only the lefthull is length 1, O(1)

        p0 = righthull.get(0).value
        p1 = righthull.get(1).value
        order = sortCW([lefthull, p1, p0]) #get all 3 points, sort them clockwise

        hull = Hull()
        hull.createHull(order[2])
        hull.insertR(order[1])
        hull.insertR(order[0]) #create a hull and order them at the most fundamental level

        return hull

    elif type(righthull) == QPointF: #right hull is length 1, O(1)

        p0 = lefthull.get(0)
        p1 = lefthull.get(1)
        order = sortCW([righthull, p1, p0])

        hull = Hull()
        hull.createHull(order[0])
        hull.insertL(order[1])
        hull.insertL(order[2]) #opposite insertion order of previous case

        return hull

    else: #if a hull is bigger than 3, it will process here
        lefthullEntry = lefthull.head #set entry points for tangent search
        righthullEntry = righthull.getLowestX()#O(n) to find lowest X

        leftPointUT = lefthullEntry #init upper tangent points as the entry points
        rightPointUT = righthullEntry
        rightShiftsUT = 0 #counters for how many shifts occur
        leftShiftsUT = 0

        complete = 0

        while not complete: #this is technically O(n); iterate between left and right pivots to find upper tangent; stop when nothing changes

            rightChanged = 0
            leftChanged = 0

            initialSlopeUT = (rightPointUT.value.y() - leftPointUT.value.y()) / (rightPointUT.value.x() - leftPointUT.value.x()) #set initial slope of current tangent points (will start at inner points)

            pivotSlopeUT = (rightPointUT.nextCW().value.y() - leftPointUT.value.y()) / (rightPointUT.nextCW().value.x() - leftPointUT.value.x()) #pivot on left point and go to next clockwise right point

            if pivotSlopeUT > initialSlopeUT: #if this slope is bigger than previous, set new right point as the right upper tangent point
                rightChanged = 1
                rightShiftsUT += 1 #move counter for each right shift
                rightPointUT = rightPointUT.nextCW()

            initialSlopeUT = (rightPointUT.value.y() - leftPointUT.value.y()) / (rightPointUT.value.x() - leftPointUT.value.x()) #re-init "initial" slope

            pivotSlopeUT = (rightPointUT.value.y() - leftPointUT.nextCCW().value.y()) / (rightPointUT.value.x() - leftPointUT.nextCCW().value.x()) #pivot on the right, move CCW on the left

            if pivotSlopeUT < initialSlopeUT: #if the slope decreases, set as left UT point
                leftChanged = 1
                leftShiftsUT += 1
                leftPointUT = leftPointUT.nextCCW()

            if leftChanged + rightChanged == 0: #if the iteration saw now changes, quit

                complete = 1

        upperTangent = [lefthullEntry.jumpCCW(leftShiftsUT),righthullEntry.jumpCW(rightShiftsUT)] #quick storage for tangent points; jump() functions use # of shifts to determine how many points away from inner points we moved

        # we now do the same thing for the lower tangent by reseting variables, and flippins signs/directions
        leftPointLT = lefthullEntry
        rightPointLT = righthullEntry
        rightShiftsLT = 0
        leftShiftsLT = 0

        complete = 0 #reset while loop exit case

        while not complete: #O(n)

            rightChanged = 0
            leftChanged = 0

            initialSlopeLT = (rightPointLT.value.y() - leftPointLT.value.y()) / (rightPointLT.value.x() - leftPointLT.value.x()) #first lower tangent line will be inner points again

            pivotSlopeLT = (rightPointLT.nextCCW().value.y() - leftPointLT.value.y()) / (rightPointLT.nextCCW().value.x() - leftPointLT.value.x()) #pivot left

            if pivotSlopeLT < initialSlopeLT: #if slope decreased, set new right LT point
                rightChanged = 1
                rightShiftsLT += 1
                rightPointLT = rightPointLT.nextCCW()

            initialSlopeLT = (rightPointLT.value.y() - leftPointLT.value.y()) / (rightPointLT.value.x() - leftPointLT.value.x()) #set new "current" tangent line

            pivotSlopeLT = (rightPointLT.value.y() - leftPointLT.nextCW().value.y()) / (rightPointLT.value.x() - leftPointLT.nextCW().value.x()) #pivot right

            if pivotSlopeLT > initialSlopeLT:#if slope increased, set new left LT point
                leftChanged = 1
                leftShiftsLT += 1
                leftPointLT = leftPointLT.nextCW()

            if leftChanged + rightChanged == 0: #again, do this until no more shifts are made
                complete = 1

        lowerTangent = [righthullEntry.jumpCCW(rightShiftsLT), lefthullEntry.jumpCW(leftShiftsLT)] #store nodes of tangent line

        upperTangent[0].next = upperTangent[1] #to remove old nodes, simply set the next/prev attributes of the tangent node to the other tangent node
        upperTangent[1].prev = upperTangent[0]
        lowerTangent[0].next = lowerTangent[1]
        lowerTangent[1].prev = lowerTangent[0]

        return righthull




