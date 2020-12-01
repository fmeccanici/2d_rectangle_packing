import math

class Vector2d(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def getX(self):
        return self.x
    
    def getY(self):
        return self.y
    
    @classmethod
    def fromNumpyArray(cls, array):
        return Vector2d(array[0], array[1])

    def __subtract__(self, other):
        return Vector2d((self.getX() - other.getX()),  (self.getY() - other.getY()))
    
    def __add__(self, other):
        return Vector2d((self.getX() + other.getX()),  (self.getY() + other.getY()))

    def __mul__(self, other):
        return Vector2d((self.getX() * other.getX()),  (self.getY() * other.getY()))

    def norm(self, other):
        return math.sqrt(self.getX()**2 + self.getY()**2)