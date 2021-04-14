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
import uuid

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

    def __init__(self, data_logger=DataLogger()):
        self.db_manager = DatabaseManager()
        self.setStandardSizesToFill([])
        self.setFillOrdersWithSmallerGridWidths(False)

        self.rectangles = []
        self.is_stacking = False

        # current rectangle to stack in current grid
        self.rectangle = Rectangle()
        self.grid = Grid()
        self.setDataLogger(data_logger)

        # stacking position of current rectangle
        self.stacking_position = []

        # stacking position of current rectangle rotated
        self.stacking_position_rotated = []

    def setDataLogger(self, data_logger):
        self.data_logger = data_logger
    
    def getDataLogger(self):
        return self.data_logger

    def setRectangle(self, rectangle):
        self.rectangle = rectangle

    def setExcelParser(self, path, file_name):
        self.excel_parser = ExcelParser(data_logger=self.data_logger, path=path, file_name=file_name)

    def stackingStopped(self):
        return not self.is_stacking

    def startStacking(self):
        self.is_stacking = True

    def stopStacking(self):
        self.is_stacking = False

    def setGrid(self, grid):
        print("Set grid to " + str(grid.getName()))
        self.grid = grid
    
    def getGrid(self):
        return self.grid

    def setStandardSizesToFill(self, sizes):
        self.standard_sizes_to_fill = sizes

    def getStandardSizesToFill(self):
        return self.standard_sizes_to_fill

    def setFillOrdersWithSmallerGridWidths(self, should_be_filled):
        self.fill_orders_with_smaller_grid_widths = should_be_filled

    def getFillSmallerGridWidths(self):
        return self.fill_smaller_grid_widths

    def getUnstackedRectangles(self):
        return [rectangle for rectangle in self.rectangles if not rectangle.isStacked()]

    def setCoupage(self, coupage):
        self.coupage = coupage
    
    def getCoupage(self):
        return self.coupage

    def start(self, automatic=True):     
        """ 
        Starts stacking the current unstacked rectangles from database in self.grid

        Parameters
        -----------
        automatic: Automatically create grids when not available and stack all unstacked rectangles in these grids (loop over all the grids instead of only self.grid)
        When automatic is false, the user should manually set a grid to be used for stacking.
        """

        self.start_time = time.time()
        self.getAndExportCoupages()
        self.is_stacking = True
        # self.loadOrdersAndAddToDatabase()

        self.getAllUnstackedRectanglesFromDatabaseAndSortOnArea()
        total_amount_of_unstacked_rectangles = len(self.getUnstackedRectangles())

        while self.anyUnstackedRectangles() and not self.stackingStopped():
            if automatic:
                self.createGridInDatabaseIfNotAvailable()
                self.grids = self.db_manager.getGridsNotCut(sort=True)
            else:
                self.grids = []
                self.grids.append(self.grid)

            for grid in self.grids:
                self.rectangles = []
                self.setGrid(grid)
                self.getUnstackedRectanglesFromDatabaseMatchingAllGridPropertiesSortedOnArea()
                self.stackUnstackedRectanglesInGrid()
                
                # some grids are empty and should not be exported
                if not grid.isEmpty() and len(self.getUnstackedRectangles()) == 0:
                    if self.fill_orders_with_smaller_grid_widths:
                        self.shrinkGridToHeighestVerticalStackedPoint()
                        self.stackOrdersWithSmallerGridWidths()
                    
                    if len(self.standard_sizes_to_fill) > 0 and self.grid.getBrand().lower() == "kokos":
                        self.shrinkGridToHeighestVerticalStackedPoint()
                        self.stackStandardRectangles()

                    self.enlargeGridToStandardSize()

                # break out of loop when operator presses stop button
                if self.stackingStopped():
                    break

            self.getAllUnstackedRectanglesFromDatabaseAndSortOnArea()

        self.optimizeOnMillimetersAndExportNonEmptyGrids()
        self.total_time = time.time() - self.start_time
        self.data_logger.setTotalExecutionTime(self.total_time)
        self.data_logger.setSuccessfullyStackedRectangles(total_amount_of_unstacked_rectangles)
        self.data_logger.storeData()
        
    def optimizeOnMillimetersAndExportNonEmptyGrids(self):
        self.grids = self.db_manager.getGridsNotCut(sort=True)
        for grid in self.grids:
            if not grid.isEmpty():
                self.setGrid(grid)
                self.convertRectanglesToMillimetersOptimizeAndExportGrid()

    def stackOrdersWithSmallerGridWidths(self):
        self.getUnstackedRectanglesOfAllSmallerGridWidthsThanOriginalSortedOnArea()
        self.stackUnstackedRectanglesInGrid()

    def shrinkGridToHeighestVerticalStackedPoint(self):
        # set height to heighest point because we only want to stack in the gaps
        # of the stack, not add more at the top
        self.grid.setHeight(self.grid.getHighestVerticalPoint())
        self.db_manager.updateGrid(self.grid)

    def enlargeGridToStandardSize(self):
        self.grid.setHeight(1500)
        self.db_manager.updateGrid(self.grid)
                    
    def getUncutAreasOfGrids(self):
        grids = self.db_manager.getGridsNotCut()
        result = []

        for grid in grids:
            if not grid.isEmpty():
                result.append(grid.getUncutArea())

        return result

    def getAndExportCoupages(self):
        coupages = self.db_manager.getUnstackedRectangles(for_cutting=True, coupage_batch="coupage")
        for coupage in coupages:
            self.setCoupage(coupage)
            self.rotateCoupageToLargestSideUpwards()
            self.exportAndUpdateCoupage()
    
    def rotateCoupageToLargestSideUpwards(self):
        _width = self.coupage.getWidth()
        _height = self.coupage.getHeight()

        if _width > _height:
            print("Coupage width is larger than height")
            width, height = Helper.swap(_width, _height)
            print("Width before swap = " + str(self.coupage.getWidth()))
            self.coupage.setWidth(width)
            self.coupage.setHeight(height)
            print("Width after swap = " + str(self.coupage.getWidth()))
            self.db_manager.updateRectangle(self.coupage)

    def exportAndUpdateCoupage(self):
        self.coupage.toDxf(for_prime_center=True)
        self.coupage.toZcc()
        self.coupage.setStacked()
        self.db_manager.updateRectangle(self.coupage)

    def loadOrdersAndAddToDatabase(self):
        try:
            self.rectangles = self.excel_parser.getUnstackedRectangles()
            self.db_manager.addRectangles(self.rectangles)
        except EmptyExcelError:
            print("Excel file is empty!")

    def computeRectangleOrderArea(self, rectangles):
        areas = [x.getArea() for x in rectangles]
        indices_descending_order = sorted(range(len(areas)), key=lambda k: areas[k])
        rectangles_descending_area_order = []
        for idx in indices_descending_order:
            rectangles_descending_area_order.append(rectangles[idx])

        return list(reversed(rectangles_descending_area_order))

    def stackStandardRectangles(self, sizes=Rectangle.getStandardSizesSortedOnMostSold()):
        print("Try stacking standard rectangles")
        
        for size in self.standard_sizes_to_fill:
            while True:
                
                if not self.stackingStopped():
                    rectangle = Rectangle(width=size[0], height=size[1], 
                        client_name="Voorraad_" + str(size[0]) + "x" + str(size[1]) + "_" + str(uuid.uuid4())[-4:], name="Voorraad_" + str(size[0]) + "x" + str(size[1]) + "_" + str(uuid.uuid4())[-4:], 
                        grid_width=self.grid.getWidth(), brand=self.grid.getBrand(),
                        color=self.grid.getColor())

                    self.db_manager.addRectangle(rectangle)
                    self.setRectangle(rectangle)

                    try:
                        print("Grid height = " + str(self.grid.getHeight()))
                        self.stackOriginalOrRotatedRectangleAndUpdateDatabase()
                    except RotatedAndOriginalRectangleDoNotFitError:
                        self.db_manager.removeRectangle(rectangle)
                        break

                else: break
    
    def getUnstackedRectanglesOfAllSmallerGridWidthsThanOriginalSortedOnArea(self):
        self.rectangles = []

        unstacked_rectangles = self.db_manager.getUnstackedRectangles(color=self.grid.getColor(), 
            brand=self.grid.getBrand(), for_cutting=True)

        for rectangle in unstacked_rectangles:
            if rectangle.getGridWidth() <= self.grid.getWidth():
                self.rectangles.append(rectangle)

        self.rectangles = self.computeRectangleOrderArea(self.rectangles)
        for rectangle in self.rectangles:
            rectangle.roundWidth()
            rectangle.roundHeight()
        
    def anyUnstackedRectangles(self):
        return len(self.getUnstackedRectangles()) > 0

    def createGridInDatabaseIfNotAvailable(self):
        for rectangle in self.rectangles:
            if not self.isGridAvailable(rectangle):
                print("Grid not available")
                print("Create unique grid with material " + str(rectangle.getMaterial()))
                print("Create unique grid with article name " + str(rectangle.getArticleName()))

                self.db_manager.createUniqueGrid(width=rectangle.getGridWidth(), article_name=rectangle.getArticleName(), material=rectangle.getMaterial(), color=rectangle.getColor(), brand=rectangle.getBrand())

    def getUnstackedRectanglesFromDatabaseMatchingAllGridPropertiesSortedOnArea(self):
        self.rectangles = self.db_manager.getUnstackedRectangles(color=self.grid.getColor(),
            brand=self.grid.getBrand(), grid_width=self.grid.getWidth(), for_cutting=True)

        self.rectangles = self.computeRectangleOrderArea(self.rectangles)
        for rectangle in self.rectangles:
            rectangle.roundWidth()
            rectangle.roundHeight()

    def getUnstackedRectanglesFromDatabaseMatchingGridColorBrandSortedOnArea(self):
        self.rectangles = self.db_manager.getUnstackedRectangles(color=self.grid.getColor(),
            brand=self.grid.getBrand(), for_cutting=True)

        self.rectangles = self.computeRectangleOrderArea(self.rectangles)
        for rectangle in self.rectangles:
            rectangle.roundWidth()
            rectangle.roundHeight()

    def getAllUnstackedRectanglesFromDatabaseAndSortOnArea(self):
        self.rectangles = self.db_manager.getUnstackedRectangles(for_cutting=True)
        self.rectangles = self.computeRectangleOrderArea(self.rectangles)
        for rectangle in self.rectangles:
            rectangle.roundWidth()
            rectangle.roundHeight()

    def isGridAvailable(self, rectangle):
        grid_width = rectangle.getGridWidth()
        color = rectangle.getColor()
        brand = rectangle.getBrand()

        return len(self.db_manager.getGridsNotCutByWidthBrandColor(width=grid_width, color=color, brand=brand)) > 0        

    def rectangleAndGridPropertiesMatch(self):
        return (self.grid.getBrand() == self.rectangle.getBrand()) and (self.grid.getColor() == self.rectangle.getColor())

    def createNewGridAndStackRectangle(self):

        new_grid = self.db_manager.createUniqueGrid(width=self.rectangle.getGridWidth(), article_name=self.rectangle.getArticleName(),
        material=self.rectangle.getMaterial(), brand=self.rectangle.getBrand(), color=self.rectangle.getColor())
        
        self.setGrid(new_grid)

        # for some reason new_grid starts out filled in an iteration
        self.db_manager.emptyGrid(new_grid)

        try:
            self.stackOriginalOrRotatedRectangleAndUpdateDatabase()
            
        except RotatedAndOriginalRectangleDoNotFitError:
            print("Something went wrong, rectangle does not fit in completely new grid")

    def convertRectanglesToMillimetersOptimizeAndExportGrid(self):
        print("Optimizing grid " + str(self.grid.getName()) + " and exporting to DXF...")
        self.getRectanglesExactWidthHeight()            
        self.grid.empty()
        
        # size to move rectangles in x and y direction
        step_size = 0.001

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

        self.grid.toDxf(for_prime_center=False)
        self.grid.toZcc()

    def getRectanglesExactWidthHeight(self):
        self.exact_rectangles = self.db_manager.getRectangles(self.grid, for_cutting=True, sort=True)
        # self.grid.setStackedRectangles(self.exact_rectangles)
        
    def moveRectangleVertically(self, step_size):
        self.grid.removeRectangle(self.optimized_rectangle)

        x = self.optimized_rectangle.getPosition()[0]
        y = self.optimized_rectangle.getPosition()[1]

        x_new = x - step_size
        print('x xnew')
        print(x_new)
        print(x)
        print(self.optimized_rectangle.getWidth(), self.optimized_rectangle.getHeight())
        print('CHECK')
        self.optimized_rectangle.setPosition([x_new, y])

        if not self.grid.isValidPosition(self.optimized_rectangle):
            print("Cannot optimize further in y direction")
            self.optimized_rectangle.setPosition([x, y])
            self.is_optimized_y = True
        else:
            pass
            # move y to y_new

    def moveRectangleHorizontally(self, step_size):
        self.grid.removeRectangle(self.optimized_rectangle)

        x = self.optimized_rectangle.getPosition()[0]
        y = self.optimized_rectangle.getPosition()[1]

        y_new = y - step_size

        self.optimized_rectangle.setPosition([x, y_new])

        if not self.grid.isValidPosition(self.optimized_rectangle):
            print("Cannot optimize further in x direction")
            self.optimized_rectangle.setPosition([x, y])
            self.is_optimized_x = True
        else:
            pass
            # move x to x_new

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

    def stackUnstackedRectanglesInGrid(self, smaller=False):
        for rectangle in self.rectangles:
            self.setRectangle(rectangle)

            if self.rectangleAndGridPropertiesMatch() and not rectangle.isStacked():
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
        # if w % 2 > 0:
        #     w += 1

        if w == self.rectangle.getHeight():
            t = height_exact
            height_exact = width_exact
            width_exact = t
            
        # set rectangle width height back to the exact ones
        self.rectangle.setWidth(width_exact)
        self.rectangle.setHeight(height_exact)

        for rectangle in self.rectangles:
            if rectangle.getName() == self.rectangle.getName():
                rectangle.setStacked()

        self.grid.addRectangle(self.rectangle)
        self.db_manager.updateRectangle(self.rectangle)
        self.db_manager.updateGrid(self.grid)

    def computeStackingPosition(self):        
        stacking_position = [self.grid.getWidth(), self.grid.getHeight()]
        print("CHECK")
        print(self.grid.getWidth())
        print(self.rectangle.getWidth())
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
        if self.rectangle.getWidth() % 2 > 0:
            width = self.rectangle.getWidth() + 1
        else:
            width = self.rectangle.getWidth()

        return reversed(range(int(width/2), int(self.grid.getWidth() - width/2) + 1))        


    def getVerticalLoopRange(self):
        if self.rectangle.getHeight() % 2 > 0:
            height = self.rectangle.getHeight() + 1
        else:
            height = self.rectangle.getHeight()
 
        return reversed(range(int(height/2), int(self.grid.getHeight() - height/2) + 1))        

    

