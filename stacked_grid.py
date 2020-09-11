from rectangle import Rectangle
import numpy as np
import copy
from bokeh.plotting import figure, output_file, show  
import random

class StackedGrid(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.stacked_rectangles = []

    def addRectangle(self, rectangle):
        self.stacked_rectangles.append(copy.deepcopy(rectangle))
    
    def isValidStackingPosition(self, rectangle):
        for i, stacked_rectangle in enumerate(self.stacked_rectangles):
            
            if rectangle.intersection(stacked_rectangle):
                return False

        return True

    def computeStackingPosition(self, rectangle):
        stacking_position = [self.width, self.height]

        for x in reversed(range(int(rectangle.width/2), int(self.width - rectangle.width/2))):
            for y in reversed(range(int(rectangle.height/2), int(self.height - rectangle.height/2))):
                position = np.array([x,y])
                rectangle.setPosition(position)

                # print(position)
                # self.isValidStackingPosition(rectangle)
                # print(np.linalg.norm(position) < np.linalg.norm(stacking_position))
                if self.isValidStackingPosition(rectangle) and np.linalg.norm(position) < np.linalg.norm(stacking_position):
                    stacking_position = position

        return stacking_position

    def computeStackingPositionAndAdd(self, rectangle):
        stacking_position = self.computeStackingPosition(rectangle)

        rectangle.setPosition(stacking_position)

        if stacking_position[0] != self.width and stacking_position[1] != self.height:
            self.addRectangle(rectangle)
        else:
            print("Could not fit rectangle in grid")

    def printAddedRectangles(self):
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

        for i in range(amount):
            width = random.randrange(2, 30, 2)
            height = random.randrange(2, 30, 2)

            r = Rectangle(np.array([0,0]), width, height)
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

if __name__ == "__main__":
    grid = StackedGrid(100, 100)
    
    rectangles = grid.generateRandomRectangles(20)
    rectangles = grid.computeRectangleOrderArea(rectangles)

    for rectangle in rectangles:
        grid.computeStackingPositionAndAdd(rectangle)

    grid.plot()
