import numpy as np
import pickle
import os 

from pathlib import Path
from dxfwrite import DXFEngine as dxf
import datetime
import random

class Rectangle(object):
    def __init__(self, width, height, name, brand='kokos', color='naturel', grid_width=100, position=np.array([-1, -1]), grid_number=-1, is_stacked=False, quantity=1, client_name='', coupage_batch="batch"):
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

        today = datetime.date.today()
        hour = datetime.datetime.now().hour

        datum = today.strftime("%Y%m%d")
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop') 

        self.dxf_path = desktop + "/grids/" + datum + "/"
        self.dxf_file_path = self.dxf_path + "/" + str(hour) + "h" + "_" + self.getBrand() + "_" + self.getColor() + "_" + self.getClientName() + "_" + str(self.getName()) + "_" + self.getCoupageBatch() + ".dxf"

        if not os.path.exists(self.dxf_path):
            os.makedirs(self.dxf_path)

        self.dxf_drawing = dxf.drawing(self.dxf_file_path)

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

        self.setWidth(width)
        self.setHeight(height)
        
    def intersection(self, other):
        if self.getBottomRight()[0] <= other.getTopLeft()[0] or self.getTopLeft()[0] >= other.getBottomRight()[0]:
            return False
        
        if self.getBottomRight()[1] >= other.getTopLeft()[1] or self.getTopLeft()[1] <= other.getBottomRight()[1]:
            return False

        return True
    
    def toDict(self):
        return {'name': self.name, 'width':self.width, 'height': self.height, 'position': self.position}

    def toDxf(self):
        top_left = self.getTopLeft()
        top_right = self.getTopRight()
        bottom_left = self.getBottomLeft()
        bottom_right = self.getBottomRight()

        upper_horizontal_line = dxf.line((top_left[0], top_left[1]), (top_right[0], top_right[1]))
        lower_horizontal_line = dxf.line((bottom_left[0], bottom_left[1]), (bottom_right[0], bottom_right[1]))
        left_vertical_line = dxf.line((top_left[0], top_left[1]), (bottom_left[0], bottom_left[1]))
        right_vertical_line = dxf.line((top_right[0], top_right[1]), (bottom_right[0], bottom_right[1]))

        return upper_horizontal_line, lower_horizontal_line, left_vertical_line, right_vertical_line

    def toMillimeters(self, variable):
        return variable * 10

    # coupage
    def exportDxf(self, for_prime_center=True):
        width = self.getWidth()
        height = self.getHeight()

        # rotate when more optimal
        if (height > width) and height <= self.getGridWidth():
            width = self.getHeight()
            height = self.getWidth()

        x = width/2
        y = height/2

        if for_prime_center == True:
            x = self.toMillimeters(x)
            y = self.toMillimeters(y)

            width = self.toMillimeters(width)
            height = self.toMillimeters(height)

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
        
    def getFlooredWidthHeight(self):
        return np.floor(self.width), np.floor(self.height)
    
    

    