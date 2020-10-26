# my own classes
from rectangle import Rectangle

# external dependencies
import numpy as np
import copy
from bokeh.plotting import figure, output_file, show, save
import random
import os
import dxfwrite
from dxfwrite import DXFEngine as dxf

from ezdxf import recover
from ezdxf.addons.drawing import matplotlib

import pandas as pd
import math 

class Error(Exception):
    """Base class for other exceptions"""
    pass

class InvalidGridPositionError(Error):
    """Raised when rectangle has invalid grid position"""
    pass

class StackedGrid(object):
    def __init__(self, width, height, name, brand = "kokos", color = "naturel", stacked_rectangles = [], is_full = False, is_cut = False):
        self.width = width
        self.height = height
        self.name = name
        self.brand = brand
        self.color = color

        self.stacked_rectangles = stacked_rectangles
        self.is_full = is_full
        self.is_cut = is_cut

        self.unstacked_rectangles = []
        
        self.path = "./dxf/" + self.getBrand() + "/" + self.getColor() + "/" + str(self.getWidth()) + "cm"
        self.grid_dxf = self.path + "/grid" + str(name) + ".dxf"

        if not os.path.exists(self.path):
            os.makedirs(self.path)

        self.drawing = dxf.drawing(self.grid_dxf)
        self.base_path = os.path.abspath(os.getcwd())

        self.min_rectangle_width = 100 #cm
        self.min_rectangle_height = 50 #cm
        self.max_rectangle_width = 200 #cm
        self.max_rectangle_height = 320 #cm

    @classmethod
    def fromExcel(cls, file_name):
        df = pd.read_excel(file_name, sheet_name=None)
        df = df['Paklijst']

        df = df.drop([0, 1, 2, 3])
        df.columns = ['Aantal', 'Merk', 'Omschrijving', 'Breedte', 'Lengte', 'Orderdatum', 'Coupage/Batch', 'Ordernummer', 'Klantnaam']

    def getWidth(self):
        return self.width
    
    def setWidth(self, width):
        self.width = width

    def getHeight(self):
        return self.height
    
    def setHeight(self, height):
        self.height = height

    def getName(self):
        return self.name
    
    def setName(self, name):
        self.name = name

    def getBrand(self):
        return self.brand

    def setBrand(self, brand):
        self.brand = brand

    def getColor(self):
        return self.color
    
    def setColor(self, color):
        self.color = color
        
    def getNumStackedRectangles(self):
        return len(self.stacked_rectangles)

    def getStackedRectangles(self):
        return self.stacked_rectangles

    def setStackedRectangles(self, rectangles):
        self.stacked_rectangles = rectangles

    def computeStackingPosition(self, rectangle):
        stacking_position = [self.getWidth(), self.getHeight()]

        for x in reversed(range(int(rectangle.width/2), int(self.getWidth() - rectangle.width/2))):
            for y in reversed(range(int(rectangle.height/2), int(self.getHeight() - rectangle.height/2))):
                position = np.array([x,y])
                rectangle.setPosition(position)
                if self.isValidPosition(rectangle) and np.linalg.norm(position) < np.linalg.norm(stacking_position):
                    stacking_position = position

        return stacking_position

    def checkAndSetFull(self):
        print("Checking if grid " + str(self.getName()) + " is full")
        min_rectangle = Rectangle(self.min_rectangle_width, self.min_rectangle_height, -1)
        min_rectangle.setPosition(self.computeStackingPosition(min_rectangle))

        min_rectangle_rotated = Rectangle(self.min_rectangle_height, self.min_rectangle_width, -1)
        min_rectangle_rotated.setPosition(self.computeStackingPosition(min_rectangle_rotated))

        if self.isValidPosition(min_rectangle) or self.isValidPosition(min_rectangle_rotated):
            self.is_full = False
            print("Grid " + str(self.getName()) + " is not full")
            return False
        else: 
            self.is_full = True
            print("Grid " + str(self.getName()) + " is full")
            return True

    def isFull(self):
        return self.is_full
    
    def isCut(self):
        return self.is_cut
    
    def setCut(self):
        self.is_cut = True
    
    def setUncut(self):
        self.is_cut = False

    def toDict(self):
        return {'name': self.name, 'width': self.width, 'height': self.height, 'stacked_rectangles': [rect.toDict() for rect in self.stacked_rectangles]}

    def toMillimeters(self, variable):
        return variable * 10

    def swap(self, x, y):
        t = x 
        x = y
        y = t

        return x, y

    def toPrimeCenterFormatDxf(self):
        for rectangle in self.stacked_rectangles:

            x = rectangle.getPosition()[0] - rectangle.getWidth()/2
            y = rectangle.getPosition()[1] - rectangle.getHeight()/2
            width = rectangle.getWidth()
            height = rectangle.getHeight()

            x, y = self.swap(x, y)
            width, height = self.swap(width, height)
                        
            bgcolor = random.randint(1,255)
            
            x = self.toMillimeters(x)
            y = self.toMillimeters(y)

            width = self.toMillimeters(width)
            height = self.toMillimeters(height)

            self.drawing.add(dxf.rectangle((x,y), width, height,
                                  bgcolor=bgcolor))

        self.drawing.save()
    
    """
    1) Make an array containing the points of all the vertices in the grid. The x and y values are extracted and the unique x, and y values are calculated. 
    2) Loop over the unique y values and if there are more than two points with the same y value but different x value, use the point with the highest x value as the end point x_1. If the value is lower
    than the current start x value, this is chosen as starting value x_0.  

    3) Loop over the unique x values and if there are more than two points with the same x value but different y value, use the point with the highest y value as y_1. Use the point with the lowest
    y value as y_0
    """
    def removeDuplicateLines(self, for_prime_center=False):            
        
        self.lines = []
        points = []

        for rectangle in self.stacked_rectangles:
            if for_prime_center == True:
                x = rectangle.getPosition()[0] - rectangle.getWidth()/2
                y = rectangle.getPosition()[1] - rectangle.getHeight()/2
                width = rectangle.getWidth()
                height = rectangle.getHeight()

                x, y = self.swap(x, y)
                width, height = self.swap(width, height)
                name = rectangle.getName()

                rectangle = Rectangle(width=width, height=height, name=name, position=[x,y])
                
            top_left, top_right, bottom_left, bottom_right = rectangle.getVertices()

            points.append(tuple(top_left))
            points.append(tuple(top_right))
            points.append(tuple(bottom_left))
            points.append(tuple(bottom_right))

        x_ = [k[0] for k in points]
        y_ = [k[1] for k in points]

        x_unique = np.unique(x_)
        y_unique = np.unique(y_)

        for y in y_unique:
            x_0 = max(x_)
            x_1 = 0
            for point in points:
                if point[1] == y and point[0] > x_1:
                    x_1 = point[0]
                if point[1] == y and point[0] < x_0:
                    x_0 = point[0]

            self.lines.append(dxf.line((x_0, y), (x_1, y)))
                
        for x in x_unique:
            y_0 = max(y_)
            y_1 = 0
            for point in points:
                if point[0] == x and point[1] > y_1:
                    y_1 = point[1]
                if point[0] == x and point[1] < y_0:
                    y_0 = point[1]

            self.lines.append(dxf.line((x, y_0), (x, y_1)))
    
    def toDxf(self, remove_duplicates=False, for_prime_center=False):
        if remove_duplicates == False:
            for rectangle in self.stacked_rectangles:
                x = rectangle.getPosition()[0] - rectangle.getWidth()/2
                y = rectangle.getPosition()[1] - rectangle.getHeight()/2
                width = rectangle.getWidth()
                height = rectangle.getHeight()

                if for_prime_center == True:
                    x = self.toMillimeters(x)
                    y = self.toMillimeters(y)

                    width = self.toMillimeters(width)
                    height = self.toMillimeters(height)

                bgcolor = random.randint(1,255)
                
                self.drawing.add(dxf.rectangle((x,y), width, height,
                                    bgcolor=bgcolor))
        else:
            self.removeDuplicateLines(for_prime_center)
            for line in self.lines:
                self.drawing.add(line)

        self.drawing.save()
    
    def toPdf(self):
        # self.toPrimeCenterFormatDxf()
        self.toDxf()
        dox, auditor = recover.readfile(self.grid_dxf)
        if not auditor.has_errors:
            matplotlib.qsave(dox.modelspace(), './pdf/' + self.getBrand() + '/' + self.getColor() + '/' + str(self.getWidth()) + '/grid_' + str(self.getName()) + '.png')

    def addRectangle(self, rectangle):
        self.stacked_rectangles.append(copy.deepcopy(rectangle))

    def deleteRectangle(self, rectangle):
        for i, stacked_rectangle in enumerate(self.getStackedRectangles()):
            if stacked_rectangle.getName() == rectangle.getName():
                del self.stacked_rectangles[i]
                break

    def isOutOfGrid(self, rectangle):
        if rectangle.getPosition()[0] - rectangle.getWidth()/2 < 0:
            return True
        if rectangle.getPosition()[1] + rectangle.getHeight()/2 > self.getHeight():
            return True
        if rectangle.getPosition()[0] + rectangle.getWidth()/2 > self.getWidth():
            return True
        if rectangle.getPosition()[1] - rectangle.getHeight()/2 < 0:
            return True
    
        return False

    def isValidPosition(self, rectangle):
        if self.isOutOfGrid(rectangle):
            return False

        for i, stacked_rectangle in enumerate(self.stacked_rectangles):
            if rectangle.intersection(stacked_rectangle):
                return False

        return True

    def printStackedRectangles(self):
        for r in self.stacked_rectangles:
            print(r.getPosition())  

    def plot(self):
        print("Plotting grid " + str(self.getName()))

        # file to save the model  
        output_file("plots/stacked_grid_" + str(self.getName()) + ".html")  
            
        # instantiating the figure object  
        graph = figure(title = "Stacked grid " + str(self.getName()), x_range=(0, self.width), y_range=(0, self.height))  

        # name of the x-axis  
        graph.xaxis.axis_label = "x-axis"
            
        # name of the y-axis  
        graph.yaxis.axis_label = "y-axis"
        
        x = []
        y = []
        width = []
        height = []

        for r in self.stacked_rectangles:
            x.append(r.getPosition()[0])
            y.append(r.getPosition()[1])
            width.append(r.getWidth())
            height.append(r.getHeight())
        
        # color value of the rectangle 
        color = ["blue" for x in range(len(self.stacked_rectangles))]
        
        # fill alpha value of the rectangle 
        fill_alpha = np.ones(len(self.stacked_rectangles)) * 0.5
        
        # plotting the graph  
        graph.rect(x, 
                y, 
                width, 
                height, 
                color = color, 
                fill_alpha = fill_alpha)  
            
        # displaying the model  
        # show(graph) 
        save(graph)
