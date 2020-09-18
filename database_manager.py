import pymongo

class DatabaseManager(object):
    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["stacked_rectangles_database"]

        mycol = self.db["rectangles"]
        mydict = { "name": "1", "width": 0, "height": 0, "position": 0, "isStacked": False, "grid": 0 }
        x = mycol.insert_one(mydict)

    def createDocument(self, rectangle):
        width = rectangle.getWidth()
        height = rectangle.getHeight()
        position = rectangle.getPosition()
        name = rectangle.getName()

        return { "name": "1", "width": 0, "height": 0, "position": 0, "isStacked": False, "grid": 0 }
    def addRectangle(self, rectangle):

if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_list = db_manager.client.list_database_names()
    if "stacked_grids_database" in db_list:
        print("database exists")