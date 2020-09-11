import numpy as np

class Rectangle(object):
    def __init__(self, position, width, height):
        self.position = position
        self.width = width
        self.height = height
    
    def getWidth(self):
        return self.width
    
    def getHeight(self):
        return self.height

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
        
    def intersection(self, other):
        if self.getBottomRight()[0] <= other.getTopLeft()[0] or self.getTopLeft()[0] >= other.getBottomRight()[0]:
            return False
        
        if self.getBottomRight()[1] <= other.getTopLeft()[1] or self.getTopLeft()[1] >= other.getBottomRight()[1]:
            return False

        return True
    
    