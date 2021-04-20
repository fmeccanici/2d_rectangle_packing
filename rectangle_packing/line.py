import numpy as np
import copy

class Error(Exception):
    """Base class for other exceptions"""
    pass

class StartPointCannotBeLargerThanEndPointException(Error):
    """Raised when start point has larger x or y coordinate than end point"""
    pass

class StartAndEndPointAreSameException(Error):
    """Raised when start point and end point are the same"""
    pass

class Line(object):

    # start point is always the point with the 
    def __init__(self, start_point=np.array([0, 0]), end_point=np.array([1, 1])):

        if (start_point[0] > end_point[0]) or (start_point[1] > end_point[1]):
            raise StartPointCannotBeLargerThanEndPointException
        
        if (start_point[0] == end_point[0] and start_point[1] == end_point[1]):
            raise StartAndEndPointAreTheSameException

        self.start_point = copy.deepcopy(start_point)
        self.end_point = copy.deepcopy(end_point)

    def __str__(self):
        return "(" + str(self.start_point[0]) + ", " + str(self.start_point[1]) + ") --> (" + str(self.end_point[0]) + ", " + str(self.end_point[1]) + ")"

    def __eq__(self, other):
        return (self.start_point[0] == other.start_point[0] and self.end_point[0] == other.end_point[0]) and ((self.start_point[1] == other.start_point[1] and self.end_point[1] == other.end_point[1]))

    def setStartPoint(self, start_point):
        self.start_point = copy.deepcopy(start_point)

    def setEndPoint(self, end_point):
        self.end_point = copy.deepcopy(end_point)

    """
    Resolves overlap with other line and returns 1 line or 2 Lines if no overlap
    :param others: other Line object
    :returns: 1 Line
    """
    def resolveOverlap(self, other):
        if self.completelyOverlaps(other):

            if self.lenght > other.length:
                return self
            else:
                return other
        
        elif self.partiallyOverlapsType1(other):
            return Line(other.start_point, self.end_point)

        elif self.partiallyOverlapsType2(other):
            return Line(self.start_point, other.end_point)

        else:
            return self, other

    def overlaps(self, other):

        if self.completelyOverlaps(other) or self.partiallyOverlapsType1(other) or self.partiallyOverlapsType2(other):
            return True

    # this line 
    # --------
    # other line
    # ----------------
    def completelyOverlaps(self, other):

        # rounding is needed
        # otherwise lines with same y values are not detected properly
        # because there can be a slight difference of e.g. 0.0001
        start_1_x = round(self.start_point[0], 2)
        start_1_y = round(self.start_point[1], 2)

        end_1_x = round(self.end_point[0], 2)
        end_1_y = round(self.end_point[1], 2)      

        start_2_x = round(other.start_point[0], 2)
        start_2_y = round(other.start_point[1], 2)

        end_2_x = round(other.end_point[0], 2)
        end_2_y = round(other.end_point[1], 2)      

        if (start_1_x >= start_2_x) and (end_1_x <= end_2_x):
            if (start_1_y == start_2_y and end_1_y == end_2_y):
                return True
        elif (start_1_y >= start_2_y) and (end_1_y <= end_2_y):
            if (start_1_x == start_2_x and end_1_x == end_2_x):
                return True

        return False

    # this line 
    #         ---------------------
    # other line
    # ----------------
    def partiallyOverlapsType1(self, other):

        if (self.start_point[0] > other.start_point[0] and self.start_point[0] < other.end_point[0]) and (self.end_point[0] > other.end_point[0]):
            return True
        
        if (self.start_point[1] > other.start_point[1] and self.start_point[1] < other.end_point[1]) and (self.end_point[1] > other.end_point[1]):
            return True

    # this line 
    # ----------------
    # other line
    #            ----------------
    def partiallyOverlapsType2(self, other):
        if (self.start_point[0] < other.start_point[0]) and (self.end_point[0] > other.start_point[0]):
            return True

        if (self.start_point[1] < other.start_point[1]) and (self.end_point[1] > other.start_point[1]):
            return True

    def length(self):
        dist_x = abs(self.self.end_point[0] - self.start_point[0])
        dist_y = abs(self.self.end_point[1] - self.start_point[1])
        dist_x_squared = dist_x ** 2
        dist_y_squared = dist_y ** 2
        line_length = math.sqrt(dist_x_squared + dist_y_squared)

        return line_length
    
