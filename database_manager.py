from rectangle import Rectangle

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

    def createDocument(self, rectangle):
        width = rectangle.getWidth()
        height = rectangle.getHeight()
        position = rectangle.getPosition()
        name = rectangle.getName()
        is_stacked = rectangle.isStacked()
        grid_number = rectangle.getGridNumber()

        return { "name": name, "width": width, "height": height, "x position": int(position[0]), "y position": int(position[1]), "isStacked": is_stacked, "grid_number": grid_number }

    def addRectangle(self, rectangle):
        document = self.createDocument(rectangle)
        self.rectangles_collection.insert(document)

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
        query = {"name" : rectangle.getName()}
        new_values = { "$set": { "grid_number" : rectangle.getGridNumber(), "x position" : int(rectangle.getPosition()[0]), "y position": int(rectangle.getPosition()[1]), "isStacked": rectangle.isStacked() } }
        self.rectangles_collection.update_one(query, new_values)

if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_list = db_manager.client.list_database_names()
    if "stacked_grids_database" in db_list:
        print("database exists")
    
    # r = Rectangle([0,0], 1, 1, '1')
    # db_manager.addRectangle(r)
    db_manager.makeBackup()
    # db_manager.loadBackup("27-09-2020-11:00:20")
