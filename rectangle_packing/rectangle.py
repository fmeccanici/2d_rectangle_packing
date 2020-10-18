import numpy as np
import pickle
import os 

from pathlib import Path

class Rectangle(object):
    def __init__(self, width, height, name, position=np.array([-1, -1]), grid_number=-1, is_stacked=False):
        self.position = np.asarray(position)
        self.width = width
        self.height = height
        self.name = name
        self.grid_number = grid_number
        self.is_stacked = is_stacked

    def getGridNumber(self):
        return self.grid_number

    def setGridNumber(self, grid_number):
        self.grid_number = grid_number

    def isStacked(self):
        return self.is_stacked

    def setStacked(self):
        self.is_stacked = True

    def setUnstacked(self):
        self.is_stacked = False

    def getName(self):
        return self.name
    
    def setName(self, name):
        self.name = name

    def getWidth(self):
        return self.width
    
    def setWidth(self, width):
        self.width = width

    def getHeight(self):
        return self.height

    def setHeight(self, height):
        self.height = height

    def getPosition(self):
        return self.position

    def setPosition(self, position):
        self.position = position

    def getTopLeft(self):   
        return self.getPosition() - np.array([self.getWidth()/2, self.getHeight()/2])
    
    def getBottomRight(self):
        return self.getPosition() + np.array([self.getWidth()/2, self.getHeight()/2])
    
    def getArea(self):
        return self.width * self.height

    def rotate(self):
        width = self.getHeight()
        height = self.getWidth()

        self.setWidth(width)
        self.setHeight(height)
        
    def intersection(self, other):
        if self.getBottomRight()[0] <= other.getTopLeft()[0] or self.getTopLeft()[0] >= other.getBottomRight()[0]:
            return False
        
        if self.getBottomRight()[1] <= other.getTopLeft()[1] or self.getTopLeft()[1] >= other.getBottomRight()[1]:
            return False

        return True
    
    def toDict(self):
        return {'name': self.name, 'width':self.width, 'height': self.height, 'position': self.position}

    