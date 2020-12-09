
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

class InvalidBrandError(Error):
    """Raised when brand field has an invalid value"""
    pass

class InvalidCoupageBatchError(Error):
    """Raised when coupage/batch field has an invalid value"""
    pass

class InvalidClientNameError(Error):
    """Raised when clientname field has an invalid value"""
    pass

class InvalidColorError(Error):
    """Raised when color field has an invalid value"""
    pass

class InvalidQuantityError(Error):
    """Raised when quantity field has an invalid value"""
    pass

class InvalidGridWidthError(Error):
    """Raised when gridwidth field has an invalid value"""
    pass

class InvalidMaterialError(Error):
    """Raised when material field has an invalid value"""
    pass

class ExcelParser():
    def __init__(self, path="./paklijsten/", file_name="paklijst.xlsx", sheet_name='paklijst_zonder_opmaak'):
        self.path = path
        self.file_name = file_name
        self.names = []
        self.setSheetName(sheet_name)
    
    def getSheetName(self):
        return self.sheet_name

    def setSheetName(self, sheet_name):
        self.sheet_name = sheet_name

    def setPath(self, path):
        self.path = path
    
    def setFileName(self, file_name):
        self.file_name = file_name

    def getUnstackedRectangles(self):
        self.reloadExcel()
        orders = self.getOrders()
        unstacked_rectangles = self.convertOrdersToRectangles(orders)
        
        return unstacked_rectangles
    
    def reloadExcel(self, basic_excel=True):
    
        # basic means only columns and rows, no other opmaak things as "PAKLIJST" large at the top
        if not basic_excel: 
            self.loadNonBasicExcel()
        else:
            self.loadBasicExcel()
        
        if self.areThereDuplicates():
            self.parseDuplicateOrderNumbers()

    def loadNonBasicExcel(self):
        self.df = pd.read_excel(self.path + self.file_name, sheet_name=None)        
        self.df = self.df['Paklijst']
        self.df = self.df.drop([0, 1, 2, 3])
        self.df.columns = ['Aantal', 'Merk', 'Omschrijving', 'Breedte', 'Lengte', 'Orderdatum', 'Coupage/Batch', 'Ordernummer', 'Klantnaam', 'Kleur', 'Rolbreedte']

    def loadBasicExcel(self):
        self.df = pd.read_excel(self.path + self.file_name, sheet_name=self.sheet_name)        
        self.df[['Ordernummer']] = self.df[['Ordernummer']].astype(str)

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

    def areThereDuplicates(self):
        duplicates = self.df.duplicated(keep=False, subset=['Ordernummer'])
        duplicates = self.df[duplicates].sort_values(by=['Ordernummer'])
        return len(duplicates) > 0
    
    def getOrders(self):
        return self.df[['Breedte', 'Lengte', 'Ordernummer', 'Merk', 'Omschrijving', 'Coupage/Batch', 'Kleur', 'Rolbreedte', 'Aantal', 'Klantnaam', 'Materiaal']]
    
    def convertOrdersToRectangles(self, orders):
        unstacked_rectangles = []
        for index, row in orders.iterrows():
            try:
                width = self.getWidth(row)
                height = self.getHeight(row)
                name = self.getName(row)
                brand = self.getBrand(row)
                coupage_batch = self.getCoupageBatch(row)
                client_name = self.getClientName(row)
                color = self.getColor(row)
                quantity = self.getQuantity(row)
                grid_width = self.getGridWidth(row)
                material = self.getMaterial(row)
                # print("Material set in excel parser: " + str(material))
                if quantity > 1:
                    for i in range(1, quantity+1):
                        rectangle = Rectangle(width=width, height=height, name=name+'-'+str(i), material=material, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name, coupage_batch=coupage_batch)
                        unstacked_rectangles.append(rectangle)
                else:   
                    # cut rectangle in two when width and height are larger then grid width        
                    if width > grid_width and height > grid_width:
                        if width > height:
                            rectangle_part1 = Rectangle(width=width/2.0, height=height, name=name+'part1', material=material, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name+"-part1", coupage_batch=coupage_batch)
                            rectangle_part2 = Rectangle(width=width/2.0, height=height, name=name+'part2', material=material, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name+"-part2", coupage_batch=coupage_batch)
                        elif height > width:
                            rectangle_part1 = Rectangle(width=width, height=height/2.0, name=name+'part1', material=material, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name+"-part1", coupage_batch=coupage_batch)
                            rectangle_part2 = Rectangle(width=width, height=height/2.0, name=name+'part2', material=material, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name+"-part2", coupage_batch=coupage_batch)

                        unstacked_rectangles.append(rectangle_part1)
                        unstacked_rectangles.append(rectangle_part2)
                    else:
                        rectangle = Rectangle(width=width, height=height, name=name, material=material, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name, coupage_batch=coupage_batch)
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
            
            except InvalidBrandError:
                print("Invalid brand value")
                continue
            
            except InvalidCoupageBatchError:
                print("Invalid coupage/batch value")
                continue
        
            except InvalidClientNameError:
                print("Invalid clientname value")
                continue

            except InvalidColorError:
                print("Invalid color value")
                continue
            
            except InvalidQuantityError:
                print("Invalid quantity value")
                continue
        
        if len(unstacked_rectangles) == 0:
            raise EmptyExcelError    

        return unstacked_rectangles

    def getWidth(self, row):
        try:
            width = row['Breedte'].split(',')[0] + '.' + row['Breedte'].split(',')[1]
        except IndexError:
            width = row['Breedte'].split(',')[0]
        except AttributeError:
            width = row['Breedte']

        width = float(width)
        if width == np.nan or width <= 0 or width is None:
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
        if height == np.nan or height <= 0 or height is None:
            raise InvalidHeightError

        return height

    def getName(self, row):
        name = str(row['Ordernummer'])
        if name == np.nan or name == "" or name is None:
            raise InvalidNameError

        name = str(name)

        return name
    
    def getBrand(self, row):
        brand = row["Merk"]
        if brand == np.nan or brand == "" or brand is None:
            raise InvalidBrandError

        brand = str(brand)

        return brand

    def getCoupageBatch(self, row):
        coupage_batch = row["Coupage/Batch"]
        if coupage_batch == np.nan or coupage_batch == "" or coupage_batch is None:
            raise InvalidCoupageBatchError

        # lower needed because somewhere else in the code it is checked for
        # coupage_batch == "batch"
        coupage_batch = str(coupage_batch).lower()

        return coupage_batch

    def getClientName(self, row):
        client_name = row["Klantnaam"]
        if client_name == np.nan or client_name == "" or client_name is None:
            raise InvalidClientNameError

        client_name = str(client_name)

        return client_name

    def getColor(self, row):
        color = row["Kleur"]
        if color == np.nan or color == "" or color is None:
            raise InvalidColorError

        color = str(color)

        return color

    def getQuantity(self, row):
        quantity = row["Aantal"]
        if quantity == np.nan or quantity == "" or quantity is None:
            raise InvalidQuantityError

        quantity = int(quantity)

        return quantity

    def getGridWidth(self, row):
        grid_width = row["Rolbreedte"]
        if grid_width == np.nan or grid_width == "" or grid_width is None:
            raise InvalidGridWidthError

        grid_width = int(grid_width)

        return grid_width

    def getMaterial(self, row):
        material = row["Materiaal"]
        if material == np.nan or material == "" or material is None:
            raise InvalidMaterialError

        return material