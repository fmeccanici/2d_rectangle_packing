
import pandas as pd
import numpy as np
from rectangle_packing.rectangle import Rectangle
from rectangle_packing.data_logger import DataLogger

import os

class Error(Exception):
    """Base class for other exceptions"""
    pass

class EmptyExcelError(Error):
    """Raised when excel is empty"""
    def __init__(self, message="Excel is empty"):
        self.message = message

    def __str__(self):
        return f'{self.message}'


class InvalidWidthError(Error):
    """Raised when width field has an invalid value"""
    def __init__(self, message="Invalid width"):
        self.message = message

    def __str__(self):
        return f'{self.message}'


class InvalidHeightError(Error):
    """Raised when height field has an invalid value"""
    def __init__(self, message="Invalid height"):
        self.message = message

    def __str__(self):
        return f'{self.message}'

class InvalidNameError(Error):
    """Raised when name field has an invalid value"""
    def __init__(self, message="Invalid name"):
        self.message = message

    def __str__(self):
        return f'{self.message}'

class InvalidBrandError(Error):
    """Raised when brand field has an invalid value"""
    def __init__(self, message="Invalid brand"):
        self.message = message

    def __str__(self):
        return f'{self.message}'


class InvalidCoupageBatchError(Error):
    """Raised when coupage/batch field has an invalid value"""
    def __init__(self, message="Definition of coupage/batch invalid"):
        self.message = message

    def __str__(self):
        return f'{self.message}'

class InvalidClientNameError(Error):
    """Raised when clientname field has an invalid value"""
    def __init__(self, message="Invalid client name"):
        self.message = message

    def __str__(self):
        return f'{self.message}'


class InvalidColorError(Error):
    """Raised when color field has an invalid value"""
    def __init__(self, message="Invalid color"):
        self.message = message

    def __str__(self):
        return f'{self.message}'

class InvalidQuantityError(Error):
    """Raised when quantity field has an invalid value"""
    def __init__(self, message="Invalid quantity"):
        self.message = message

    def __str__(self):
        return f'{self.message}'


class InvalidGridWidthError(Error):
    """Raised when gridwidth field has an invalid value"""
    def __init__(self, message="Invalid grid width"):
        self.message = message

    def __str__(self):
        return f'{self.message}'

class InvalidMaterialError(Error):
    """Raised when material field has an invalid value"""
    def __init__(self, message="Invalid material"):
        self.message = message

    def __str__(self):
        return f'{self.message}'

class InvalidArticleNameError(Error):
    """Raised when article_name field has an invalid value"""
    def __init__(self, message="Invalid article name"):
        self.message = message

    def __str__(self):
        return f'{self.message}'

class ExcelParser():
    def __init__(self, data_logger=DataLogger(), path="./paklijsten/", file_name="paklijst.xlsx", sheet_name='paklijst_zonder_opmaak'):
        self.path = path
        self.file_name = file_name
        self.names = []
        self.data_logger = data_logger

        self.setSheetName(sheet_name)
    
    def setDataLogger(self, data_logger):
        self.data_logger = data_logger
    
    def getDataLogger(self):
        return self.data_logger

    def getSheetName(self):
        return self.sheet_name

    def setSheetName(self, sheet_name):
        self.sheet_name = sheet_name

    def setPath(self, path):
        self.path = path
        print("Set path to " + str(self.path))

    def setFileName(self, file_name):
        self.file_name = file_name
        print("Set file name to " + str(self.file_name))

    def getUnstackedRectangles(self):
        self.reloadExcel()
        orders = self.getOrders()
        unstacked_rectangles = self.convertOrdersToRectangles(orders)
        
        return unstacked_rectangles
    
    def reloadExcel(self, basic_excel=True):
        self.data_logger.clearErrorData()

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
        return self.df[['Breedte', 'Lengte', 'Ordernummer', 'Merk', 'Omschrijving', 'Coupage/Batch', 'Soort', 'Rolbreedte', 'Aantal', 'Klantnaam', 'Materiaal', 'Artikelnaam']]
    
    def convertOrdersToRectangles(self, orders):
        unstacked_rectangles = []
        self.data_logger.setTotalRectanglesToStack(len(orders))

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
                article_name = self.getArticleName(row)


                # print("Material set in excel parser: " + str(material))
                if quantity > 1:
                    for i in range(1, quantity+1):
                        rectangle = Rectangle(width=width, height=height, name=name+'-'+str(i), article_name=article_name, material=material, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name, coupage_batch=coupage_batch)
                        unstacked_rectangles.append(rectangle)
                else:   
                    # cut rectangle in two when width and height are larger then grid width        
                    if width > grid_width and height > grid_width:
                        if width > height:
                            rectangle_part1 = Rectangle(width=width/2.0, height=height, name=name+'part1', article_name=article_name, material=material, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name+"-part1", coupage_batch=coupage_batch)
                            rectangle_part2 = Rectangle(width=width/2.0, height=height, name=name+'part2', article_name=article_name, material=material, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name+"-part2", coupage_batch=coupage_batch)
                        elif height > width:
                            rectangle_part1 = Rectangle(width=width, height=height/2.0, name=name+'part1', article_name=article_name, material=material, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name+"-part1", coupage_batch=coupage_batch)
                            rectangle_part2 = Rectangle(width=width, height=height/2.0, name=name+'part2', article_name=article_name, material=material, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name+"-part2", coupage_batch=coupage_batch)

                        unstacked_rectangles.append(rectangle_part1)
                        unstacked_rectangles.append(rectangle_part2)
                    else:
                        rectangle = Rectangle(width=width, height=height, name=name, article_name=article_name, material=material, brand=brand, color=color, grid_width=grid_width, quantity=quantity, client_name=client_name, coupage_batch=coupage_batch)
                        unstacked_rectangles.append(rectangle)
            
            except Exception as e:
                name = self.getName(row)
                print("Something went wrong parsing order " + str(name) + ": " + str(e))
                self.data_logger.addErrorData("Order " + str(name) + ": " + str(e))
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

        if np.isnan(width) or width <= 0 or width is None or self.isNan(width):
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

        if np.isnan(height) or height <= 0 or height is None or self.isNan(height):
            raise InvalidHeightError

        return height

    def getName(self, row):
        name = int(row['Ordernummer'])

        if name == "" or name is None or self.isNan(name):
            raise InvalidNameError

        name = str(name)

        return name
    
    def getBrand(self, row):
        brand = row["Merk"]
        if brand == "" or brand is None or self.isNan(brand):
            raise InvalidBrandError

        brand = str(brand)

        return brand


    def getCoupageBatch(self, row):
        coupage_batch = row["Coupage/Batch"]

        if coupage_batch == "" or coupage_batch is None or self.isNan(coupage_batch):
            raise InvalidCoupageBatchError

        # lower needed because somewhere else in the code it is checked for
        # coupage_batch == "batch"
        coupage_batch = str(coupage_batch).lower()

        return coupage_batch

    def getClientName(self, row):
        client_name = row["Klantnaam"]
        if client_name == "" or client_name is None or self.isNan(client_name):
            raise InvalidClientNameError

        client_name = str(client_name)

        return client_name

    def getColor(self, row):
        color = row["Soort"]
        if color == "" or color is None or self.isNan(color):
            raise InvalidColorError

        color = str(color)

        return color

    def getQuantity(self, row):
        quantity = row["Aantal"]
        if np.isnan(quantity) or quantity == "" or quantity is None or self.isNan(quantity):
            raise InvalidQuantityError

        quantity = int(quantity)

        return quantity

    def getGridWidth(self, row):
        grid_width = row["Rolbreedte"]
        if np.isnan(grid_width) or grid_width == "" or grid_width is None or self.isNan(grid_width):
            raise InvalidGridWidthError

        grid_width = int(grid_width)

        return grid_width

    def getMaterial(self, row):
        material = row["Materiaal"]
        if material == "" or material is None or self.isNan(material):
            raise InvalidMaterialError
        
        material = str(row["Materiaal"])

        return material

    def getArticleName(self, row):
        article_name = row["Artikelnaam"]
        if article_name == "" or article_name is None or self.isNan(article_name):
            raise InvalidArticleNameError
        article_name = str(article_name)

        return article_name

    def isNan(self, string):
        return string != string