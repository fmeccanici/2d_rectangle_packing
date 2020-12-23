from rectangle_packing.helper import Helper

class DataLogger(object):
    def __init__(self):
        self.setStoragePath(Helper.getDesktopPath() + "/log/" + Helper.getDateTimeToday())
        self.error_data = []

    def setTotalExecutionTime(self, time):
        self.total_execution_time = time
    
    def getTotalExecutionTime(self):
        return self.total_execution_time

    def setTotalRectanglesToStack(self, amount):
        self.total_rectangles_to_stack = amount

    def getTotalRectanglesToStack(self):
        return self.total_rectangles_to_stack
    
    def setSuccessfullyStackedRectangles(self, amount):
        self.successfully_stacked_rectangles = amount

    def getSuccessfullyStackedRectangles(self):
        return self.successfully_stacked_rectangles
        
    def setStoragePath(self, path):
        self.path = path
    
    def getStoragePath(self):
        return self.path

    def addErrorData(self, data):
        self.error_data.append(data)
    
    def getErrorData(self):
        return self.error_data
    
    def clearErrorData(self):
        self.error_data = []
    
    def setErrorData(self, data):
        self.error_data = data

    def getAmountOfErrors(self):
        return len(self.error_data)
        
    def storeErrorData(self):
        file_name = 'log.txt'
        with open(self.getStoragePath() + file_name, 'w+'):
            f.write("Errors:\n")
            f.write(str(self.getErrorData()))

    
