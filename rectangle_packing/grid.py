# my own classes
from rectangle_packing.rectangle import Rectangle
from rectangle_packing.helper import Helper

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
import datetime

class Error(Exception):
    """Base class for other exceptions"""
    pass

class InvalidGridPositionError(Error):
    """Raised when rectangle has invalid grid position"""
    pass

class Grid(object):
    def __init__(self, width=-1, height=-1, name="-1", material='kokos', brand = "kokos", color = "naturel", stacked_rectangles = [], is_full = False, is_cut = False):
        self.setWidth(width)
        self.setHeight(height)
        self.setName(name)
        self.setMaterial(material)
        self.setBrand(brand)
        self.setColor(color)
        self.setStackedRectangles(stacked_rectangles)

        self.is_full = is_full
        self.is_cut = is_cut

        self.initEmptyDxfDrawing()
        
        # used for removing duplicates
        self.points = []
        self.lines = []

    def setDxfDrawing(self, path, file_name):
        self.dxf_file_path = path + file_name
        self.dxf_drawing = dxf.drawing(self.dxf_file_path)

    def initEmptyDxfDrawing(self):
        self.createDxfFilePath()
        self.dxf_drawing = dxf.drawing(self.dxf_file_path)

    def createDxfFilePath(self):
        dxf_path = Helper.createAndGetDxfFolder()
        hour = Helper.getCurrentHour()
        self.dxf_file_path = dxf_path + "/" + str(hour) + "h" + "_" + self.getBrand() + "_" + self.getColor() + "_" + str(self.getWidth()) + "cm" + ".dxf"
        # self.dxf_file_path = dxf_path + "/" + str(hour) + "h" + "_" + self.getMaterial() + "_" + str(self.getWidth()) + "cm" + ".dxf"
        
    def getWidth(self):
        return self.width
    
    def setWidth(self, width):
        self.width = int(width)

    def getHeight(self):
        return self.height
    
    def setHeight(self, height):
        self.height = int(height)

    def getName(self):
        return self.name
    
    def setName(self, name):
        self.name = int(name)

    def getMaterial(self):
        return self.material

    def setMaterial(self, material):
        self.material = material

    def getBrand(self):
        return self.brand

    def setBrand(self, brand):
        self.brand = str(brand)

    def getColor(self):
        return self.color
    
    def setColor(self, color):
        self.color = str(color)
        
    def getNumStackedRectangles(self):
        return len(self.stacked_rectangles)

    def getStackedRectangles(self):
        return self.stacked_rectangles

    def setStackedRectangles(self, rectangles):
        self.stacked_rectangles = rectangles

    def isEmpty(self):
        is_empty = (len(self.stacked_rectangles) == 0)
        print("Grid empty: " + str(is_empty))
        print(str(len(self.stacked_rectangles)) + " rectangles")
        return is_empty

    def empty(self):
        self.stacked_rectangles = []
        
    def isFull(self):
        return self.is_full
    
    def isCut(self):
        return self.is_cut
    
    def setCut(self):
        self.is_cut = True
    
    def setUncut(self):
        self.is_cut = False

    def getUncutArea(self):
        uncut_area = self.getWidth() * self.getHighestVerticalPoint()

        # print("Uncut area")
        # print(uncut_area)
        # print(self.getWidth())
        # print(self.getHighestVerticalPoint())
        # print()
        for rectangle in self.stacked_rectangles:
            # print("r width = " + str(rectangle.getWidth()))
            # print("r height = " + str(rectangle.getHeight()))
            uncut_area -= rectangle.getArea()
        # print(uncut_area)

        return uncut_area
    
    def getArea(self):
        return self.width * self.height

    def getHighestVerticalPoint(self):
        highest_vertical_point = 0
        for rectangle in self.stacked_rectangles:
            # print()
            # print(rectangle.getTopLeft()[1])
            # print()
            vertical_point = rectangle.getTopLeft()[1]

            if vertical_point > highest_vertical_point:
                highest_vertical_point = vertical_point 

        return highest_vertical_point
        
    def isValidPosition(self, rectangle):
        if self.isOutOfGrid(rectangle):
            return False
        
        for stacked_rectangle in self.stacked_rectangles:
            if rectangle.intersection(stacked_rectangle):
                return False
                
        return True
    
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

    def toDxf(self, remove_duplicates=True, for_prime_center=False):
        try:
            if remove_duplicates == True:
                self.removeDuplicateLines(for_prime_center)
                self.addLinesToDxf()            
            else:
                self.addRectanglesToDxf(for_prime_center)

            self.dxf_drawing.save()
        except PermissionError:
            print("DXF file opened in another program")
    """
    1) Make an array containing the points of all the vertices in the grid. The x and y values are extracted and the unique x, and y values are calculated. 
    2) Loop over the unique y values and if there are more than two points with the same y value but different x value, use the point with the highest x value as the end point x_end. If the value is lower
    than the current start x value, this is chosen as starting value x_start.  
    3) Loop over the unique x values and if there are more than two points with the same x value but different y value, use the point with the highest y value as y_end. Use the point with the lowest
    y value as y_start
    """
    def removeDuplicateLines(self, for_prime_center=False):            
        self.lines = []        
        self.points = []

        self.convertRectanglesToPoints()
        self.x_, self.y_ = self.getXYfromPointsAndRound()

        self.x_unique = self.getUniqueValues(self.x_)
        self.y_unique = self.getUniqueValues(self.y_)

        self.removeDuplicateVerticalLines(for_prime_center)
        self.removeDuplicateHorizontalLines(for_prime_center)

    def convertRectanglesToPoints(self):
        for rectangle in self.stacked_rectangles:
            top_left, top_right, bottom_left, bottom_right = rectangle.getVertices()
            self.points.append(tuple(top_left))
            self.points.append(tuple(top_right))
            self.points.append(tuple(bottom_left))
            self.points.append(tuple(bottom_right))

    def getXYfromPointsAndRound(self):
        x_ = [round(k[0], 2) for k in self.points]
        y_ = [round(k[1], 2) for k in self.points]

        return x_, y_
    
    def getUniqueValues(self, array):
        return np.unique(array)

    def removeDuplicateVerticalLines(self, for_prime_center):

        for y in self.y_unique:
            x_start = max(self.x_)
            x_end = 0
            for point in self.points:
                if round(point[1], 2) == y and round(point[0], 2) > x_end:
                    x_end = round(point[0], 2)
                if round(point[1], 2) == y and round(point[0], 2) < x_start:
                    x_start = round(point[0], 2)

            if for_prime_center == True:
                x_start = Helper.toMillimeters(x_start)
                x_end = Helper.toMillimeters(x_end)
                y = Helper.toMillimeters(y)
                self.lines.append(dxf.line((y, x_start), (y, x_end)))
            else:
                self.lines.append(dxf.line((x_start, y), (x_end, y)))
            
    def removeDuplicateHorizontalLines(self, for_prime_center):
        for x in self.x_unique:
            y_start = max(self.y_)
            y_end = 0
            for point in self.points:
                if round(point[0], 2) == x and round(point[1], 2) > y_end:
                    y_end = round(point[1], 2)
                if round(point[0], 2) == x and round(point[1], 2) < y_start:
                    y_start = round(point[1], 2)

            if for_prime_center == True:
                y_start = Helper.toMillimeters(y_start)
                y_end = Helper.toMillimeters(y_end)
                x = Helper.toMillimeters(x)
                self.lines.append(dxf.line((y_start, x), (y_end, x)))
            else:
                self.lines.append(dxf.line((x, y_start), (x, y_end)))

    def addLinesToDxf(self):
        for line in self.lines:
            self.dxf_drawing.add(line)

    def addRectanglesToDxf(self, for_prime_center):
        for rectangle in self.stacked_rectangles:
            rectangle_dxf = rectangle.getRectangleDxf()
            label_dxf = rectangle.getLabelDxf()
            self.dxf_drawing.add(rectangle_dxf)
            self.dxf_drawing.add(label_dxf)
            
    def toPdf(self):
        self.toDxf(remove_duplicates=False)
        dox, auditor = recover.readfile(self.dxf_file_path)
        if not auditor.has_errors:
            file_path = './pdf/' + self.getBrand() + '/' + self.getColor() + '/' + str(self.getWidth()) 
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            
            file_name = '/grid_' + str(self.getName()) + '.png'
            matplotlib.qsave(dox.modelspace(), file_path + file_name)

    def addRectangle(self, rectangle):
        self.stacked_rectangles.append(copy.deepcopy(rectangle))

    def deleteRectangle(self, rectangle):
        for i, stacked_rectangle in enumerate(self.getStackedRectangles()):
            if stacked_rectangle.getName() == rectangle.getName():
                del self.stacked_rectangles[i]
                break

    def printStackedRectangles(self):
        for r in self.stacked_rectangles:
            print(r.getPosition())  

    def toHtml(self):
        print("Plotting grid " + str(self.getName()))
        html_path = './html/'

        if not os.path.exists(html_path):
            os.makedirs(html_path)
        
        # file to save the model  
        output_file(html_path + "grid_" + str(self.getName()) + ".html")  
            
        # instantiating the figure object  
        graph = figure(title = "Grid " + str(self.getName()), x_range=(0, self.width), y_range=(0, self.height))  

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