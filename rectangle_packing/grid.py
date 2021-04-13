# my own classes
from rectangle_packing.rectangle import Rectangle
from rectangle_packing.helper import Helper
from rectangle_packing.zcc_creator import ZccCreator
from rectangle_packing.line import Line

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
        self.dxf_lines_without_overlap = []
        self.lines_without_overlap = []

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
                # print('Intersection with ' + str(stacked_rectangle.getName()))
                # print(stacked_rectangle.getWidth())
                # print(rectangle.getWidth())

                # print(stacked_rectangle.getHeight())
                # print(rectangle.getHeight())

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

    def toDxf(self, for_prime_center=False, remove_overlap=True):
        try:
            if remove_overlap == True:
                self.removeOverlappingLines()
                self.addLinesToDxf()
                self.addLabelsToDxf()

            if for_prime_center:
                self.addLargeHorizontalLineAtTop()

            self.dxf_drawing.save()
            print("Lines count is " + str(len(self.dxf_lines_without_overlap)))

        except PermissionError:
            print("DXF file opened in another program")
    
    def isHeighestLine(self, line):
        y_heighest = self.getHighestVerticalPoint()
        
        if line.start_point[1] == y_heighest and line.end_point[1] == y_heighest:
            return True
        else: 
            return False
        
    def addLargeHorizontalLineAtTop(self):
        y_start = Helper.toMillimeters(self.getHighestVerticalPoint())
        x_start = 0
        y_end = Helper.toMillimeters(self.getHighestVerticalPoint())
        x_end = Helper.toMillimeters(self.getWidth() + 20)

        line = dxf.line((y_start, x_start), (y_end, x_end))
        self.dxf_drawing.add(line)
        # self.lines_without_overlap.append(line)

    def convertRectanglesToLines(self):
        self.lines = []

        for rectangle in self.stacked_rectangles:
            self.lines.extend(rectangle.getLines())

    def getVerticalLinesPerXValue(self, x):
        result = []

        for line in self.lines:
            if line.start_point[0] == x and line.end_point[0] == x:
                result.append(line)

        return result

    def getHorizontalLinesPerYValue(self, y):
        result = []

        for line in self.lines:
            if line.start_point[1] == y and line.end_point[1] == y:
                result.append(line)

        return result

    """
    1) Make an array containing the points of all the vertices in the grid. The x and y values are extracted and the unique x, and y values are calculated. 
    2) Loop over the unique y values and if there are more than two points with the same y value but different x value, use the point with the highest x value as the end point x_end. If the value is lower
    than the current start x value, this is chosen as starting value x_start.  
    3) Loop over the unique x values and if there are more than two points with the same x value but different y value, use the point with the highest y value as y_end. Use the point with the lowest
    y value as y_start
    """
    def removeOverlappingLines(self, for_prime_center=True):            
        self.points = []
        self.lines = []

        self.convertRectanglesToLines()
        self.convertRectanglesToPoints()

        self.x_, self.y_ = self.getXYfromPointsAndRound()

        self.x_unique = self.getUniqueValues(self.x_)
        self.y_unique = self.getUniqueValues(self.y_)

        self.removeOverlappingHorizontalLines(for_prime_center)
        self.removeOverlappingVerticalLines(for_prime_center)

        print([l.start_point for l in self.lines_without_overlap])
        print([l.end_point for l in self.lines_without_overlap])

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

    def thereAreOverlappingLines(self, lines):
        if len(lines) == 1:
            return False

        for l1 in lines:
            for l2 in lines:
                if l1.overlaps(l2):
                    return True
        
        return False

    def removeOverlappingHorizontalLines(self, for_prime_center):
        for y in self.y_unique:
            horizontal_lines = self.getHorizontalLinesPerYValue(y)

            i = 0
            j = 1
            
            while self.thereAreOverlappingLines(horizontal_lines):
                
                l1 = horizontal_lines[i]
                l2 = horizontal_lines[j]
                
                if i != j:
                    if l1.overlaps(l2):
                        if l2.end_point[0] > l1.end_point[0]:
                            l1.setEndPoint(l2.end_point)

                        if l2.start_point[0] < l1.start_point[0]:
                            l1.setStartPoint(l2.start_point)

                        del horizontal_lines[j]

                        i = 0
                        j = 1
                    else:
                        print(len(horizontal_lines))
                        if (j + 1 >= len(horizontal_lines)):
                            if (i + 1 >= len(horizontal_lines)):
                                break
                            else:
                                print('increment i to ' + str(i + 1))
                                i += 1
                                j = 0
                        else:
                            print('increment j to ' + str(j + 1))
                            j += 1
                else:
                    print(len(horizontal_lines))
                    if (j + 1 >= len(horizontal_lines)):
                        if (i + 1 >= len(horizontal_lines)):
                            break
                        else:
                            print('increment i to ' + str(i + 1))
                            i += 1
                            j = 0
                    else:
                        print('increment j to ' + str(j + 1))
                        j += 1            
            

            if for_prime_center == True:
                for line in horizontal_lines:
                    print(self.isHeighestLine(line))
                    if self.isHeighestLine(line):
                        print('heighest line is ' + str(line.start_point))
                        continue

                    new_line = Line()
                    new_line.setStartPoint([Helper.toMillimeters(line.start_point[1]), Helper.toMillimeters(line.start_point[0])])
                    new_line.setEndPoint([Helper.toMillimeters(line.end_point[1]), Helper.toMillimeters(line.end_point[0])])

                    print('Setting start point to ' + str(line.start_point))
                    print('Setting end point to ' + str(line.end_point))

                    y = Helper.toMillimeters(y)
                    
                    self.lines_without_overlap.append(new_line)
                    self.dxf_lines_without_overlap.append(dxf.line((y, new_line.start_point[0]), (y, new_line.end_point[0])))
            else:
                for line in horizontal_lines:
                    if self.isHeighestLine(line):
                        continue
                    
                    self.lines_without_overlap.append(line)
                    self.dxf_lines_without_overlap.append(dxf.line((line.start_point[0], y), (line.end_point[0], y)))

    def removeOverlappingVerticalLines(self, for_prime_center):

        for x in self.x_unique:
            vertical_lines = self.getVerticalLinesPerXValue(x)

            i = 0
            j = 1

            while self.thereAreOverlappingLines(vertical_lines):
                l1 = vertical_lines[i]
                l2 = vertical_lines[j]
                
                if i != j:
                    if l1.overlaps(l2):
                        if l2.end_point[1] > l1.end_point[1]:
                            l1.setEndPoint(l2.end_point)

                        if l2.start_point[1] < l1.start_point[1]:
                            l1.setStartPoint(l2.start_point)

                        del vertical_lines[j]

                        i = 0
                        j = 1
                    else:
                        print(len(vertical_lines))
                        if (j + 1 >= len(vertical_lines)):
                            if (i + 1 >= len(vertical_lines)):
                                break
                            else:
                                print('increment i to ' + str(i + 1))
                                i += 1
                                j = 0
                        else:
                            print('increment j to ' + str(j + 1))
                            j += 1
                else:
                    print(len(vertical_lines))
                    if (j + 1 >= len(vertical_lines)):
                        if (i + 1 >= len(vertical_lines)):
                            break
                        else:
                            print('increment i to ' + str(i + 1))
                            i += 1
                            j = 0
                    else:
                        print('increment j to ' + str(j + 1))
                        j += 1            
            

            if for_prime_center == True:
                for line in vertical_lines:
                    print(line.start_point)
                    print(line.end_point)

                    new_line = Line()
                    new_line.setStartPoint([Helper.toMillimeters(line.start_point[1]), Helper.toMillimeters(line.start_point[0])])
                    new_line.setEndPoint([Helper.toMillimeters(line.end_point[1]), Helper.toMillimeters(line.end_point[0])])    

                    x = Helper.toMillimeters(x)
                    print('Setting start point to ' + str(line.start_point))
                    print('Setting end point to ' + str(line.end_point))

                    self.lines_without_overlap.append(new_line)
                    self.dxf_lines_without_overlap.append(dxf.line((new_line.start_point[1], x), (new_line.end_point[1], x)))
            else:
                for line in vertical_lines:
                    self.lines_without_overlap.append(line)
                    self.dxf_lines_without_overlap.append(dxf.line((x, line.start_point[1]), (x, line.end_point[1])))
            
    def addLinesToDxf(self, for_prime_center = True):
        for line in self.dxf_lines_without_overlap:
            self.dxf_drawing.add(line)

    def addLabelsToDxf(self, for_prime_center = True):
        for rectangle in self.stacked_rectangles:
            label_dxf = rectangle.getLabelDxf(for_prime_center)
            self.dxf_drawing.add(label_dxf)

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
