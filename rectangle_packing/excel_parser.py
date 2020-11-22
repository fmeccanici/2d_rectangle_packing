
import pandas as pd
import numpy as np
from rectangle_packing.rectangle import Rectangle
import os

class Error(Exception):
    """Base class for other exceptions"""
    pass

class EmptyExcelError(Error):
    """Raised when excel is empty"""
    pass

class InvalidWidthError(Error):
    """Raised when width field has an invalid value"""
    pass

class InvalidHeightError(Error):
    """Raised when height field has an invalid value"""
    pass

class InvalidNameError(Error):
    """Raised when name field has an invalid value"""
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
        order_numbers = np.unique(list(self.df['Ordernummer']))
        
        for order_number in order_numbers:
            df_order_number = self.df.loc[self.df['Ordernummer'] == order_number]
            df_order_number_indices = df_order_number.index            

            # check for duplicates
            if len(df_order_number) > 1:
                
                # index used for appending duplicates
                j = 1

                # append duplicates with -
                for i in df_order_number_indices:
                    self.df.loc[self.df.index[i], 'Ordernummer'] = order_number + "-" + str(j)
                    j += 1

    def getOrdernumberRows(self, order_number):
        return self.df.loc[self.df['Ordernummer'] == order_number]

    def areThereDuplicates(self):
        duplicates = self.df.duplicated(keep=False, subset=['Ordernummer'])
        duplicates = self.df[duplicates].sort_values(by=['Ordernummer'])
        return len(duplicates) > 0

    def getWidth(self, row):
        try:
            width = row['Breedte'].split(',')[0] + '.' + row['Breedte'].split(',')[1]
        except IndexError:
            width = row['Breedte'].split(',')[0]
        except AttributeError:
            width = row['Breedte']

        width = float(width)
        if width == np.nan or width <= 0:
            raise InvalidWidthError

        return width
    
    def getHeight(self, row):
        try:
            height = row['Lengte'].split(',')[0] + '.' + row['Lengte'].split(',')[1]
        except IndexError:
            height = row['Lengte'].split(',')[0]
        except AttributeError:
            height = row['Lengte']

        height = float(height)
        if height == np.nan or height <= 0:
            raise InvalidHeightError

        return height

    def getName(self, row):
        name = str(row['Ordernummer'])
        if name == np.nan:
            raise InvalidNameError

        name = str(name)

        return name

    def getOrders(self):
        self.reloadExcel()
        orders = self.df[['Breedte', 'Lengte', 'Ordernummer', 'Merk', 'Omschrijving', 'Coupage/Batch', 'Kleur', 'Rolbreedte', 'Aantal', 'Klantnaam']]
        colors = []

        unstacked_rectangles = []
        for index, row in orders.iterrows():
            try:
                width = self.getWidth(row)
                height = self.getHeight(row)
                name = self.getName(row)

                brand = row["Merk"]
                if brand is not None:
                    brand = str(brand)

                coupage_batch = row["Coupage/Batch"].lower()
                client_name = row["Klantnaam"]

                color = str(row['Kleur'])
                brand = brand
                quantity = int(row['Aantal'])
                colors.append(color)

                grid_width = int(row['Rolbreedte'])
                
                if quantity > 1:
                    for i in range(1, quantity+1):
                        rectangle = Rectangle(width=width, height=height, name=name+'-'+str(i), brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name, coupage_batch=coupage_batch)
                        unstacked_rectangles.append(rectangle)
                else:            
                    rectangle = Rectangle(width=width, height=height, name=name, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name, coupage_batch=coupage_batch)
                    unstacked_rectangles.append(rectangle)

            except InvalidHeightError:
                print("Invalid height value")
                continue

            except InvalidWidthError:
                print("Invalid width value")
                continue
            
            except InvalidNameError:
                print("Invalid name value")
                continue

        if len(unstacked_rectangles) == 0:
            raise EmptyExcelError

        return unstacked_rectangles

if __name__ == "__main__":
    desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop') 
    path = desktop + "/paklijsten/"
    file_name = "paklijst_bug_2_aantal_ambiant.xlsx"

    parser = ExcelParser(path, file_name)
    parser.getOrders()
