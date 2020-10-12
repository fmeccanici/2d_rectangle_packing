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

class Error(Exception):
    """Base class for other exceptions"""
    pass

class InvalidGridPositionError(Error):
    """Raised when rectangle has invalid grid position"""
    pass

class StackedGrid(object):
    def __init__(self, width, height, name, stacked_rectangles = [], is_full = False, is_cut = False):
        self.width = width
        self.height = height
        self.name = name
        self.stacked_rectangles = stacked_rectangles
        self.is_full = is_full
        self.is_cut = is_cut

        self.unstacked_rectangles = []
        
        self.grid_dxf = "grid" + str(name) + ".dxf"
        self.drawing = dxf.drawing(self.grid_dxf)
        self.base_path = os.path.abspath(os.getcwd())

        self.min_rectangle_width = 100 #cm
        self.min_rectangle_height = 50 #cm
        self.max_rectangle_width = 200 #cm
        self.max_rectangle_height = 1500 #cm

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

    def isFull(self):
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
    
    def isCut(self):
        return self.is_cut
    
    def setCut(self):
        self.is_cut = True
    
    def toDict(self):
        return {'name': self.name, 'width': self.width, 'height': self.height, 'stacked_rectangles': [rect.toDict() for rect in self.stacked_rectangles]}

    def toDxf(self):
        for rectangle in self.stacked_rectangles:
            x = rectangle.getPosition()[0] - rectangle.getWidth()/2
            y = rectangle.getPosition()[1] - rectangle.getHeight()/2
            width = rectangle.getWidth()
            height = rectangle.getHeight()
            bgcolor = random.randint(1,255)
            
            self.drawing.add(dxf.rectangle((x,y), width, height,
                                  bgcolor=bgcolor))

        self.drawing.save()
        
    def addRectangle(self, rectangle):
        self.stacked_rectangles.append(copy.deepcopy(rectangle))

    def isValidPosition(self, rectangle):
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
        output_file("grids/stacked_grid_" + str(self.getName()) + ".html")  
            
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

