# my own classes
from rectangle_packing.helper import Helper

# external dependencies
import numpy as np
from pathlib import Path
from dxfwrite import DXFEngine as dxf
import random

class Rectangle(object):
    def __init__(self, width=-1, height=-1, name="-1", material="Kokos", brand='kokos', color='naturel', grid_width=100, position=np.array([-1, -1]), grid_number=-1, is_stacked=False, quantity=1, client_name='', coupage_batch="batch"):
        self.position = np.asarray(position)
        self.setWidth(width)
        self.setHeight(height)
        self.setMaterial(material)
        self.setName(name)
        self.setBrand(brand)
        self.setColor(color)
        self.setGridWidth(grid_width)
        self.setQuantity(quantity)
        self.setClientName(client_name)
        self.setCoupageBatch(coupage_batch)
        self.setGridNumber(grid_number)
        
        self.is_stacked = is_stacked

        self.initEmptyDxfDrawing()

    @staticmethod
    def getMinimumSize():
        min_width = 100
        min_height = 50
        return min_width, min_height
    
    @staticmethod
    def getMaximumSize():
        max_width = 200
        max_height = 1500
        return max_width, max_height

    @staticmethod
    def getStandardSizesSortedOnMostSold():
        size_1 = (60, 80)
        size_2 = (100, 80)
        size_3 = (50, 80)
        size_4 = (40, 70)

        return [size_1, size_2, size_3, size_4]

    def initEmptyDxfDrawing(self):
        dxf_file_name = self.getDxfFileName()
        dxf_file_path = Helper.createAndGetDxfFolder() + "/" + self.getDxfFileName()
        self.dxf_drawing = dxf.drawing(dxf_file_path)

    def getDxfFileName(self):
        hour = Helper.getCurrentHour()
        return str(hour) + "h" + "_" + str(self.getMaterial()) + "_" + str(self.getColor()) + "_" + str(self.getClientName()) + "_" + str(self.getName()) + "_" + str(self.getCoupageBatch()) + ".dxf"

    def getMaterial(self):
        return self.material

    def setMaterial(self, material):
        self.material = material

    def setClientName(self, client_name):
        self.client_name = str(client_name)
    
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
        self.name = str(name)
    
    def getBrand(self):
        return self.brand

    def setBrand(self, brand):
        self.brand = str(brand)

    def getColor(self):
        return self.color
    
    def setColor(self, color):
        self.color = str(color)

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
        self.grid_width = int(width)

    def getQuantity(self):
        return self.quantity
    
    def setQuantity(self, quantity):
        self.quantity = int(quantity)
        
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
        self.coupage_batch = str(coupage_batch)
    
    def isCoupage(self):
        return self.coupage_batch == 'coupage'

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

    def toDxf(self, for_prime_center=True):
        rectangle_dxf = self.getRectangleDxf()
        label_dxf = self.getLabelDxf()

        self.dxf_drawing.add(rectangle_dxf)
        self.dxf_drawing.add(label_dxf)
        
        self.dxf_drawing.save()

    def getRectangleDxf(self, for_prime_center=True):
        x = self.getPosition()[0] - self.getWidth()/2
        y = self.getPosition()[1] - self.getHeight()/2
        width = self.getWidth()
        height = self.getHeight()

        if self.isCoupage() and (height > width) and height <= self.getGridWidth():
            # rotate when more optimal
            width = self.getHeight()
            height = self.getWidth()

        if for_prime_center == True:
            x = Helper.toMillimeters(x)
            y = Helper.toMillimeters(y)

            width = Helper.toMillimeters(width)
            height = Helper.toMillimeters(height)

            bgcolor = random.randint(1,255)
            
            return dxf.rectangle((y,x), height, width,
                                bgcolor=bgcolor)

        else:
            bgcolor = random.randint(1,255)
            
            return dxf.rectangle((x, y), width, height,
                                bgcolor=bgcolor)

    def getLabelDxf(self, for_prime_center=True):
        x = self.getPosition()[0] - self.getWidth()/2
        y = self.getPosition()[1] - self.getHeight()/2
        width = self.getWidth()
        height = self.getHeight()

        if self.isCoupage() and (height > width) and height <= self.getGridWidth():
            # rotate when more optimal
            width = self.getHeight()
            height = self.getWidth()

        if for_prime_center == True:
            x = Helper.toMillimeters(x)
            y = Helper.toMillimeters(y)
            width = Helper.toMillimeters(width)
            height = Helper.toMillimeters(width)

            text = dxf.text(str(self.getClientName()), (y, x + width), 100.0, rotation=0)
            
            text['layer'] = 'TEXT'
            text['color'] = '7'
        else:
            text = dxf.text(str(self.getClientName()), (x, y), 100.0, rotation=0)

            text['layer'] = 'TEXT'
            text['color'] = '7'
        
        return text

    def getVertices(self):
        return self.getTopLeft(), self.getTopRight(), self.getBottomLeft(), self.getBottomRight()