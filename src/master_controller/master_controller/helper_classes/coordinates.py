import json

class Coordinates:
    def __init__(self, x: float = 0.0, y: float = 0.0, str_data: str = None):
        if str_data:
            data = json.loads(str_data)
            self.x, self.y = data['x'], data['y']
        else:
            self.x = x
            self.y = y
    
    def __repr__(self):
        return json.dumps({
            "x": self.x, 
            "y": self.y
        })
    
    def __eq__(self, other):
        if isinstance(other, Coordinates):
            return ((self.x == other.x) and (self.y == other.y))
        return False

    def __neg__(self):
        return Coordinates(-self.x, -self.y)
    
    def __add__(self, other: 'Coordinates'):
        return Coordinates(self.x + other.x, self.y + other.y)
    
    def CrossProduct(self, other: 'Coordinates'):
        return ((self.x * other.y) - (other.x * self.y))
    