
from rectangle import Rectangle
from stacked_grid import StackedGrid
from database_manager import DatabaseManager

import random
import time
import numpy as np

class Error(Exception):
    """Base class for other exceptions"""
    pass

class InvalidGridPositionError(Error):
    """Raised when rectangle has invalid grid position"""
    pass

class GridFullError(Error):
    """Raised when grid is full"""
    pass

class Stacker(object):
    def __init__(self):
        self.db_manager = DatabaseManager()
        
        # grid = StackedGrid(width=200, height=1500, name=991)
        # self.db_manager.addGrid(grid)
        
        # self.grids = self.db_manager.getGridsNotFull()
        

        self.unstacked_rectangles = []
        
        self.min_rectangle_width = 100 #cm
        self.min_rectangle_height = 50 #cm
        self.max_rectangle_width = 200 #cm
        self.max_rectangle_height = 1500 #cm
        
        self.min_grid_buffer_size = 50

        self.stop_stacking = False

    def stackingStopped(self):
        return self.stop_stacking
    
    def stopStacking(self):
        self.stop_stacking = True

    def startStacking(self):
        self.stop_stacking = False

    def addToDatabase(self, rectangles):
        for rectangle in rectangles:
            self.db_manager.addRectangle(rectangle)

    def computeStackingPosition(self, rectangle, grid):
        stacking_position = [grid.getWidth(), grid.getHeight()]

        for x in reversed(range(int(rectangle.width/2), int(grid.getWidth() - rectangle.width/2))):
            for y in reversed(range(int(rectangle.height/2), int(grid.getHeight() - rectangle.height/2))):
                
                position = np.array([x,y])
                rectangle.setPosition(position)
                if grid.isValidPosition(rectangle) and np.linalg.norm(position) < np.linalg.norm(stacking_position):
                    stacking_position = position

        return stacking_position

    def createAndAddNewGrid(self):
        try:
            grid = StackedGrid(width=200, height=1500, name=self.grids[-1].getName() + 1, stacked_rectangles=[])
            self.grids.append(grid)

            self.db_manager.addGrid(grid)
            print("Created and added new grid to database")

        except IndexError:
            grid = StackedGrid(width=200, height=1500, name=1)
            self.grids.append(grid)
            self.db_manager.addGrid(grid)
            print("Created and added initial grid to database")

    def computeStackingPositionAndUpdateDatabase(self, rectangle, grid):
        stacking_position = self.computeStackingPosition(rectangle, grid)
        rectangle.setPosition(stacking_position)

        if stacking_position[0] != grid.getWidth() and stacking_position[1] != grid.getHeight():
            rectangle.setStacked()
            rectangle.setGridNumber(grid.getName())

            grid.addRectangle(rectangle)
            self.db_manager.updateRectangle(rectangle)
            self.db_manager.updateGrid(grid)
            
        else:
            raise InvalidGridPositionError

    def computeRectangleOrderArea(self, rectangles):
        
        areas = [x.getArea() for x in rectangles]
        indices_descending_order = sorted(range(len(areas)), key=lambda k: areas[k])
        rectangles_descending_area_order = []
        for idx in indices_descending_order:
            rectangles_descending_area_order.append(rectangles[idx])

        return list(reversed(rectangles_descending_area_order))

    def generateRandomRectangles(self, amount):
        rectangles = []
        # random.seed(41)
        for i in range(amount):
            width = random.randrange(self.min_rectangle_width, self.max_rectangle_width, 2)
            height = random.randrange(self.min_rectangle_height, self.max_rectangle_height/2, 2)

            r = Rectangle(width, height, name=int(time.time()))
            rectangles.append(r)
            time.sleep(1)

            print("Generated random rectangle " + str(r.getName()))

        return rectangles

    def start(self):        
        n = 5
        self.unstacked_rectangles = self.generateRandomRectangles(n)
        self.addToDatabase(self.unstacked_rectangles)
        self.unstacked_rectangles = self.db_manager.getUnstackedRectangles()

        # minimum amount of rectangles such that we can sort the rectangles based on area
        while len(self.unstacked_rectangles) > self.min_grid_buffer_size:
            
            self.unstacked_rectangles = self.db_manager.getUnstackedRectangles()

            # print([x.getName() for x in self.unstacked_rectangles])
            # print([x.getName() for x in self.grids])

            self.unstacked_rectangles = self.computeRectangleOrderArea(self.unstacked_rectangles)


            for i, rectangle in enumerate(self.unstacked_rectangles):
                print("Amount of unstacked rectangles = " + str(len(self.unstacked_rectangles)))
                print("Rectangle " + str(rectangle.getName()))

                for grid in self.grids:
                    print("Grid " + str(grid.getName()))
                    grid.plot()

                    try:
                        print("Original rectangle")
                        print(rectangle.getWidth(), rectangle.getHeight())
                        self.computeStackingPositionAndUpdateDatabase(rectangle, grid)
                        del self.unstacked_rectangles[i]
                        break

                    except InvalidGridPositionError:
                        print("Failed to stack original rectangle")
                        print("Try rotated")
                        try:
                            rectangle.rotate()
                            print("Rotated rectangle")
                            print(rectangle.getWidth(), rectangle.getHeight())

                            self.computeStackingPositionAndUpdateDatabase(rectangle, grid)
                            del self.unstacked_rectangles[i]
                            break

                        except InvalidGridPositionError:
                            print("Invalid grid position")
                            continue
                        
                if not rectangle.isStacked():
                    self.createAndAddNewGrid()
            
        for grid in self.grids:
            grid.plot()

if __name__ == "__main__":
    stacker = Stacker()
    # stacker.db_manager.convertGridsNotCutToDxf()
    
    while True:
        t_start = time.time()
        stacker.start()
        stacker.db_manager.makeBackup()
        t_stop = time.time() - t_start

        print("Time: " + str(round(t_stop)) + " seconds")
    

