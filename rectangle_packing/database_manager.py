# import own classes
from rectangle import Rectangle
from stacked_grid import StackedGrid

# external dependencies
import pymongo
from os.path import join
from bson.json_util import dumps
import time
import os
import getpass
import numpy as np

class DatabaseManager(object):
    def __init__(self, host='localhost', port=27017, database="stacked_rectangles_database", username="NA", password="NA"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db_name = database

        self.client = pymongo.MongoClient(host, port)
        self.db = self.client[database]
        self.rectangles_collection = self.db["rectangles"]
        self.grids_collection = self.db["grids"]

        username = getpass.getuser()

        self.backup_path = '/home/' + username + '/Documents/2d_rectangle_packing/rectangle_packing/database_backups/'

    def listUsedGridNames(self):
        names = []
        cursor = self.grids_collection.find({})
        
        for document in cursor:
            name = document['name']
            names.append(name)
        
        return names

    def createUniqueGrid(self):
        width = 200
        height = 1500

        try:
            used_names = self.listUsedGridNames()
            sorted_names = sorted(used_names)
            unique_name = int(sorted_names[-1] + 1)
            grid = StackedGrid(width, height, unique_name)
            self.addGrid(grid)

        except IndexError:
            print("No grids available yet")
            print("Creating first grid")

            grid = StackedGrid(width, height, 1)
            self.addGrid(grid)
            
        return grid

    def createGridDocument(self, grid):
        width = grid.getWidth()
        height = grid.getHeight()
        num_rectangles = grid.getNumStackedRectangles()
        name = grid.getName()
        is_full = grid.isFull()
        is_cut = grid.isCut()

        return { "name": name, "width": width, "height": height, "numRectangles" : num_rectangles, "isFull" : is_full, "isCut": is_cut}
    
    def convertGridsNotCutToDxf(self):
        grids_not_cut = self.getGridsNotCut()
        for grid in grids_not_cut:
            grid.toDxf()

    def getGridsNotCut(self):
        grids = []

        cursor = self.grids_collection.find({})
        for document in cursor:
            grid = StackedGrid(width=document['width'], height=document['height'], name=document['name'], is_cut=document['isCut'])
            rectangles = self.getRectangles(grid)
            grid.setStackedRectangles(rectangles)
            
            if not grid.isCut():
                print("Loaded grid " + str(document["name"]) + " from database")

                grids.append(grid)

        return grids

    def getGridsCut(self):
        grids = []

        cursor = self.grids_collection.find({})
        for document in cursor:
            grid = StackedGrid(width=document['width'], height=document['height'], name=document['name'], is_cut=document['isCut'])
            rectangles = self.getRectangles(grid)
            grid.setStackedRectangles(rectangles)
            
            if grid.isCut():
                print("Loaded grid " + str(document["name"]) + " from database")

                grids.append(grid)

        return grids

    def getAllGrids(self):
        grids = []
        cursor = self.grids_collection.find({})

        for document in cursor:
                print("Loaded grid " + str(document["name"]) + " from database")
                grid = StackedGrid(document['width'], document['height'], document['name'])
                rectangles = self.getRectangles(grid)
                grid.setStackedRectangles(rectangles)
                grids.append(grid)

    def getGrid(self, grid_number):
        query = {"name" : grid_number}

        cursor = self.grids_collection.find(query)
        for document in cursor:
            grid = StackedGrid(document['width'], document['height'], document['name'])
            rectangles = self.getRectangles(grid)
            grid.setStackedRectangles(rectangles)
        
        return grid

    def getGridsNotFull(self):
        try:
            grids = []

            cursor = self.grids_collection.find({})

            for document in cursor:
                    print("Loaded grid " + str(document["name"]) + " from database")
                    grid = StackedGrid(document['width'], document['height'], document['name'])
                    rectangles = self.getRectangles(grid)
                    grid.setStackedRectangles(rectangles)
                    
                    grid.checkAndSetFull()
                    if not grid.isFull():
                        grids.append(grid)
        except:
            pass

        return grids

    def createRectangleDocument(self, rectangle):
        width = rectangle.getWidth()
        height = rectangle.getHeight()
        position = rectangle.getPosition()
        name = rectangle.getName()
        is_stacked = rectangle.isStacked()
        grid_number = rectangle.getGridNumber()

        return { "name": name, "width": width, "height": height, "x position": int(position[0]), "y position": int(position[1]), "isStacked": is_stacked, "grid_number": grid_number }

    def addGrid(self, grid):
        document = self.createGridDocument(grid)
        self.grids_collection.insert(document)

    def addRectangle(self, rectangle):
        document = self.createRectangleDocument(rectangle)
        self.rectangles_collection.insert(document)

    def getRectangle(self, rectangle_number):
        query = {"name" : rectangle_number}

        cursor = self.rectangles_collection.find(query)
        for document in cursor:
            rectangle = Rectangle(document['width'], document['height'], document['name'], position=[document['x position'], document['y position']], grid_number=document['grid_number'], is_stacked=document['isStacked'])
        
        return rectangle

    def getRectangles(self, grid):
        print("Loading rectangles within grid " + str(grid.getName()) + " from database")

        rectangles_dict = self.rectangles_collection.find({
            "grid_number" : {"$eq" : grid.getName()}
        })
        
        rectangles = []
        for rectangle in rectangles_dict:
            rectangles.append(Rectangle(rectangle['width'], rectangle['height'], rectangle['name'], position=[rectangle['x position'], rectangle['y position']], grid_number=rectangle['grid_number'], is_stacked=rectangle['isStacked']))
            print("Rectangle " + str(rectangle['name']) + " loaded from database")
        return rectangles
    
    def renderOutputLocations(self):
        return self.backup_path + time.strftime("%d-%m-%Y-%H:%M:%S")

    def makeBackup(self):
        command = "mongodump"
        if self.host != 'NA':
            command += " --host " + self.host
        if self.port != 'NA':
            command += " --port " + str(self.port)
        if self.username != 'NA':
            command += " --username " + self.username
        if self.password != 'NA':
            command += " --password " + self.password
        
        command += " --out " + self.renderOutputLocations()

        os.mkdir(self.renderOutputLocations())
        os.system(command)

        print("mongo backup progress started")

    def loadBackup(self, datetime):
        command = "mongorestore -d " + self.db_name + " " + self.backup_path + datetime + "/" + self.db_name 
        print(command)
        os.system(command)

        print("loading backup from " + str(datetime))

    def getUnstackedRectangles(self):
        rectangles_dict = self.rectangles_collection.find({
            "isStacked" : {"$eq" : False}
        })

        rectangles = []
        for rectangle in rectangles_dict:
            rectangles.append(Rectangle(rectangle['width'], rectangle['height'], rectangle['name']))

        return rectangles
    
    def updateGrid(self, grid):
        print("Updating grid " + str(grid.getName()) + " in database")
        print("isCut = " + str(grid.isCut()))
        print("numRectangles = " + str(grid.getNumStackedRectangles()))

        query = {"name" : grid.getName()}

        new_values = { "$set": { "numRectangles" : grid.getNumStackedRectangles() + 1 , "isCut": grid.isCut()} }
        self.grids_collection.update_one(query, new_values)
    
    def updateRectangle(self, rectangle):
        print("Updating rectangle in database")
        query = {"name" : rectangle.getName()}
        print(rectangle.getWidth())
        print(rectangle.getHeight())

        new_values = { "$set": { "grid_number" : rectangle.getGridNumber(), "x position" : int(rectangle.getPosition()[0]), "y position": int(rectangle.getPosition()[1]), "isStacked": rectangle.isStacked(), 'width': rectangle.getWidth(), 'height': rectangle.getHeight() } }
        self.rectangles_collection.update_one(query, new_values)
    
    def emptyGrid(self, grid):
        rectangles = self.getRectangles(grid)
        
        for rectangle in rectangles:
            rectangle.setUnstacked()
            rectangle.setGridNumber(-1)
            rectangle.setPosition(np.array([-1, -1]))
            self.updateRectangle(rectangle)

        grid.setStackedRectangles([])
        grid.setUncut()
        self.updateGrid(grid)

if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_list = db_manager.client.list_database_names()
    if "stacked_grids_database" in db_list:
        print("database exists")
    
    # r = Rectangle([0,0], 1, 1, '1')
    # db_manager.addRectangle(r)
    # db_manager.makeBackup()
    db_manager.getGridsNotFull()
    # db_manager.loadBackup("27-09-2020-11:00:20")
