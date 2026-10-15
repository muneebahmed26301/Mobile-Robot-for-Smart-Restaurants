import json
from master_controller.helper_classes.coordinates import Coordinates

class GraphEdge:
    def __init__(self, source_node_id: int = None, target_node_id: int = None, direction: Coordinates = None, weight: float = 1.0, str_data: str = None):
        if str_data:
            data = json.loads(str_data)
            self.source_node_id = data["source_node_id"]
            self.target_node_id = data["target_node_id"]
            self.direction = Coordinates(str_data=data["direction"])
            self.weight = data["weight"]
        else:
            self.source_node_id = source_node_id
            self.target_node_id = target_node_id
            self.direction = direction
            self.weight = weight
    
    def __repr__(self):
        return json.dumps({
            "source_node_id":self.source_node_id, 
            "target_node_id":self.target_node_id, 
            "direction":repr(self.direction), 
            "weight":self.weight
        })
