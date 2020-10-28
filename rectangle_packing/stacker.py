
from rectangle import Rectangle
from stacked_grid import StackedGrid
from database_manager import DatabaseManager
from excel_parser import ExcelParser

import random
import time
import numpy as np
import copy

class Error(Exception):
    """Base class for other exceptions"""
    pass

class InvalidGridPositionError(Error):
    """Raised when rectangle has invalid grid position"""
    pass

class GridFullError(Error):
    """Raised when grid is full"""
    pass

"""
Contains algorithm for stacking rectangles in a 2D grid. First the rectangles should be sorted
using computeRectangleOrderArea, after which they can be stacked using computeStackingPosition
"""
class Stacker(object):
    def __init__(self):
        self.db_manager = DatabaseManager()
        path = "/home/fmeccanici/Documents/2d_rectangle_packing/documents/"
        file_name = "paklijst.xlsx"

        self.excel_parser = ExcelParser(path, file_name)
        
        self.unstacked_rectangles = []
        
        self.min_rectangle_width = 100 #cm
        self.min_rectangle_height = 50 #cm
        self.max_rectangle_width = 200 #cm
        self.max_rectangle_height = 1500 #cm
        
        self.stop_stacking = False

    def stackingStopped(self):
        return self.stop_stacking
    
    def stopStacking(self):
        self.stop_stacking = True

    def startStacking(self):
        self.stop_stacking = False

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
        self.startStacking()
        self.loadOrders()

        self.unstacked_rectangles = self.db_manager.getUnstackedRectangles()
        self.unstacked_rectangles = self.computeRectangleOrderArea(self.unstacked_rectangles)

        while len(self.unstacked_rectangles) > 0:
            self.createGridInDatabaseIfNotAvailable()

            self.grids = self.db_manager.getGridsNotCut()

            for grid in self.grids:
                self.grid = grid
                self.unstacked_rectangles = self.db_manager.getUnstackedRectangles(color=grid.getColor())
                self.unstacked_rectangles = self.computeRectangleOrderArea(self.unstacked_rectangles)

                for i, rectangle in enumerate(self.unstacked_rectangles):
                    self.rectangle = rectangle

                    if not self.stackingStopped():
                        
                        if self.rectangleAndGridPropertiesMatch:
                            try:
                                self.computeStackingPositionAndUpdateDatabase(rectangle, grid)
                            
                            except InvalidGridPositionError:
                                try:
                                    print("Cannot stack rectangle")
                                    print("Try rotated rectangle")
                                    rectangle.rotate()
                                    self.computeStackingPositionAndUpdateDatabase(rectangle, grid)
                                    continue

                                except InvalidGridPositionError:
                                    print("Rotate rectangle back to original")
                                    rectangle.rotate()
                                    print("Cannot stack rectangle in this grid")
                                    print("Creating new grid and stack this rectangle")
                                    new_grid = self.db_manager.createUniqueGrid(width=rectangle.getGridWidth(), brand=rectangle.getBrand(),
                                            color=rectangle.getColor())
                                    
                                    # for some reason new_grid starts out filled in an iteration
                                    self.db_manager.emptyGrid(new_grid)
                                    self.computeStackingPositionAndUpdateDatabase(rectangle, new_grid)
                                    continue
                        else: 
                            print("Colors don't match")
                    else:
                        print("Stacking stopped")
                        break
                    
                self.optimizeAndExportGrid(grid)
            
            self.unstacked_rectangles = self.db_manager.getUnstackedRectangles()
            self.unstacked_rectangles = self.computeRectangleOrderArea(self.unstacked_rectangles)
    
    def loadOrders(self):
        self.excel_parser.reloadExcel()
        unstacked_rectangles = self.excel_parser.getOrders()
        self.addToDatabase(unstacked_rectangles)

    def addToDatabase(self, rectangles):
        for rectangle in rectangles:
            self.db_manager.addRectangle(rectangle)

    def computeRectangleOrderArea(self, rectangles):
        areas = [x.getArea() for x in rectangles]
        indices_descending_order = sorted(range(len(areas)), key=lambda k: areas[k])
        rectangles_descending_area_order = []
        for idx in indices_descending_order:
            rectangles_descending_area_order.append(rectangles[idx])

        return list(reversed(rectangles_descending_area_order))

    def createGridInDatabaseIfNotAvailable(self):
        for rectangle in self.unstacked_rectangles:
            if not self.isGridAvailable(rectangle):
                self.db_manager.createUniqueGrid(width=rectangle.getGridWidth(), color=rectangle.getColor())

    def isGridAvailable(self, rectangle):
        grid_width = rectangle.getGridWidth()
        color = rectangle.getColor()
        return len(self.db_manager.getGridsNotCutByWidthBrandColor(width=grid_width, color=color)) > 0        

    def rectangleAndGridPropertiesMatch(self):
        return (self.grid.getBrand() == self.rectangle.getBrand()) and (self.grid.getColor() == self.rectangle.getColor()) and (self.grid.getWidth() == self.rectangle.getGridWidth())

    def optimizeAndExportGrid(self, grid):
        print("Optimizing grid and exporting to DXF...")
        self.grid = grid
        self.getRectanglesExactWidthHeight(grid)            
        
        step_size = 0.01

        for exact_rectangle in self.exact_rectangles:
            self.is_optimized_x = False
            self.is_optimized_y = False
            self.optimized_rectangle = copy.deepcopy(exact_rectangle)
            
            while not self.is_optimized_x:
                self.moveRectangleVertically(step_size)
            
            while not self.is_optimized_y:
                self.moveRectangleHorizontally(step_size)
            
            grid.addRectangle(self.optimized_rectangle)

        grid.toDxf(remove_duplicates=True, for_prime_center=False)
    
    def getRectanglesExactWidthHeight(self, grid):
        self.exact_rectangles = self.db_manager.getRectangles(grid, for_cutting=True, sort=True)

    def moveRectangleVertically(self, step_size):
        self.grid.deleteRectangle(self.optimized_rectangle)

        x = self.optimized_rectangle.getPosition()[0]
        y = self.optimized_rectangle.getPosition()[1]

        x_new = x - step_size

        self.optimized_rectangle.setPosition([x_new, y])

        if not self.grid.isValidPosition(self.optimized_rectangle):
            print("Cannot optimize further in x direction")
            self.optimized_rectangle.setPosition([x, y])
            self.is_optimized_x = True
        else:
            print("Moved x to " + str(x_new))

    def moveRectangleHorizontally(self, step_size):
        self.grid.deleteRectangle(self.optimized_rectangle)

        x = self.optimized_rectangle.getPosition()[0]
        y = self.optimized_rectangle.getPosition()[1]

        y_new = y - step_size

        self.optimized_rectangle.setPosition([x, y_new])

        if not self.grid.isValidPosition(self.optimized_rectangle):
            print("Cannot optimize further in y direction")
            self.optimized_rectangle.setPosition([x, y])
            self.is_optimized_y = True
        else:
            print("Moved y to " + str(y_new))

    def createAndAddNewGrid(self, width=100, brand='kokos', color='naturel'):
        try:
            grid = StackedGrid(width=width, height=1500, name=self.grids[-1].getName() + 1, brand=brand, color=color, stacked_rectangles=[])
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

            # get exact rectangle width and height
            rectangle_exact = self.db_manager.getRectangle(rectangle.getName(), for_cutting=True)

            width_exact = rectangle_exact.getWidth()
            height_exact = rectangle_exact.getHeight()
            
            # check if rectangle was rotated
            w = int(np.ceil(width_exact))
            if w % 2 > 0:
                w += 1

            if w == rectangle.getHeight():
                print("RECTANGLE WAS ROTATED")
                t = height_exact
                height_exact = width_exact
                width_exact = t
                
            # set rectangle width height back to the exact ones
            rectangle.setWidth(width_exact)
            rectangle.setHeight(height_exact)
            

            grid.addRectangle(rectangle)
            self.db_manager.updateRectangle(rectangle)
            self.db_manager.updateGrid(grid)
            
        else:
            raise InvalidGridPositionError

    def computeStackingPosition(self, rectangle, grid):
        stacking_position = [grid.getWidth(), grid.getHeight()]

        for x in reversed(range(int(rectangle.width/2), int(grid.getWidth() - rectangle.width/2))):
            for y in reversed(range(int(rectangle.height/2), int(grid.getHeight() - rectangle.height/2))):
                
                position = np.array([x,y])
                rectangle.setPosition(position)
                if grid.isValidPosition(rectangle) and np.linalg.norm(position) < np.linalg.norm(stacking_position):
                    stacking_position = position
        
        return stacking_position

if __name__ == "__main__":
    stacker = Stacker()
    stacker.start()    

    

