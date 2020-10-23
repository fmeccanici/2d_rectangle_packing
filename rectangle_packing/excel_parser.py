
import pandas as pd
from rectangle import Rectangle

class ExcelParser():
    def __init__(self, path, file_name):
        self.path = path
        self.file_name = file_name
        self.df = pd.read_excel(path + file_name, sheet_name=None)

    def getOrders(self):
        self.df = self.df['Paklijst']
        self.df = self.df.drop([0, 1, 2, 3])
        self.df.columns = ['Aantal', 'Merk', 'Omschrijving', 'Breedte', 'Lengte', 'Orderdatum', 'Coupage/Batch', 'Ordernummer', 'Klantnaam']

        orders = self.df[['Breedte', 'Lengte', 'Ordernummer', 'Merk', 'Omschrijving', 'Coupage/Batch']]

        unstacked_rectangles = []
        for index, row in orders.iterrows():

            try:
                width = row['Breedte'].split(',')[0] + '.' + row['Breedte'].split(',')[1]
            except IndexError:
                width = row['Breedte'].split(',')[0]
            except AttributeError:
                width = row['Breedte']

            try:
                height = row['Lengte'].split(',')[0] + '.' + row['Lengte'].split(',')[1]
                print(height)
            except IndexError:
                height = row['Lengte'].split(',')[0]
            except AttributeError:
                height = row['Lengte']

            name = row['Ordernummer']

            width = float(width)
            height = float(height)
            brand = row["Merk"]
            coupage_batch = row["Coupage/Batch"]
            
            if brand == "Kokos" and coupage_batch == "Batch":
                rectangle = Rectangle(width, height, name)
                unstacked_rectangles.append(rectangle)
        
        return unstacked_rectangles