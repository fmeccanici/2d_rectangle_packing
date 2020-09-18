import pymongo

class DatabaseManager(object):
    def __init__(self):
        # self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.client = pymongo.MongoClient('localhost', 27017)

        self.db = self.client["stacked_grids_database"]

if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_list = db_manager.client.list_database_names()
    # if "stacked_grids_database" in db_list:
    #     print("database exists")