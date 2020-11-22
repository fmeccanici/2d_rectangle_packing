import datetime, os

# class with useful functions
class Helper(object):
    def __init__(self):
        pass
    
    @staticmethod
    def toMillimeters(variable):
        return variable * 10

    @staticmethod
    def swap(x, y):
        t = x 
        x = y
        y = t

        return x, y

    @staticmethod
    def createAndGetDxfFolder():
        today = datetime.date.today()

        datum = today.strftime("%Y%m%d")
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop') 

        dxf_path = desktop + "/grids/" + datum + "/"
        if not os.path.exists(dxf_path):
            os.makedirs(dxf_path)

        return dxf_path
    
    @staticmethod
    def getDateTimeToday():
        return datetime.date.today().strftime("%Y%m%d")

    @staticmethod
    def getCurrentHour():
        return datetime.datetime.now().hour

    @staticmethod
    def getDesktopPath():
        return os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop') 