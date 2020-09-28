
# my own classes
from rectangle import Rectangle
from database_manager import DatabaseManager

# external dependencies
import numpy as np
import copy
from bokeh.plotting import figure, output_file, show  
import random
import pickle
import os
import dxfwrite
from dxfwrite import DXFEngine as dxf
import time

class Error(Exception):
    """Base class for other exceptions"""
    pass

class InvalidGridPositionError(Error):
    """Raised when rectangle has invalid grid position"""
    pass

class StackedGrid(object):
    def __init__(self, width, height, name):
        self.width = width
        self.height = height
        self.name = name

        self.unstacked_rectangles = []
        self.stacked_rectangles = []

        self.grid_dxf = "grid" + str(name) + ".dxf"
        
        self.drawing = dxf.drawing(self.grid_dxf)

        self.min_rectangle_width = 100 #cm
        self.min_rectangle_height = 50 #cm
        self.max_rectangle_width = 200 #cm
        self.max_rectangle_height = 1500 #cm

        self.base_path = os.path.abspath(os.getcwd())
        self.db_manager = DatabaseManager()

    def setPicklePath(self, path):
        self.path = path

    def toDict(self):
        return {'name': self.name, 'width': self.width, 'height': self.height, 'stacked_rectangles': [rect.toDict() for rect in self.stacked_rectangles]}

    def saveAsPickle(self):
        stacked_grid_dict = self.toDict()
        with open(self.path + str(self.name), 'wb') as f:
            pickle.dump(stacked_grid_dict, f)
    
    def loadFromPickle(self, file_path):
        with open(file_path, 'rb') as f:
            stacked_grid = pickle.load(f)
            self.name = stacked_grid['name']
            self.stacked_rectangles = [Rectangle(rect['width'], rect['height'], rect['name'], rect['position']) for rect in stacked_grid['stacked_rectangles']]
    
    def loadAndAddRectanglesTodo(self):
        todo_path = self.base_path + '/rectangles/todo/'
        files = os.listdir(todo_path)
        
        for f in enumerate(files):
            rectangle = Rectangle(0, 0, str(f[1].split('.')[0]))
            rectangle.setPicklePath(todo_path)
            rectangle.loadFromPickle()
            self.unstacked_rectangles.append(rectangle)

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

    def isValidStackingPosition(self, rectangle):
        for i, stacked_rectangle in enumerate(self.stacked_rectangles):
            
            if rectangle.intersection(stacked_rectangle):
                return False

        return True

    def computeStackingPosition(self, rectangle):
        stacking_position = [self.width, self.height]
        
        # for x in reversed(range(int(rectangle.width/2), int(self.width - rectangle.width/2), int(self.min_rectangle_width/2 + rectangle.width/2))):
        #     for y in reversed(range(int(rectangle.height/2), int(self.height - rectangle.height/2), int(self.min_rectangle_height/2 + rectangle.height/2))):

        print("width = " + str(self.width))
        print("height = " + str(self.height))
        print(rectangle.width)
        print(rectangle.height)

        for x in reversed(range(int(rectangle.width/2), int(self.width - rectangle.width/2))):
            for y in reversed(range(int(rectangle.height/2), int(self.height - rectangle.height/2))):
                position = np.array([x,y])
                rectangle.setPosition(position)
                if self.isValidStackingPosition(rectangle) and np.linalg.norm(position) < np.linalg.norm(stacking_position):
                    stacking_position = position

        return stacking_position

    def computeStackingPositionAndUpdateDatabase(self, rectangle):
        try:

            stacking_position = self.computeStackingPosition(rectangle)
            rectangle.setPosition(stacking_position)
            
            if stacking_position[0] != self.width and stacking_position[1] != self.height:
                rectangle.setStacked()
                rectangle.setGridNumber(self.name)

                self.addRectangle(rectangle)
                self.db_manager.updateRectangle(rectangle)

                # grid_path = self.base_path + '/grids/'
                # self.setPicklePath(grid_path)
                # self.saveAsPickle()
                # rectangle.removePickle()
                # rectangle.setPicklePath(done_path)
                # rectangle.saveAsPickle()

            else:
                raise InvalidGridPositionError
            
        except InvalidGridPositionError:
            print("Could not fit rectangle in grid!")


    def printStackedRectangles(self):
        for r in self.stacked_rectangles:
            print(r.getPosition())

    def computeRectangleOrderArea(self, rectangles):
        
        areas = [x.getArea() for x in rectangles]
        indices_descending_order = sorted(range(len(areas)), key=lambda k: areas[k])
        rectangles_descending_area_order = []
        for idx in indices_descending_order:
            rectangles_descending_area_order.append(rectangles[idx])

        return list(reversed(rectangles_descending_area_order))
    
    def generateRandomRectangles(self, amount):
        rectangles = []
        random.seed(41)
        for i in range(amount):
            width = random.randrange(self.min_rectangle_width, self.max_rectangle_width, 2)
            height = random.randrange(self.min_rectangle_height, self.max_rectangle_height/2, 2)

            r = Rectangle(width, height, name=i)
            rectangles.append(r)
        return rectangles
    
    def generateAndSaveRandomRectangles(self, amount):
        rectangles = []
        random.seed(41)
        for i in range(amount):
            width = random.randrange(self.min_rectangle_width, 200, 2)
            height = random.randrange(self.min_rectangle_height, 200, 2)

            r = Rectangle(width, height, name=i)
            r.setPicklePath(self.base_path + '/rectangles/todo/')
            r.saveAsPickle()
            rectangles.append(r)
        return rectangles     

    def plot(self):
        # file to save the model  
        output_file("stacked_grid.html")  
            
        # instantiating the figure object  
        graph = figure(title = "Stacked grid")  
        
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
        show(graph) 

    def addToDatabase(self, rectangles):
        for rectangle in rectangles:
            self.db_manager.addRectangle(rectangle)

    def startStacking(self):
        t_start = time.time()

        # n = 20
        
        # self.unstacked_rectangles = self.generateRandomRectangles(n)
        
        # self.loadAndAddRectanglesTodo()
        
        # self.addToDatabase(self.unstacked_rectangles)
        self.unstacked_rectangles = self.db_manager.getUnstackedRectangles()
        if len(self.unstacked_rectangles) > 4:
            self.unstacked_rectangles = grid.computeRectangleOrderArea(self.unstacked_rectangles)

            # print([rect.toDict() for rect in self.unstacked_rectangles])

            for i, rectangle in enumerate(self.unstacked_rectangles):
                print("Rectangle " + str(rectangle.getName()))
                self.computeStackingPositionAndUpdateDatabase(rectangle)

            # self.plot()
            # self.toDxf()
        
            # t_stop = time.time() - t_start
            # print("Time: " + str(round(t_stop)) + " seconds")
        
if __name__ == "__main__":
    # 3 meters long
    # grid = StackedGrid(width=200, height=1500, name=0)

    # grid = StackedGrid(width=0, height=0, name=0)
    # grid.loadFromPickle('/home/fmeccanici/Documents/2d_rectangle_packing/grids/0')
    # grid.startStacking()

    grid = StackedGrid(width=200, height=1500, name=1)
    grid.startStacking()


