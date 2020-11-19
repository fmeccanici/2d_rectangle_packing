
import pandas as pd
import numpy as np
from rectangle import Rectangle
import os

class Error(Exception):
    """Base class for other exceptions"""
    pass

class EmptyExcelError(Error):
    """Raised when excel is empty"""
    pass

class ExcelParser():
    def __init__(self, path="./paklijsten/", file_name="paklijst.xlsx"):
        self.path = path
        self.file_name = file_name
        self.names = []

    def setPath(self, path):
        self.path = path
    
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
            self.df[['Ordernummer']] = self.df[['Ordernummer']].astype(str)
            if self.areThereDuplicates():
                self.parseDuplicateOrderNumbers()

    def parseDuplicateOrderNumbers(self):
        duplicates = self.df.duplicated(keep=False, subset=['Ordernummer'])
        duplicates = self.df[duplicates].sort_values(by=['Ordernummer'])

        duplicates_ordernumbers = list(duplicates['Ordernummer'])

        i = 0
        while True:
            try:
                if (duplicates_ordernumbers[i] == duplicates_ordernumbers[i+1]) and not (duplicates_ordernumbers[i] == duplicates_ordernumbers[i+2]):
                    duplicates_ordernumbers[i] = duplicates_ordernumbers[i] + '-1'        
                    duplicates_ordernumbers[i+1] = duplicates_ordernumbers[i+1] + '-2'
                    
                    i = i + 2
                    if i >= len(duplicates_ordernumbers)-1: break

                elif (duplicates_ordernumbers[i] == duplicates_ordernumbers[i+1]) and (duplicates_ordernumbers[i+1] == duplicates_ordernumbers[i+2]):
                    duplicates_ordernumbers[i] = duplicates_ordernumbers[i] + '-1'        
                    duplicates_ordernumbers[i+1] = duplicates_ordernumbers[i+1] + '-2'
                    duplicates_ordernumbers[i+2] = duplicates_ordernumbers[i+2] + '-3'
                    i = i + 3
                    if i >= len(duplicates_ordernumbers)-1: break
                else:
                    i = i + 1
                    if i >= len(duplicates_ordernumbers)-1: break

            except IndexError:
                try:
                    duplicates_ordernumbers[i] = duplicates_ordernumbers[i] + '-1'        
                    duplicates_ordernumbers[i+1] = duplicates_ordernumbers[i+1] + '-2'
                    break
                except IndexError:
                    raise EmptyExcelError

        duplicates.drop(['Ordernummer'], axis=1)
        duplicates['Ordernummer'] = duplicates_ordernumbers

        self.df = self.df.drop_duplicates(keep=False, subset=["Ordernummer"])
        self.df = pd.concat([self.df, duplicates])
        print(list(self.df['Ordernummer']))

    def areThereDuplicates(self):
        duplicates = self.df.duplicated(keep=False, subset=['Ordernummer'])
        duplicates = self.df[duplicates].sort_values(by=['Ordernummer'])
        return len(duplicates) > 0

    def getOrders(self):
        self.reloadExcel()
        orders = self.df[['Breedte', 'Lengte', 'Ordernummer', 'Merk', 'Omschrijving', 'Coupage/Batch', 'Kleur', 'Rolbreedte', 'Aantal', 'Klantnaam']]
        colors = []

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

            if name is not np.nan:
                name = str((name))

            width = float(width)
            height = float(height)
            brand = row["Merk"]
            if brand is not None:
                brand = str(brand)

            coupage_batch = row["Coupage/Batch"]
            client_name = row["Klantnaam"]

            if coupage_batch == "Batch":
                color = str(row['Kleur'])
                brand = brand
                print("brand = " + (brand))
                print("color = " + (color))
                quantity = int(row['Aantal'])
                colors.append(color)

                grid_width = int(row['Rolbreedte'])
                if quantity > 1:
                    for i in range(1, quantity+1):
                        rectangle = Rectangle(width=width, height=height, name=name+'-'+str(i), brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name)
                        unstacked_rectangles.append(rectangle)
                else:            
                    rectangle = Rectangle(width=width, height=height, name=name, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name)
                    unstacked_rectangles.append(rectangle)
        
        if len(unstacked_rectangles) == 0:
            raise EmptyExcelError

        return unstacked_rectangles

if __name__ == "__main__":
    desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop') 
    path = desktop + "/paklijsten/"
    file_name = "paklijst2.xlsx"

    parser = ExcelParser(path, file_name)
    parser.getOrders()
