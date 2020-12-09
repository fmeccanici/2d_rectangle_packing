from rectangle_packing.rectangle import Rectangle
from rectangle_packing.grid import Grid
from rectangle_packing.database_manager import DatabaseManager
from rectangle_packing.excel_parser import *
from rectangle_packing.zcc_creator import ZccCreator
from rectangle_packing.helper import Helper

import random
import time
import numpy as np
import copy
import getpass

class Error(Exception):
    """Base class for other exceptions"""
    pass

class RectangleDoesNotFitError(Error):
    """Raised when rectangle does not fit in grid"""
    pass
    
class GridFullError(Error):
    """Raised when grid is full"""
    pass

class RotatedAndOriginalRectangleDoNotFitError(Error):
    """Raised when both original and rotated rectangle do not fit in grid"""
    pass

class Stacker(object):
    """
    Contains the algorithm for stacking rectangles in a grid in 2D. The rectangles are first sorted at centimeter accuracy. First the rectangles are sorted
    using in descending order based on the area, after which they are stacked to the most lower left position. After that the rectangles are shrunken to their exact
    millimeter size and moved left and downwards until they cannot be moved further. The result is a millimeter accuracy stacked grid.
    """

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

    def startStacking(self):
        self.is_stacking = True

    def stopStacking(self):
        self.is_stacking = False

    def setGrid(self, grid):
        self.grid = grid
    
    def getGrid(self):
        return self.grid

    def start(self, automatic=True):     
        """ 
        Starts stacking the current unstacked rectangles from database in self.grid

        Parameters
        -----------
        automatic: Automatically create grids when not available and stack all unstacked rectangles in these grids (loop over all the grids instead of only self.grid)
        When automatic is false, the user should manually set a grid to be used for stacking.
        """

        self.exportCoupages()
        self.is_stacking = True
        # self.loadOrdersAndAddToDatabase()

        self.getAllUnstackedRectanglesFromDatabaseAndSortOnArea()

        while self.anyUnstackedRectangles() and not self.stackingStopped():
            print('check1')
            if automatic:
                self.createGridInDatabaseIfNotAvailable()
                self.grids = self.db_manager.getGridsNotCut(sort=True)
            else:
                self.grids = []
                self.grids.append(self.grid)

            for grid in self.grids:
                self.unstacked_rectangles = []

                self.setGrid(grid)
                print("self.grid material = " + str(self.grid.getMaterial()))
                self.getUnstackedRectanglesFromDatabaseMatchingGridPropertiesSortedOnArea()
                self.stackUnstackedRectanglesInGrid()

                if not grid.isEmpty():
                    self.getUnstackedRectanglesOfAllSmallerGridWidthsThanOriginalSortedOnArea()
                    # set height to heighest point because we only want to stack in the gaps
                    # of the stack, not add more at the top
                    self.grid.setHeight(self.grid.getHighestVerticalPoint())
                    self.db_manager.updateGrid(self.grid)

                    self.stackUnstackedRectanglesInGrid()

                    self.stackStandardRectangles()
                    self.grid.setHeight(1500)
                    self.db_manager.updateGrid(self.grid)
                    
                    self.convertRectanglesToMillimetersOptimizeAndExportGrid()
                    print(self.grid.getUncutArea())  

                # break out of loop when operator presses stop button
                if self.stackingStopped():
                    break
                    
            self.getAllUnstackedRectanglesFromDatabaseAndSortOnArea()

    def getUncutAreasOfGrids(self):
        grids = self.db_manager.getGridsNotCut()
        result = []

        for grid in grids:
            if not grid.isEmpty():
                result.append(grid.getUncutArea())

        return result

    def exportCoupages(self):
        coupages = self.db_manager.getUnstackedRectangles(for_cutting=True, coupage_batch="coupage")
        for coupage in coupages:
            _width = coupage.getWidth()
            _height = coupage.getHeight()

            if _width > _height:
                print("Coupage width is larger than height")
                width, height = Helper.swap(_width, _height)
                print("Width before swap = " + str(coupage.getWidth()))
                coupage.setWidth(width)
                coupage.setHeight(height)
                print("Width after swap = " + str(coupage.getWidth()))
                self.db_manager.updateRectangle(coupage)

            # for some reason for_prime_center has to be false
            # to be rotated correctly for Zund prime center
            # side with largest length should point sidewards
            # in Prime center it will be rotated 90deg such that the 
            # largest side points upwards
            coupage.toDxf(for_prime_center=True)
            coupage.setStacked()
            self.zcc_creator = ZccCreator(coupage)
            self.zcc_creator.save()
            self.db_manager.updateRectangle(coupage)
            
    def loadOrdersAndAddToDatabase(self):
        try:
            self.unstacked_rectangles = self.excel_parser.getUnstackedRectangles()
            self.db_manager.addRectangles(self.unstacked_rectangles)
        except EmptyExcelError:
            print("Excel file is empty!")

    def computeRectangleOrderArea(self, rectangles):
        areas = [x.getArea() for x in rectangles]
        indices_descending_order = sorted(range(len(areas)), key=lambda k: areas[k])
        rectangles_descending_area_order = []
        for idx in indices_descending_order:
            rectangles_descending_area_order.append(rectangles[idx])

        return list(reversed(rectangles_descending_area_order))

    def stackStandardRectangles(self):
        if not self.grid.isEmpty():
            print("Try stacking standard rectangles")
            sizes = Rectangle.getStandardSizesSortedOnMostSold()

            i = 1
            for size in sizes:
                
                while True:
                    
                    if not self.stackingStopped():
                        rectangle = Rectangle(width=size[0], height=size[1], 
                        client_name="Voorraad " + str(i), name="00000" + str(i), 
                        grid_width=self.grid.getWidth(), brand=self.grid.getBrand(),
                        color=self.grid.getColor())

                        self.db_manager.addRectangle(rectangle)
                        self.setRectangle(rectangle)

                        try:
                            self.stackOriginalOrRotatedRectangleAndUpdateDatabase()
                        except RotatedAndOriginalRectangleDoNotFitError:
                            self.db_manager.removeRectangle(rectangle)
                            self.grid.deleteRectangle(rectangle)
                            break

                        i += 1

                    else: break

    def getUnstackedRectanglesOfAllSmallerGridWidthsThanOriginalSortedOnArea(self):
        self.unstacked_rectangles = []
        unstacked_rectangles = self.db_manager.getUnstackedRectangles(color=self.grid.getColor(), brand=self.grid.getBrand())

        for rectangle in unstacked_rectangles:
            if rectangle.getGridWidth() < self.grid.getWidth():
                self.unstacked_rectangles.append(rectangle)

        self.unstacked_rectangles = self.computeRectangleOrderArea(self.unstacked_rectangles)

    def anyUnstackedRectangles(self):
        return len(self.getUnstackedRectangles()) > 0

    def getUnstackedRectangles(self):
        return self.unstacked_rectangles

    def createGridInDatabaseIfNotAvailable(self):
        for rectangle in self.unstacked_rectangles:
            if not self.isGridAvailable(rectangle):
                print("Grid not available")
                print("Create unique grid with material " + str(rectangle.getMaterial()))
                print("Create unique grid with article name " + str(rectangle.getArticleName()))

                self.db_manager.createUniqueGrid(width=rectangle.getGridWidth(), article_name=rectangle.getArticleName(), material=rectangle.getMaterial(), color=rectangle.getColor(), brand=rectangle.getBrand())

    def getUnstackedRectanglesFromDatabaseMatchingGridPropertiesSortedOnArea(self):
        self.unstacked_rectangles = self.db_manager.getUnstackedRectangles(color=self.grid.getColor(), brand=self.grid.getBrand(), grid_width=self.grid.getWidth())
        # for rectangle in unstacked_rectangles:
        #     if rectangle.getGridWidth() <= self.grid.getWidth():
        #         self.unstacked_rectangles.append(rectangle)

        self.unstacked_rectangles = self.computeRectangleOrderArea(self.unstacked_rectangles)

    def getAllUnstackedRectanglesFromDatabaseAndSortOnArea(self):
        self.unstacked_rectangles = self.db_manager.getUnstackedRectangles()
        self.unstacked_rectangles = self.computeRectangleOrderArea(self.unstacked_rectangles)

    def isGridAvailable(self, rectangle):
        grid_width = rectangle.getGridWidth()
        color = rectangle.getColor()
        brand = rectangle.getBrand()

        return len(self.db_manager.getGridsNotCutByWidthBrandColor(width=grid_width, color=color, brand=brand)) > 0        

    def rectangleAndGridPropertiesMatch(self):
        return (self.grid.getBrand() == self.rectangle.getBrand()) and (self.grid.getColor() == self.rectangle.getColor()) and (self.grid.getWidth() == self.rectangle.getGridWidth())

    def createNewGridAndStackRectangle(self):

        new_grid = self.db_manager.createUniqueGrid(width=self.rectangle.getGridWidth(), article_name=self.rectangle.getArticleName(),
        material=self.rectangle.getMaterial(), brand=self.rectangle.getBrand(), color=self.rectangle.getColor())
        
        self.setGrid(new_grid)

        # for some reason new_grid starts out filled in an iteration
        self.db_manager.emptyGrid(new_grid)

        try:
            print("Create new grid and stack rectangle")
            print("Grid:")
            print("Width = "+ str(new_grid.getWidth()))
            print("Height = "+ str(new_grid.getHeight()))
            print("Rectangle:")
            print("Width = "+ str(self.rectangle.getGridWidth()))
            print("Height = "+ str(self.rectangle.getHeight()))

            self.stackOriginalOrRotatedRectangleAndUpdateDatabase()

        except RotatedAndOriginalRectangleDoNotFitError:
            print("Something went wrong, rectangle does not fit in completely new grid")

    def convertRectanglesToMillimetersOptimizeAndExportGrid(self):
        print("Optimizing grid and exporting to DXF...")
        self.getRectanglesExactWidthHeight()            

        # size to move rectangles in x and y direction
        step_size = 0.01

        for exact_rectangle in self.exact_rectangles:
            self.is_optimized_x = False
            self.is_optimized_y = False

            # copy needed because otherwise variables have the same address
            self.optimized_rectangle = copy.deepcopy(exact_rectangle)

            while not self.is_optimized_x:
                self.moveRectangleHorizontally(step_size)
                        
            while not self.is_optimized_y:
                self.moveRectangleVertically(step_size)

            self.db_manager.updateRectangle(self.optimized_rectangle)
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

    def createAndAddNewGrid(self, width=100, article_name='default', material='kokos', brand='kokos', color='naturel'):
        try:
            grid = Grid(width=width, height=1500, article_name=article_name, material=material, name=self.grids[-1].getName() + 1, brand=brand, color=color, stacked_rectangles=[])
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
            
            try:
                self.stackOriginalOrRotatedRectangleAndUpdateDatabase()

            except RotatedAndOriginalRectangleDoNotFitError:
                print("Both rotated and original do not fit in grid")
                self.createNewGridAndStackRectangle()
                continue

            # stop the loop if user presses stop button
            if self.stackingStopped():
                break
    
    def stackOriginalOrRotatedRectangleAndUpdateDatabase(self):
        self.chooseOriginalOrRotatedRectangle()
        self.updateUnstackedRectangleInDatabase()

    def chooseOriginalOrRotatedRectangle(self):
        try:
            self.computeRotatedRectangleStackingPosition()
        except RectangleDoesNotFitError:
            print("Rotated rectangle does not fit")
            pass

        try:
            self.computeOriginalRectangleStackingPosition()
        except RectangleDoesNotFitError:
            print("Original rectangle does not fit")
            pass
        
        if self.isRotatedRectangleMoreOptimal():
            self.updateStackingPositionToRotatedInDatabase()

        if self.stacking_position_rotated[0] == self.grid.getWidth() and self.stacking_position_rotated[1] == self.grid.getHeight():
            if self.stacking_position[0] == self.grid.getWidth() and self.stacking_position[1] == self.grid.getHeight():
                raise RotatedAndOriginalRectangleDoNotFitError

    def computeRotatedRectangleStackingPosition(self):
        print("Computing stacking position for rotated rectangle " + str(self.rectangle.getName()))
        
        self.rectangle.rotate()
        self.stacking_position_rotated = self.computeStackingPosition()
        self.rectangle.rotate()

        if self.stacking_position_rotated[0] == self.grid.getWidth() and self.stacking_position_rotated[1] == self.grid.getHeight():
            raise RectangleDoesNotFitError
        
    def computeOriginalRectangleStackingPosition(self):
        print("Computing stacking position for original rectangle " + str(self.rectangle.getName()))

        self.stacking_position = self.computeStackingPosition()

        if self.stacking_position[0] == self.grid.getWidth() and self.stacking_position[1] == self.grid.getHeight():
            raise RectangleDoesNotFitError

    def isRotatedRectangleMoreOptimal(self):
        return np.linalg.norm(self.stacking_position_rotated) < np.linalg.norm(self.stacking_position)

    def updateStackingPositionToRotatedInDatabase(self):
        self.rectangle.rotate()
        self.stacking_position = copy.deepcopy(self.stacking_position_rotated)

        # get exact width height to update database correctly
        # rotate this rectangle
        rectangle_exact = self.db_manager.getRectangle(self.rectangle.getName(), for_cutting=True)
        rectangle_exact.rotate()
        self.db_manager.updateRectangle(rectangle_exact)

    def updateUnstackedRectangleInDatabase(self):
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
        print("Rectangle width = " + str(self.rectangle.getWidth()))
        print("Rectangle height = " + str(self.rectangle.getHeight()))

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

    

