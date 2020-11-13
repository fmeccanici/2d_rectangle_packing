
import pandas as pd
import numpy as np
from rectangle import Rectangle

class ExcelParser():
    def __init__(self, path, file_name):
        self.path = path
        self.file_name = file_name
        self.names = []

    def setFileName(self, file_name):
        self.file_name = file_name

    def reloadExcel(self, basic_excel=True):
        if not basic_excel: 
            self.df = pd.read_excel(self.path + self.file_name, sheet_name=None)        
            self.df = self.df['Paklijst']
            self.df = self.df.drop([0, 1, 2, 3])
            self.df.columns = ['Aantal', 'Merk', 'Omschrijving', 'Breedte', 'Lengte', 'Orderdatum', 'Coupage/Batch', 'Ordernummer', 'Klantnaam', 'Kleur', 'Rolbreedte']
        else:
            self.df = pd.read_excel(self.path + self.file_name, sheet_name='paklijst_zonder_opmaak')        

    def getOrders(self):
        self.reloadExcel()
        orders = self.df[['Breedte', 'Lengte', 'Ordernummer', 'Merk', 'Omschrijving', 'Coupage/Batch', 'Kleur', 'Rolbreedte', 'Aantal', 'Klantnaam']]

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
            except IndexError:
                height = row['Lengte'].split(',')[0]
            except AttributeError:
                height = row['Lengte']

            name = str(row['Ordernummer'])
            for i, stored_name in enumerate(self.names):
                if stored_name == name:
                    print("Got double order")
                    self.names[i] = name + "-1"
                    self.names.append(name + "-2")
            else:
                self.names.append(name)
                
            width = float(width)
            height = float(height)
            brand = row["Merk"]
            coupage_batch = row["Coupage/Batch"]
            client_name = row["Klantnaam"]

            if brand == "Kokos" and coupage_batch == "Batch":
                color = row['Kleur'].lower()
                brand = brand.lower()
                quantity = int(row['Aantal'])
                
                    
                grid_width = int(row['Rolbreedte'])
                if quantity > 1:
                    for i in range(1, quantity+1):
                        rectangle = Rectangle(width=width, height=height, name=name+'-'+str(i), brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name)
                        unstacked_rectangles.append(rectangle)
                else:            
                    rectangle = Rectangle(width=width, height=height, name=name, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name)
                    unstacked_rectangles.append(rectangle)

        return unstacked_rectangles