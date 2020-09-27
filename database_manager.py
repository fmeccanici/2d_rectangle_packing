import pymongo
from os.path import join
from bson.json_util import dumps

class DatabaseManager(object):
    def __init__(self, host='localhost', port=27017, database="stacked_rectangles_database"):
        self.client = pymongo.MongoClient(host, port)
        self.db = self.client[database]
        self.collection = self.db["rectangles"]

    def createDocument(self, rectangle):
        width = rectangle.getWidth()
        height = rectangle.getHeight()
        position = rectangle.getPosition()
        name = rectangle.getName()
        is_stacked = rectangle.isStacked()
        grid_number = rectangle.getGridNumber()

        return { "name": name, "width": width, "height": height, "position": position, "isStacked": is_stacked, "grid_number": grid_number }

    def addRectangle(self, rectangle):
        document = self.createDocument(rectangle)
        self.collection.insert(document)

    def makeBackup(self, path):
        col = getattr(self.db, self.collection)
        collection = col.find()
        jsonfile = "rectangles.json"
        jsonpath = join(path, jsonfile)

        with open(jsonpath, 'wb') as f:
            f.write(dumps(collection))

if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_list = db_manager.client.list_database_names()
    if "stacked_grids_database" in db_list:
        print("database exists")
    
    db_manager.makeBackup('/home/fmeccanici/Documents/2d_rectangle_packing/')
    