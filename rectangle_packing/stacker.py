from rectangle_packing.rectangle import Rectangle
from rectangle_packing.grid import Grid
from rectangle_packing.database_manager import DatabaseManager
from rectangle_packing.excel_parser import *

import random
import time
import numpy as np
import copy
import getpass

class Error(Exception):
    """Base class for other exceptions"""
    pass

class InvalidGridPositionError(Error):
    """Raised when rectangle has invalid grid position"""
    pass

class RectangleDoesNotFitError(Error):
    """Raised when rectangle does not fit in grid"""
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

        self.unstacked_rectangles = []
        self.is_stacking = False

        # current rectangle to stack in current grid
        self.rectangle = Rectangle()
        self.grid = Grid()

        # stacking position of current rectangle
        self.stacking_position = []

        # stacking position of current rectangle rotated
        self.stacking_position_rotated = []
     
    def setRectangle(self, rectangle):
        self.rectangle = rectangle

    def setExcelParser(self, path, file_name):
        self.excel_parser = ExcelParser(path, file_name)
    
    def stackingStopped(self):
        return not self.is_stacking
    
    def stopStacking(self):
        self.is_stacking = False

    def startStacking(self):
        self.is_stacking = True

    def setGrid(self, grid):
        self.grid = grid
    
    def getGrid(self, grid):
        return self.grid

    def exportCoupages(self):
        coupages = self.db_manager.getUnstackedRectangles(for_cutting=True, coupage_batch="coupage")
        for coupage in coupages:
            coupage.toDxf(for_prime_center=True, coupage=True)
            coupage.setStacked()
            self.db_manager.updateRectangle(coupage)

    def start(self, automatic=True):        
        self.exportCoupages()
        self.startStacking()
        # self.loadOrdersAndAddToDatabase()

        self.getAllUnstackedRectanglesFromDatabaseAndSortOnArea()

        while self.anyUnstackedRectangles() and not self.stackingStopped():
            if automatic:
                self.createGridInDatabaseIfNotAvailable()
                self.grids = self.db_manager.getGridsNotCut()
            else:
                self.grids = []
                self.grids.append(self.grid)

            for grid in self.grids:
                self.setGrid(grid)
                self.getUnstackedRectanglesFromDatabaseMatchingGridPropertiesOnArea()

                self.stackUnstackedRectanglesInGrid()
                self.optimizeAndExportGrid()

                if self.stackingStopped():
                    break

            self.getAllUnstackedRectanglesFromDatabaseAndSortOnArea()

    def loadOrdersAndAddToDatabase(self):
        try:
            self.unstacked_rectangles = self.excel_parser.getUnstackedRectangles()
            self.addToDatabase(self.unstacked_rectangles)
        except EmptyExcelError:
            print("Excel file is empty!")

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

    def anyUnstackedRectangles(self):
        return len(self.getUnstackedRectangles()) > 0

    def getUnstackedRectangles(self):
        return self.unstacked_rectangles

    def createGridInDatabaseIfNotAvailable(self):
        for rectangle in self.unstacked_rectangles:
            if not self.isGridAvailable(rectangle):
                self.db_manager.createUniqueGrid(width=rectangle.getGridWidth(), color=rectangle.getColor(), brand=rectangle.getBrand())

    def getUnstackedRectanglesFromDatabaseMatchingGridPropertiesOnArea(self):
        self.unstacked_rectangles = self.db_manager.getUnstackedRectangles(color=self.grid.getColor())
        self.unstacked_rectangles = self.computeRectangleOrderArea(self.unstacked_rectangles)

    def getAllUnstackedRectanglesFromDatabaseAndSortOnArea(self):
        self.unstacked_rectangles = self.db_manager.getUnstackedRectangles()
        self.unstacked_rectangles = self.computeRectangleOrderArea(self.unstacked_rectangles)

    def stackOriginalRectangle(self):
        self.computeStackingPositionAndUpdateDatabase()

    def isGridAvailable(self, rectangle):
        grid_width = rectangle.getGridWidth()
        color = rectangle.getColor()
        brand = rectangle.getBrand()

        return len(self.db_manager.getGridsNotCutByWidthBrandColor(width=grid_width, color=color, brand=brand)) > 0        

    def rectangleAndGridPropertiesMatch(self):
        return (self.grid.getBrand() == self.rectangle.getBrand()) and (self.grid.getColor() == self.rectangle.getColor()) and (self.grid.getWidth() == self.rectangle.getGridWidth())

    def stackRotatedRectangle(self):
        print("Cannot stack rectangle")
        print("Try rotated rectangle")
        self.rectangle.rotate()
        self.computeStackingPositionAndUpdateDatabase()

    def createNewGridAndStackRectangle(self):

        new_grid = self.db_manager.createUniqueGrid(width=self.rectangle.getGridWidth(), brand=self.rectangle.getBrand(),
                    color=self.rectangle.getColor())
        
        self.setGrid(new_grid)

        # for some reason new_grid starts out filled in an iteration
        self.db_manager.emptyGrid(new_grid)

        try:
            self.computeStackingPositionAndUpdateDatabase()
        
        except RectangleDoesNotFitError:
            self.rectangle.rotate()
            self.computeStackingPositionAndUpdateDatabase()
    
    def optimizeAndExportGrid(self):
        print("Optimizing grid and exporting to DXF...")
        self.getRectanglesExactWidthHeight()            
        
        step_size = 0.01

        for exact_rectangle in self.exact_rectangles:
            self.is_optimized_x = False
            self.is_optimized_y = False
            self.optimized_rectangle = copy.deepcopy(exact_rectangle)

            while not self.is_optimized_x:
                self.moveRectangleHorizontally(step_size)
                        
            while not self.is_optimized_y:
                self.moveRectangleVertically(step_size)

            self.grid.addRectangle(self.optimized_rectangle)

        self.grid.toDxf(remove_duplicates=False, for_prime_center=True)
    
    def getRectanglesExactWidthHeight(self):
        self.exact_rectangles = self.db_manager.getRectangles(self.grid, for_cutting=True, sort=True)

    def moveRectangleVertically(self, step_size):
        self.grid.deleteRectangle(self.optimized_rectangle)

        x = self.optimized_rectangle.getPosition()[0]
        y = self.optimized_rectangle.getPosition()[1]

        x_new = x - step_size

        self.optimized_rectangle.setPosition([x_new, y])

        if not self.grid.isValidPosition(self.optimized_rectangle):
            print("Cannot optimize further in x direction")
            self.optimized_rectangle.setPosition([x, y])
            self.is_optimized_y = True
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
            self.is_optimized_x = True
        else:
            print("Moved y to " + str(y_new))

    def createAndAddNewGrid(self, width=100, brand='kokos', color='naturel'):
        try:
            grid = Grid(width=width, height=1500, name=self.grids[-1].getName() + 1, brand=brand, color=color, stacked_rectangles=[])
            self.grids.append(grid)

            self.db_manager.addGrid(grid)
            print("Created and added new grid to database")

        except IndexError:
            grid = Grid(width=200, height=1500, name=1)
            self.grids.append(grid)
            self.db_manager.addGrid(grid)
            print("Created and added initial grid to database")

    def stackUnstackedRectanglesInGrid(self):
        for rectangle in self.unstacked_rectangles:
            self.setRectangle(rectangle)
            
            if self.rectangleAndGridPropertiesMatch():
                try:
                    self.stackOriginalRectangle()
                    
                except RectangleDoesNotFitError:
                    try:        
                        self.stackRotatedRectangle()
                        continue

                    except RectangleDoesNotFitError:
                        self.createNewGridAndStackRectangle()
                        continue
            else: 
                print("Grid properties don't match with rectangle")

            # stop the loop if user presses stop button
            if self.stackingStopped():
                break

    def computeStackingPositionAndUpdateDatabase(self):
        self.stacking_position = self.computeStackingPosition()
        self.rectangle.rotate()
        self.stacking_position_rotated = self.computeStackingPosition()
    
        if np.linalg.norm(self.stacking_position_rotated) < np.linalg.norm(self.stacking_position):
            self.stacking_position = self.stacking_position_rotated

            # get exact width height to update database correctly
            # rotate this rectangle
            rectangle_exact = self.db_manager.getRectangle(self.rectangle.getName(), for_cutting=True)
            rectangle_exact.rotate()
            self.db_manager.updateRectangle(rectangle_exact)

        else:
            # rotate rectangle back to original
            self.rectangle.rotate()
        
        if self.stacking_position[0] == self.grid.getWidth() and self.stacking_position[1] == self.grid.getHeight():
            raise RectangleDoesNotFitError

        self.stackRectangle()

    def stackRectangle(self):
        self.rectangle.setPosition(self.stacking_position)

        self.rectangle.setStacked()
        self.rectangle.setGridNumber(self.grid.getName())

        # get exact rectangle width and height
        rectangle_exact = self.db_manager.getRectangle(self.rectangle.getName(), for_cutting=True)

        width_exact = rectangle_exact.getWidth()
        height_exact = rectangle_exact.getHeight()
        
        # check if rectangle was rotated in start function
        w = int(np.ceil(width_exact))
        if w % 2 > 0:
            w += 1

        if w == self.rectangle.getHeight():
            t = height_exact
            height_exact = width_exact
            width_exact = t
            
        # set rectangle width height back to the exact ones
        self.rectangle.setWidth(width_exact)
        self.rectangle.setHeight(height_exact)

        self.grid.addRectangle(self.rectangle)
        self.db_manager.updateRectangle(self.rectangle)
        self.db_manager.updateGrid(self.grid)

    def computeStackingPosition(self):
        stacking_position = [self.grid.getWidth(), self.grid.getHeight()]

        if self.grid.getWidth() > self.rectangle.getWidth():
            for x in self.getHorizontalLoopRange():
                for y in self.getVerticalLoopRange():
                    position = np.array([x,y])
                    self.rectangle.setPosition(position)

                    if self.grid.isValidPosition(self.rectangle) and np.linalg.norm(position) < np.linalg.norm(stacking_position):
                        stacking_position = position
        
        elif self.grid.getWidth() == self.rectangle.getWidth():
            x = self.rectangle.getWidth() / 2
            
            for y in self.getVerticalLoopRange():
                position = np.array([x,y])
                self.rectangle.setPosition(position)
                if self.grid.isValidPosition(self.rectangle) and np.linalg.norm(position) < np.linalg.norm(stacking_position):
                    stacking_position = position
        
        return stacking_position

    def getHorizontalLoopRange(self):
        return reversed(range(int(self.rectangle.width/2), int(self.grid.getWidth() - self.rectangle.width/2) + 1))        

    def getVerticalLoopRange(self):
        return reversed(range(int(self.rectangle.height/2), int(self.grid.getHeight() - self.rectangle.height/2) + 1))        


if __name__ == "__main__":
    stacker = Stacker()
    stacker.start()    

    

