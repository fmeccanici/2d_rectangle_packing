# my own classes
from rectangle_packing.rectangle import Rectangle
from rectangle_packing.helper import Helper
from rectangle_packing.zcc_creator import ZccCreator

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
    def __init__(self, width=-1, height=-1, name="-1", article_name='default', material='kokos', brand = "kokos", color = "naturel", stacked_rectangles = [], is_full = False, is_cut = False):
        self.setWidth(width)
        self.setName(name)
        self.setHeight(height)
        self.setArticleName(article_name)
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

    def getDxfFileName(self):
        hour = Helper.getCurrentHour()
        return str(hour) + "h" + "_" + str(self.getArticleName()) + "_" + str(self.getWidth()) + "cm" + "_batch_" + str(self.getName()) + ".dxf"

    def createDxfFilePath(self):
        dxf_path = Helper.createAndGetDxfFolder()
        hour = Helper.getCurrentHour()
        print("Article name for export dxf = " + str(self.getArticleName()))
        # self.dxf_file_path = dxf_path + "/" + str(hour) + "h" + "_" + self.getBrand() + "_" + self.getColor() + "_" + str(self.getWidth()) + "cm" + ".dxf"
        self.dxf_file_path = dxf_path + "/" + str(hour) + "h" + "_" + self.getArticleName() + "_" + str(self.getWidth()) + "cm" + "_batch_" + str(self.getName()) + ".dxf"
        
    def getWidth(self):
        return self.width
    
    def setWidth(self, width):
        self.width = int(width)

    def getHeight(self):
        return self.height
    
    def setHeight(self, height):
        print("Setting height of grid " + str(self.getName()) + " to " + str(height))
        self.height = int(height)

    def getName(self):
        return self.name
    
    def setName(self, name):
        self.name = int(name)

    def getMaterial(self):
        return self.material

    def setMaterial(self, material):
        self.material = material

    def getArticleName(self):
        return self.article_name

    def setArticleName(self, article_name):
        print("Setting article name of grid " + str(self.getName()) +  " to " + str(article_name))
        self.article_name = article_name

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

        for rectangle in self.stacked_rectangles:
            uncut_area -= rectangle.getArea()

        return uncut_area
    
    def getArea(self):
        return self.width * self.height

    def getHighestVerticalPoint(self):
        highest_vertical_point = 0
        for rectangle in self.stacked_rectangles:
            vertical_point = rectangle.getTopLeft()[1]

            if vertical_point > highest_vertical_point:
                highest_vertical_point = vertical_point 

        print("Highest vertical point = " + str(highest_vertical_point))
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

    def toDxf(self, for_prime_center=False):
        try:

            self.addRectanglesToDxf(for_prime_center)
            if for_prime_center:
                self.addLargeHorizontalLineAtTop()

            self.dxf_drawing.save()
        except PermissionError:
            print("DXF file opened in another program")
    
    def addLargeHorizontalLineAtTop(self):
        y_start = Helper.toMillimeters(self.getHighestVerticalPoint())
        x_start = 0
        y_end = Helper.toMillimeters(self.getHighestVerticalPoint())
        x_end = Helper.toMillimeters(self.getWidth() + 20)

        line = dxf.line((y_start, x_start), (y_end, x_end))
        self.dxf_drawing.add(line)

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

    def addLinesToDxf(self):
        for line in self.lines:
            self.dxf_drawing.add(line)

    def addRectanglesToDxf(self, for_prime_center):
        for rectangle in self.stacked_rectangles:
            rectangle_dxf = rectangle.getRectangleDxf(for_prime_center)
            label_dxf = rectangle.getLabelDxf(for_prime_center)
            self.dxf_drawing.add(rectangle_dxf)
            self.dxf_drawing.add(label_dxf)
            
    def toPdf(self):
        self.toDxf(remove_duplicates=False, for_prime_center=False)
        dox, auditor = recover.readfile(self.dxf_file_path)
        if not auditor.has_errors:
            file_path = './pdf/' + self.getBrand() + '/' + self.getColor() + '/' + str(self.getWidth()) 
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            
            file_name = '/grid_' + str(self.getName()) + '.png'
            matplotlib.qsave(dox.modelspace(), file_path + file_name)

    def addRectangle(self, rectangle):
        self.stacked_rectangles.append(copy.deepcopy(rectangle))

    def removeRectangle(self, rectangle):
        for i, stacked_rectangle in enumerate(self.getStackedRectangles()):
            if stacked_rectangle.getName() == rectangle.getName():
                print("Removed " + str(self.stacked_rectangles[i].getName()) + " from grid " + str(self.getName()))
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
    
    def toZcc(self):
        self.getHighestVerticalPoint()
        self.zcc_creator = ZccCreator(self.getMaterial(), self.getDxfFileName())
        self.getHighestVerticalPoint()

        self.zcc_creator.addGrid(self)
        self.zcc_creator.save()
        self.getHighestVerticalPoint()
