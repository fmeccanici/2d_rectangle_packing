# import own classes
from rectangle import Rectangle
from stacked_grid import StackedGrid

# external dependencies
import pymongo
from os.path import join
from bson.json_util import dumps
import time
import os

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

        self.backup_path = '/home/fmeccanici/Documents/2d_rectangle_packing/databases/'

    def createGridDocument(self, grid):
        width = grid.getWidth()
        height = grid.getHeight()
        num_rectangles = grid.getNumStackedRectangles()
        name = grid.getName()
        is_full = grid.isFull()
        is_cut = grid.isCut()

        return { "name": name, "width": width, "height": height, "num rectangles" : num_rectangles, "isFull" : is_full, "isCut": is_cut}
    
    def getGrids(self):
        grids = []

        cursor = self.grids_collection.find({})
        for document in cursor:
            print("Loaded grid " + str(document["name"]) + " from database")
            grid = StackedGrid(document['width'], document['height'], document['name'])
            rectangles = self.getRectangles(grid)
            grid.setStackedRectangles(rectangles)
            grid.isFull()
            grids.append(grid)

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

    def getRectangles(self, grid):
        rectangles_dict = self.rectangles_collection.find({
            "grid_number" : {"$eq" : grid.getName()}
        })
        
        rectangles = []
        for rectangle in rectangles_dict:
            rectangles.append(Rectangle(rectangle['width'], rectangle['height'], rectangle['name'], position=[rectangle['x position'], rectangle['y position']], grid_number=rectangle['grid_number'], is_stacked=rectangle['isStacked']))

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
    
    def updateRectangle(self, rectangle):
        print("Updating rectangle in database")
        query = {"name" : rectangle.getName()}
        print(rectangle.getWidth())
        print(rectangle.getHeight())

        new_values = { "$set": { "grid_number" : rectangle.getGridNumber(), "x position" : int(rectangle.getPosition()[0]), "y position": int(rectangle.getPosition()[1]), "isStacked": rectangle.isStacked(), 'width': rectangle.getWidth(), 'height': rectangle.getHeight() } }
        self.rectangles_collection.update_one(query, new_values)
    
if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_list = db_manager.client.list_database_names()
    if "stacked_grids_database" in db_list:
        print("database exists")
    
    # r = Rectangle([0,0], 1, 1, '1')
    # db_manager.addRectangle(r)
    # db_manager.makeBackup()
    db_manager.getGrids()
    # db_manager.loadBackup("27-09-2020-11:00:20")
