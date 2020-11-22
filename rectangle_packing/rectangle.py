# my own classes
from rectangle_packing.helper import Helper

# external dependencies
import numpy as np
from pathlib import Path
from dxfwrite import DXFEngine as dxf
import random

class Rectangle(object):
    def __init__(self, width=-1, height=-1, name="-1", brand='kokos', color='naturel', grid_width=100, position=np.array([-1, -1]), grid_number=-1, is_stacked=False, quantity=1, client_name='', coupage_batch="batch"):
        self.position = np.asarray(position)
        self.width = width
        self.height = height
        self.name = name
        self.brand = brand
        self.color = color
        self.grid_width = grid_width
        self.quantity = quantity 
        self.client_name = client_name
        self.coupage_batch = coupage_batch

        self.grid_number = grid_number
        self.is_stacked = is_stacked

        self.initEmptyDxfDrawing()

    def initEmptyDxfDrawing(self):
        hour = Helper.getCurrentHour()
        dxf_file_path = Helper.createAndGetDxfFolder() + "/" + str(hour) + "h" + "_" + str(self.getBrand()) + "_" + str(self.getColor()) + "_" + str(self.getClientName()) + "_" + str(self.getName()) + "_" + str(self.getCoupageBatch()) + ".dxf"
        self.dxf_drawing = dxf.drawing(dxf_file_path)

    def setClientName(self, client_name):
        self.client_name
    
    def getClientName(self):
        return self.client_name

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
    
    def getBrand(self):
        return self.brand

    def setBrand(self, brand):
        self.brand = brand

    def getColor(self):
        return self.color
    
    def setColor(self, color):
        self.color = color

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

    def getGridWidth(self):
        return self.grid_width
    
    def setGridWidth(self, width):
        self.grid_width = width

    def getQuantity(self):
        return self.quantity
    
    def setQuantity(self, quantity):
        self.quantity = quantity
        
    def getTopLeft(self):   
        return self.getPosition() + np.array([-self.getWidth()/2, self.getHeight()/2])
    
    def getTopRight(self):   
        return self.getPosition() + np.array([self.getWidth()/2, self.getHeight()/2])
    
    def getBottomRight(self):
        return self.getPosition() + np.array([self.getWidth()/2, -self.getHeight()/2])

    def getBottomLeft(self):
        return self.getPosition() + np.array([-self.getWidth()/2, -self.getHeight()/2])
    
    def getArea(self):
        return self.width * self.height

    def getCoupageBatch(self):
        return self.coupage_batch
    
    def setCoupageBatch(self, coupage_batch):
        self.coupage_batch = coupage_batch
        
    def rotate(self):
        width = self.getHeight()
        height = self.getWidth()
        x = self.getPosition()[1]
        y = self.getPosition()[0]

        self.setWidth(width)
        self.setHeight(height)
        self.setPosition([x, y])

    def intersection(self, other):
        if self.getBottomRight()[0] <= other.getTopLeft()[0] or self.getTopLeft()[0] >= other.getBottomRight()[0]:
            return False
        
        if self.getBottomRight()[1] >= other.getTopLeft()[1] or self.getTopLeft()[1] <= other.getBottomRight()[1]:
            return False

        return True

    # TODO
    # refactor drawing adding to dxf
    # make two separate functions: 1 to saveAsDxf and one getDxf
    def toDxf(self, for_prime_center=True, coupage=False):
        x = self.getPosition()[0] - self.getWidth()/2
        y = self.getPosition()[1] - self.getHeight()/2
        width = self.getWidth()
        height = self.getHeight()

        if coupage and (height > width) and height <= self.getGridWidth():
            # rotate when more optimal
            width = self.getHeight()
            height = self.getWidth()

        if for_prime_center == True:
            x = Helper.toMillimeters(x)
            y = Helper.toMillimeters(y)

            width = Helper.toMillimeters(width)
            height = Helper.toMillimeters(height)

            bgcolor = random.randint(1,255)
            
            self.dxf_drawing.add(dxf.rectangle((y,x), height, width,
                                bgcolor=bgcolor))
            text = dxf.text(str(self.getClientName()), (y, x + width), 100.0, rotation=0)
            
            text['layer'] = 'TEXT'
            text['color'] = '7'
            self.dxf_drawing.add(text)
        else:
            bgcolor = random.randint(1,255)
            
            self.dxf_drawing.add(dxf.rectangle((x, y), width, height,
                                bgcolor=bgcolor))

            text = dxf.text(str(self.getClientName()), (x, y), 100.0, rotation=0)

            text['layer'] = 'TEXT'
            text['color'] = '7'

            self.dxf_drawing.add(text)
        
        self.dxf_drawing.save()

    def getVertices(self):
        return self.getTopLeft(), self.getTopRight(), self.getBottomLeft(), self.getBottomRight()

    
    

    