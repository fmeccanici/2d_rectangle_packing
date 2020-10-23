
from rectangle import Rectangle
from stacked_grid import StackedGrid
from database_manager import DatabaseManager

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

    # def optimizeAndExportGrid(self, grid):
    #     exact_rectangles = self.db_manager.getRectangles(grid, for_cutting=True)
    #     rectangles_for_stacking = self.db_manager.getRectangles(grid, for_cutting=False)
    #     optimized_grid = StackedGrid(200, 1500, grid.getName())


    #     for exact_rectangle in exact_rectangles:
    #         for rectangle_for_stacking in rectangles_for_stacking:
    #             if rectangle_for_stacking.getName() == exact_rectangle.getName():
    #                 dx = rectangle_for_stacking.getWidth()/2 - exact_rectangle.getWidth()/2
    #                 dy = rectangle_for_stacking.getHeight()/2 - exact_rectangle.getHeight()/2
    #                 x_new = exact_rectangle.getPosition()[0] - dx
    #                 y_new = exact_rectangle.getPosition()[1] - dy
    #                 new_rectangle = Rectangle(exact_rectangle.getWidth(), exact_rectangle.getHeight(), exact_rectangle.getName(), grid_number=exact_rectangle.getGridNumber(), is_stacked=exact_rectangle.isStacked())
    #                 new_rectangle.setPosition([x_new, y_new])
    #                 optimized_grid.addRectangle(new_rectangle)
        
    #     optimized_grid.toDxf()

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

        # print(list(reversed(range(int(rectangle.width/2), int(grid.getWidth() - rectangle.width/2)))))
        # print((reversed(range(int(rectangle.height/2), int(grid.getHeight() - rectangle.height/2)))))

        for x in reversed(range(int(rectangle.width/2), int(grid.getWidth() - rectangle.width/2))):
            for y in reversed(range(int(rectangle.height/2), int(grid.getHeight() - rectangle.height/2))):
                
                position = np.array([x,y])
                rectangle.setPosition(position)
                if grid.isValidPosition(rectangle) and np.linalg.norm(position) < np.linalg.norm(stacking_position):
                    stacking_position = position
        
        # print(stacking_position)
        # print(rectangle.getWidth()/2)
        # print(rectangle.getHeight()/2)
        
        return stacking_position
        
    def optimizeAndExportGrid(self, grid):
            print("Optimizing grid and exporting to DXF...")
            exact_rectangles = self.db_manager.getRectanglesSortedMostUpperLeft(grid, for_cutting=True)

            
            for exact_rectangle in exact_rectangles:
                is_optimized_x = False
                is_optimized_y = False
                print("Rectangle " + str(exact_rectangle.getName()))
                optimized_rectangle = copy.deepcopy(exact_rectangle)

                while is_optimized_x == False:
                    grid.deleteRectangle(optimized_rectangle)

                    x = optimized_rectangle.getPosition()[0]
                    y = optimized_rectangle.getPosition()[1]

                    x_new = x - 0.0001

                    print("x_new = " + str(x_new))
                    # print('check')
                    # print(x_new)
                    # print(x_new - optimized_rectangle.getWidth()/2)
                    # print('check')

                    optimized_rectangle.setPosition([x_new, y])
                    if not grid.isValidPosition(optimized_rectangle):
                        print("Cannot optimize further in x direction")
                        optimized_rectangle.setPosition([x, y])
                        is_optimized_x = True
                    else:
                        print("Moved x to " + str(x_new))



                while is_optimized_y == False:                    
                    grid.deleteRectangle(optimized_rectangle)

                    x = optimized_rectangle.getPosition()[0]
                    y = optimized_rectangle.getPosition()[1]

                    y_new = y - 0.0001

                    optimized_rectangle.setPosition([x, y_new])
                    if not grid.isValidPosition(optimized_rectangle):
                        print("Cannot optimize further in y direction")
                        optimized_rectangle.setPosition([x, y])
                        is_optimized_y = True
                    else:
                        print("Moved y to " + str(y_new))

                grid.addRectangle(optimized_rectangle)

            grid.toDxf()

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
    

